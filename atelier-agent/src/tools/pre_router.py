"""
Pre-routing: decide which perspective model to measure against, from what the student said.

**This replaces `gemma_router.py`, which did not work and could not.** That module constructed
a `genai.Client`, discarded it, and returned a hardcoded branch on `student_level_hint` — a
string the caller had already supplied. It reported a `confidence` of 0.94 for a decision no
model made, and the `canny_thresholds` it "recommended" were consumed by nothing:
`geometry.py` hardcoded `cv2.Canny(blurred, 50, 150)`. It was documented across the README,
the architecture diagram and the evidence log as a shipped Vertex AI feature.

**Why it is no longer called Gemma.** Gemma is not a publisher model on Vertex AI — reaching it
needs a Model Garden endpoint, which is a deployed and billed resource. Verified against this
project: `gemma-3-27b-it`, `-12b-it` and `-4b-it` all return `404 NOT_FOUND`, as do every
`*-flash-lite` variant. The only model this project can call is `gemini-3.5-flash`. Naming a
module after a model it cannot reach is how the previous version came to exist.

**Why the routing step is worth keeping at all.** The old one recommended `k`, which the caller
already knew: `k` came from `student.level`, a stored profile field. A router that returns a
value you passed in is not a router. This one reads the student's own description of what they
were practising — the free text from the ASK verb — and picks the perspective model from that.
A beginner who drew a two-point corridor gets measured as a two-point drawing, because they
said so, rather than as one-point because of a field in their profile.
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

    source: str = Field("fallback", description="'vertex' when a model decided, 'fallback' when the profile did")
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

        client = genai.Client(
            vertexai=True,
            project=settings.gcp_project,
            location=settings.gemini_location,
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
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

        return RoutingResult(
            **decision.model_dump(),
            source="vertex",
            model_version=settings.gemini_model,
        )
    except Exception as exc:  # noqa: BLE001 - reported, not swallowed
        logger.warning(
            "Routing model unavailable (%s: %s); falling back to the student's level.",
            type(exc).__name__,
            exc,
        )
        return fallback
