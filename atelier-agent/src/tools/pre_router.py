"""
Pre-routing: decide which perspective model to measure against, from what the student said.

**This replaces `gemma_router.py`, which did not work and could not.** That module constructed
a `genai.Client`, discarded it, and returned a hardcoded branch on `student_level_hint` — a
string the caller had already supplied. It reported a `confidence` of 0.94 for a decision no
model made, and the `canny_thresholds` it "recommended" were consumed by nothing:
`geometry.py` hardcoded `cv2.Canny(blurred, 50, 150)`. It was documented across the README,
the architecture diagram and the evidence log as a shipped Vertex AI feature.

**Why it is no longer called `gemma_router`.** Gemma is not a publisher model on Vertex AI —
`gemma-3-27b-it`, `-12b-it`, `-4b-it` and the Gemma 4 line all return `404 NOT_FOUND` there, as
does every `*-flash-lite` variant. It *is* hosted on the Gemini API, which is where this module
reaches it, with a key from Secret Manager. The old module named itself after a model it had
never called through an endpoint that could not serve it.

**Why the routing step is worth keeping at all.** The old one recommended `k`, which the caller
already knew: `k` came from `student.level`, a stored profile field. A router that returns a
value you passed in is not a router. This one reads the student's own description of what they
were practising — the free text from the ASK verb — and picks the perspective model from that.
A beginner who drew a two-point corridor gets measured as a two-point drawing, because they
said so, rather than as one-point because of a field in their profile.

**Two models, because they are good at different things.**

- `route_from_intent` runs on **Gemma 4** through the Gemini API. Words only. Measured on this
  project's key: a structured routing answer in ~1.6 seconds, four times out of four.
- `classify_drawing` runs on **Gemini 3.5 Flash** on Vertex AI, and looks at the photograph.
  This is the gate the original design asked for and the deleted module never had: *is this even
  a perspective exercise?* A picture of a cat, or a page too blurred to read, is refused here —
  before the geometry engine and before a critique call spends tokens describing nothing.

Gemma does not take the picture. Its vision path was measured and rejected: it spends the entire
output budget reasoning and returns empty text, and at larger budgets it does not return at all.
A pre-router that takes minutes has defeated its own purpose.
"""

import logging

from pydantic import BaseModel, Field

from src.config import settings

logger = logging.getLogger(__name__)

# Every exercise type the router may name, and the count each one implies. This is the *same*
# convention as the vision gate below — conic carries its vanishing-point count, a parallel
# projection carries 3 for its three axes, and anything the engine does not measure carries 0 —
# so the stage that reads words and the stage that looks at the page cannot disagree about what a
# word means.
#
# The list was conic-only until the axonometric and orthographic engines existed, and nobody
# extended it. Asking a schema-constrained model to classify "an isometric cube" into a set that
# has no axonometric member does not produce a wrong answer: it produces no answer at all. The
# model spent its whole budget reasoning and never emitted the JSON, and the reader watched a
# frozen page for as long as the client would wait. Adding a system to the engine means adding it
# here, in the same commit.
ONE_POINT_CONICAL = "one-point-conical"
TWO_POINT_OBLIQUE = "two-point-oblique"
CURVILINEAR = "curvilinear"
ISOMETRIC = "isometric"
DIMETRIC = "dimetric"
CAVALIER = "cavalier"
ORTHOGRAPHIC_TWO_VIEW = "orthographic-two-view"
FREEHAND = "freehand"

K_BY_TYPE = {
    ONE_POINT_CONICAL: 1,
    TWO_POINT_OBLIQUE: 2,
    ISOMETRIC: 3,
    DIMETRIC: 3,
    CAVALIER: 3,
    ORTHOGRAPHIC_TWO_VIEW: 0,
    # Neither of these is measured by any of the three engines, so neither carries a count.
    CURVILINEAR: 0,
    FREEHAND: 0,
}

# How long the router may take before the fallback is used instead. The failure this bounds is
# not slowness but silence: a request that never completes.
#
# **The Gemini API refuses anything under 10s** — `400 INVALID_ARGUMENT: Manually set deadline 8s
# is too short. Minimum allowed deadline is 10s.` A deadline it rejects is worse than none: every
# call fails instantly and every reader gets the fallback, which is what 8000 did here in
# production for the four minutes it took to read the log. 12s clears the floor and is still
# seven times the 1.6s the model takes when it answers at all.
ROUTER_TIMEOUT_MS = 12000

ROUTER_SYSTEM_PROMPT = """You route a drawing to the right system of representation before any
measurement happens. You are given only the student's own words about what they were practising.

The systems are the ones descriptive geometry names, and they are measured against unrelated
references, so telling them apart is the whole job:

CONIC (perspectiva cónica) — receding edges converge on vanishing points.
- ONE-POINT CONICAL (cónica frontal): the picture plane is parallel to a principal face, so one
  family of edges recedes to a single vanishing point. A corridor, a road, a room from the doorway,
  a box seen face-on.
- TWO-POINT OBLIQUE (cónica oblicua): the subject is turned to the picture plane, so two families
  recede to F1 and F2. A building corner, a box at an angle, an oblique street view.
- CURVILINEAR: three-point or fisheye. Named for completeness; not measured.

AXONOMETRIC (proyección paralela) — edges stay parallel and never meet. There is no vanishing
point at all.
- ISOMETRIC: three axes evenly spaced at 30, 150 and 90 degrees; the cube reads as a hexagon.
- DIMETRIC: two axes share a scale and the third does not.
- CAVALIER: one face is a true square facing the viewer and depth runs off at a slant, often 45.

ORTHOGRAPHIC (sistema diédrico, Monge) — two flat views about a ground line: a plan below and an
elevation above, each point in one lying directly under its counterpart in the other.

FREEHAND: a sketch with no construction the student names.

Answer with:
- exercise_type: 'one-point-conical', 'two-point-oblique', 'curvilinear', 'isometric', 'dimetric',
  'cavalier', 'orthographic-two-view' or 'freehand'
- recommended_k: 1 or 2 for conic, by how many vanishing points the words imply. 3 for any
  axonometric system, because a parallel projection shows three axes and no vanishing point.
  0 for orthographic, curvilinear and freehand, which have neither.
- reasoning: one short sentence naming the words that decided it

Answer with one of those values and nothing else. If the description does not say which system it
is, choose the fallback you are told and say so in the reasoning. Never invent detail the student
did not give you."""


class RoutingDecision(BaseModel):
    """What the router is allowed to decide. Provenance is stamped by the caller, not the model."""

    exercise_type: str = Field(
        ...,
        description=(
            "'one-point-conical' (cónica frontal), 'two-point-oblique' (cónica oblicua), "
            "'curvilinear', 'isometric', 'dimetric', 'cavalier', 'orthographic-two-view' "
            "(sistema diédrico) or 'freehand'"
        ),
    )
    recommended_k: int = Field(
        1,
        description=(
            "1 or 2 for conic, by vanishing point count. 3 for any axonometric system, for its "
            "three axes. 0 for orthographic, curvilinear and freehand, which have neither."
        ),
    )
    reasoning: str = Field("", description="One sentence naming what in the description decided it")


class RoutingResult(RoutingDecision):
    """A routing decision plus where it came from."""

    source: str = Field("fallback", description="'gemma' when the router model decided, 'fallback' when the profile did")
    model_version: str = Field("profile-level", description="Set by the server, never by the model")


def route_from_intent(student_intent: str | None, student_level: str = "beginner") -> RoutingResult:
    """
    Choose the perspective model, preferring the student's description over their profile.

    Falls back to the level-based guess when there is nothing to read or the model is
    unreachable — and says which happened. The previous version could not tell you either.
    """
    fallback_k = 2 if student_level.lower() == "advanced" else 1
    fallback = RoutingResult(
        exercise_type=TWO_POINT_OBLIQUE if fallback_k == 2 else ONE_POINT_CONICAL,
        recommended_k=fallback_k,
        reasoning=f"No usable description; fell back to the student's level ({student_level}).",
        source="fallback",
        model_version="profile-level",
    )

    if not student_intent or not student_intent.strip():
        return fallback

    try:
        from google import genai
        from google.genai import types

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is unset; the Gemma router is unreachable.")

        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=ROUTER_TIMEOUT_MS),
        )
        response = client.models.generate_content(
            model=settings.router_model,
            contents=(
                f'The student wrote: "{student_intent.strip()}"\n'
                f"If it does not say, fall back to k={fallback_k} (their level is {student_level})."
            ),
            config=types.GenerateContentConfig(
                system_instruction=ROUTER_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=RoutingDecision,
                temperature=0.0,
            ),
        )
        if not response.text:
            raise ValueError("Empty routing response.")

        decision = RoutingDecision.model_validate_json(response.text)
        # Observed on this model: it answered `two-point-oblique` with `recommended_k=1` for "a box
        # at an angle". A router that contradicts itself is not usable output, whichever half is
        # right, so it is refused rather than half-believed. A type outside the table is refused
        # for the same reason: an answer we cannot map is not an answer.
        expected_k = K_BY_TYPE.get(decision.exercise_type)
        if expected_k is None:
            raise ValueError(f"Router returned an unknown exercise type: {decision.exercise_type!r}.")
        if decision.recommended_k != expected_k:
            raise ValueError(
                f"Router contradicted itself: {decision.exercise_type} with k={decision.recommended_k}."
            )

        return RoutingResult(
            **decision.model_dump(),
            source="gemma",
            model_version=settings.router_model,
        )
    except Exception as exc:  # noqa: BLE001 - reported, not swallowed
        logger.warning(
            "Routing model unavailable (%s: %s); falling back to the student's level.",
            type(exc).__name__,
            exc,
        )
        return fallback


# ---------------------------------------------------------------------------------------------
# The gate: is this even a perspective exercise?
# ---------------------------------------------------------------------------------------------

GATE_SYSTEM_PROMPT = """You look at a photograph of a page and decide whether it is a technical
drawing exercise that a geometry engine should measure, and if so, which kind.

There are three kinds, and telling them apart is the whole job:

- CONIC PERSPECTIVE: receding edges CONVERGE. Follow two edges that run away from the viewer and
  they meet, on the page or off it. There is a horizon.
- AXONOMETRIC (parallel projection: isometric, dimetric, cavalier): receding edges stay PARALLEL.
  They never meet. An isometric cube reads as a regular hexagon; a cavalier box has a square front
  face with depth running off at a constant slant. There is no horizon and no vanishing point.
- ORTHOGRAPHIC (sistema diedrico / Monge): NOT a picture of a solid at all. Two flat, separate
  views of the same object - a plan and an elevation - laid out on the page and divided by one long
  horizontal rule, the ground line, with thin vertical reference lines carrying points between
  them. Nothing in it looks three-dimensional. Two flat outlines stacked above and below a long
  horizontal line is this and nothing else.

Answer with:
- is_exercise: true only if there are straight construction lines forming a spatial construction.
  A finished illustration, a portrait, a photograph of an object, a page of text, a blank page, or
  an image too blurred to read straight edges: all false.
- projection: 'conic' when edges converge, 'axonometric' when they stay parallel, 'orthographic'
  for two flat views about a ground line, 'none' when this is not an exercise.
- exercise_type: 'one-point-conical', 'two-point-oblique', 'curvilinear', 'isometric',
  'dimetric', 'cavalier', 'orthographic-two-view' or 'not-an-exercise'
- axonometric_system: 'isometric', 'dimetric' or 'cavalier' when projection is axonometric; null
  otherwise. Isometric: three axes evenly spaced, the solid reads as a hexagon. Cavalier: one face
  is a true square or rectangle facing the viewer, and depth runs off at a slant.
- recommended_k: for conic, 1 or 2. For axonometric, 3, because a parallel projection shows three
  axes. For orthographic, 0 - it has neither vanishing points nor axes to count. 0 when it is not
  an exercise.
- reasoning: one short sentence saying what you saw

Be strict, and do not guess between the kinds. If the edges converge it is conic; if they stay
parallel and the drawing shows a solid, it is axonometric; if it shows two flat views split by a
long horizontal line, it is orthographic. Measuring an axonometric drawing as if it were
perspective finds a vanishing point among lines that were never meant to meet, and then reports an
error about it. Measuring an orthographic plate as either would be worse: there is no solid in it
to measure at all."""


class DrawingGateDecision(BaseModel):
    """What the vision model may decide about the photograph."""

    is_exercise: bool = Field(..., description="Whether this is a drawing exercise worth measuring")
    projection: str = Field(
        "conic",
        description=(
            "'conic' when receding edges converge, 'axonometric' when they stay parallel, "
            "'orthographic' for two flat views about a ground line, 'none' when this is not an "
            "exercise. This selects the reference the engine measures against, and the three have "
            "nothing in common: conic estimates a vanishing point from the drawing, axonometric "
            "compares against fixed axis angles, and orthographic compares the two views with each "
            "other about the ground line."
        ),
    )
    exercise_type: str = Field(
        "not-an-exercise",
        description="'one-point-conical', 'two-point-oblique', 'curvilinear', 'isometric', 'dimetric', 'cavalier', 'orthographic-two-view' or 'not-an-exercise'",
    )
    axonometric_system: str | None = Field(
        None, description="'isometric', 'dimetric' or 'cavalier' when projection is axonometric"
    )
    recommended_k: int = Field(0, description="1 or 2 for conic, 3 for axonometric, 0 when not measurable")
    reasoning: str = Field("", description="One sentence describing what was seen")


class DrawingGateResult(DrawingGateDecision):
    """A gate decision plus where it came from."""

    source: str = Field("fallback", description="'vertex' when the model looked, 'fallback' when it could not")
    model_version: str = Field("none", description="Set by the server, never by the model")


def classify_drawing(image_bytes: bytes, mime_type: str = "image/png") -> DrawingGateResult:
    """
    Decide whether a photograph is worth measuring, before anything expensive happens.

    This is the step the original design asked for — *1-point / 2-point / not-an-exercise, before
    the analysis* — and the deleted module never performed: it read no image and returned a
    branch on a string. The valuable class is the third one. Without it, a photograph of a cat
    goes through RANSAC, produces a vanishing point from whatever edges exist, and a critique
    call spends real tokens telling a student their line weight is confident.

    **On failure it opens rather than closes.** An unreachable model must not silently stop a
    student's work from being marked; the fallback says `is_exercise=True` and labels itself
    `fallback`, so the caller can tell the difference between "we looked and it is a drawing"
    and "we could not look".
    """
    # The open gate stays conic on purpose. It is the behaviour every existing caller already
    # gets, and a fallback is the wrong place to start guessing at a projection system: choosing
    # the wrong reference would produce a confident measurement of the wrong thing, which is worse
    # than the unchecked pass this branch already admits to.
    open_gate = DrawingGateResult(
        is_exercise=True,
        projection="conic",
        exercise_type="one-point-conical",
        axonometric_system=None,
        recommended_k=1,
        reasoning="The gate model could not be reached; the drawing was let through unchecked.",
        source="fallback",
        model_version="none",
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            vertexai=True,
            project=settings.gcp_project,
            location=settings.gemini_location,
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                "Is this a technical drawing exercise, and is it conic or axonometric?",
            ],
            config=types.GenerateContentConfig(
                system_instruction=GATE_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=DrawingGateDecision,
                temperature=0.0,
            ),
        )
        if not response.text:
            raise ValueError("Empty gate response.")

        decision = DrawingGateDecision.model_validate_json(response.text)

        # The answer has to be internally consistent before it is allowed to select a measurement
        # reference. An 'axonometric' verdict naming no system would otherwise fall through to
        # whichever default the caller happened to pass.
        if decision.is_exercise:
            if decision.projection == "axonometric":
                if decision.axonometric_system not in ("isometric", "dimetric", "cavalier"):
                    raise ValueError(
                        f"Gate said axonometric but named system {decision.axonometric_system!r}."
                    )
            elif decision.projection == "conic":
                if decision.recommended_k not in (1, 2):
                    raise ValueError(f"Gate said conic but k={decision.recommended_k}.")
            elif decision.projection == "orthographic":
                pass  # Nothing further to check: neither a k nor a named axis system applies.
            else:
                raise ValueError(f"Gate said exercise but projection={decision.projection!r}.")

        return DrawingGateResult(
            **decision.model_dump(),
            source="vertex",
            model_version=settings.gemini_model,
        )
    except Exception as exc:  # noqa: BLE001 - reported, not swallowed
        logger.warning(
            "Drawing gate unavailable (%s: %s); letting the image through unchecked.",
            type(exc).__name__,
            exc,
        )
        return open_gate
