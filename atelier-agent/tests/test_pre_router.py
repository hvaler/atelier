"""
Tests for the intent-based pre-router.

The module these replace asserted a stub's own hardcoded constants back at itself:
`test_gemma_router.py` checked that a function returning `recommended_k=2` for
`student_level_hint="advanced"` returned 2 for "advanced". It could not fail, and it passed
while the router it covered constructed a model client and never called it.

These run without credentials, which is the point: every case below is either the deterministic
fallback path or an injected failure, so CI exercises the behaviour that matters — that an
unreachable model produces a *labelled* fallback rather than a confident invention.
"""

from src.tools import pre_router
from src.tools.pre_router import route_from_intent


def test_no_description_falls_back_to_the_profile_level():
    """With nothing to read, the router says so instead of guessing."""
    beginner = route_from_intent(None, "beginner")
    advanced = route_from_intent("   ", "advanced")

    assert beginner.recommended_k == 1
    assert advanced.recommended_k == 2
    assert beginner.source == "fallback"
    assert advanced.source == "fallback"
    assert "level" in beginner.reasoning.lower()


def test_fallback_never_claims_a_model_produced_it():
    """`model_version` is the server's word, not the model's."""
    result = route_from_intent(None, "beginner")

    assert result.source == "fallback"
    assert result.model_version == "profile-level"
    # The old router stamped a confidence of 0.94 on a decision no model made.
    assert not hasattr(result, "confidence")


def test_an_unreachable_model_degrades_visibly(monkeypatch):
    """
    When Vertex cannot be reached the answer is still usable — and still says it is a fallback.

    This is the invariant the previous design broke everywhere: a swallowed failure that
    presented itself as a successful model call.
    """

    class Boom:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("no route to host")

    import google.genai

    monkeypatch.setattr(google.genai, "Client", Boom)

    result = route_from_intent("the corner of a building", "beginner")

    assert result.source == "fallback"
    assert result.model_version == "profile-level"
    assert result.recommended_k == 1  # the beginner default, not an invented 2


def test_only_measurable_vanishing_point_counts_are_accepted(monkeypatch):
    """A router that returns k=3 is rejected: the solver measures 1 and 2."""

    class FakeResponse:
        text = '{"exercise_type": "curvilinear", "recommended_k": 3, "reasoning": "three points"}'

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.models = FakeModels()

    import google.genai

    monkeypatch.setattr(google.genai, "Client", FakeClient)

    result = route_from_intent("a spiral staircase", "advanced")

    assert result.source == "fallback", "k=3 should have been refused, not passed through"
    assert result.recommended_k == 2


def test_a_real_decision_is_labelled_as_one(monkeypatch):
    """The happy path stamps `vertex` and the configured model, both set by the server."""

    class FakeResponse:
        text = (
            '{"exercise_type": "2-point-oblique", "recommended_k": 2, '
            '"reasoning": "the student wrote corner"}'
        )

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.models = FakeModels()

    import google.genai

    monkeypatch.setattr(google.genai, "Client", FakeClient)

    result = route_from_intent("the corner of a building", "beginner")

    assert result.source == "vertex"
    assert result.model_version == pre_router.settings.gemini_model
    # The description wins over the profile: a beginner who drew a corner is measured as one.
    assert result.recommended_k == 2
