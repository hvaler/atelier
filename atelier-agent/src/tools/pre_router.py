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

ROUTER_SYSTEM_PROMPT = """You route a drawing to the right perspective model before any
measurement happens. You are given only the student's own words about what they were practising.

Answer with:
- exercise_type: '1-point-box', '2-point-oblique', 'curvilinear' or 'freehand'
- recommended_k: 1 when a single vanishing point is implied (a corridor, a road, a box seen
  face-on, a room from the doorway); 2 when the subject is seen from a corner (a building
  corner, a box at an angle, an oblique street view)
- reasoning: one short sentence naming the words that decided it

If the description does not say, choose the fallback you are told and say so in the reasoning.
Never invent detail the student did not give you."""


class RoutingDecision(BaseModel):
    """What the router is allowed to decide. Provenance is stamped by the caller, not the model."""

    exercise_type: str = Field(..., description="'1-point-box', '2-point-oblique', 'curvilinear' or 'freehand'")
    recommended_k: int = Field(1, description="Vanishing point count to measure against: 1 or 2")
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
        exercise_type="2-point-oblique" if fallback_k == 2 else "1-point-box",
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

        client = genai.Client(api_key=settings.gemini_api_key)
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
        if decision.recommended_k not in (1, 2):
            raise ValueError(f"Router returned k={decision.recommended_k}; only 1 and 2 are measurable.")
        # Observed on this model: it answered `2-point-oblique` with `recommended_k=1` for "a box
        # at an angle". A router that contradicts itself is not usable output, whichever half is
        # right, so it is refused rather than half-believed.
        expected_k = 2 if "2-point" in decision.exercise_type else 1
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
- exercise_type: '1-point-box', '2-point-oblique', 'curvilinear', 'isometric', 'dimetric',
  'cavalier', 'orthographic-two-view' or 'not-an-exercise'
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
        description="'1-point-box', '2-point-oblique', 'curvilinear', 'isometric', 'dimetric', 'cavalier', 'orthographic-two-view' or 'not-an-exercise'",
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
    call spends real tokens telling a child their line weight is confident.

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
        exercise_type="1-point-box",
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
