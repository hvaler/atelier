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
    """`curvilinear` carries no vanishing-point count, so k=3 against it is a contradiction.

    k=3 is *not* refused on its own any more — it is what an axonometric system carries. What
    is refused is a type and a count that disagree, whichever pair they are.
    """

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
    monkeypatch.setattr(pre_router.settings, "gemini_api_key", "test-key")

    result = route_from_intent("a spiral staircase", "advanced")

    assert result.source == "fallback", "k=3 should have been refused, not passed through"
    assert result.recommended_k == 2


def test_a_real_decision_is_labelled_as_one(monkeypatch):
    """The happy path stamps `vertex` and the configured model, both set by the server."""

    class FakeResponse:
        text = (
            '{"exercise_type": "two-point-oblique", "recommended_k": 2, '
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
    # The Gemma router authenticates with an API key, not ADC; CI has neither.
    monkeypatch.setattr(pre_router.settings, "gemini_api_key", "test-key")

    result = route_from_intent("the corner of a building", "beginner")

    assert result.source == "gemma"
    assert result.model_version == pre_router.settings.router_model
    # The description wins over the profile: a beginner who drew a corner is measured as one.
    assert result.recommended_k == 2


def test_no_api_key_is_a_labelled_fallback(monkeypatch):
    """Without a key the router cannot reach Gemma, and says so rather than guessing."""
    monkeypatch.setattr(pre_router.settings, "gemini_api_key", None)

    result = route_from_intent("the corner of a building", "beginner")

    assert result.source == "fallback"
    assert result.recommended_k == 1


def _fake_router(monkeypatch, payload: str) -> None:
    """Point the router at a canned response without credentials."""

    class FakeResponse:
        text = payload

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.models = FakeModels()

    import google.genai

    monkeypatch.setattr(google.genai, "Client", FakeClient)
    monkeypatch.setattr(pre_router.settings, "gemini_api_key", "test-key")


def test_a_parallel_projection_is_routable(monkeypatch):
    """The taxonomy covers the three systems the engine measures, not conic alone.

    While it was conic-only, "an isometric cube" asked a schema-constrained model for a value
    its schema could not express. It did not answer wrongly; it did not answer at all, and the
    reader watched a frozen page until the client gave up.
    """
    _fake_router(
        monkeypatch,
        '{"exercise_type": "isometric", "recommended_k": 3, "reasoning": "the student wrote isometric"}',
    )

    result = route_from_intent("an isometric cube", "beginner")

    assert result.source == "gemma"
    assert result.exercise_type == "isometric"
    assert result.recommended_k == 3, "a parallel projection carries its three axes, not a k of 1"


def test_orthographic_carries_no_count(monkeypatch):
    """A Monge plate has neither vanishing points nor axes to count, so k is 0."""
    _fake_router(
        monkeypatch,
        '{"exercise_type": "orthographic-two-view", "recommended_k": 0, "reasoning": "plan and elevation"}',
    )

    result = route_from_intent("a plan and an elevation about a ground line", "advanced")

    assert result.source == "gemma"
    assert result.recommended_k == 0


def test_a_type_outside_the_table_is_refused(monkeypatch):
    """An answer that cannot be mapped is not an answer, and is not passed through as one."""
    _fake_router(
        monkeypatch,
        '{"exercise_type": "trimetric", "recommended_k": 3, "reasoning": "invented a system"}',
    )

    result = route_from_intent("a trimetric drawing", "beginner")

    assert result.source == "fallback", "an unmappable type should degrade, not be believed"
    assert result.model_version == "profile-level"


def test_the_router_is_given_a_deadline(monkeypatch):
    """The failure this bounds is silence, not slowness: a request that never completes.

    Recorded against the deployed service: descriptions naming an axonometric system returned
    nothing at all, and what eventually unblocked the interface was the .NET client's 100s
    default. The deadline belongs on the call, not on whoever happens to be waiting for it.
    """
    seen = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            raise TimeoutError("deadline exceeded")

    class FakeClient:
        def __init__(self, *args, **kwargs):
            seen.update(kwargs)
            self.models = FakeModels()

    import google.genai

    monkeypatch.setattr(google.genai, "Client", FakeClient)
    monkeypatch.setattr(pre_router.settings, "gemini_api_key", "test-key")

    result = route_from_intent("an isometric cube", "beginner")

    assert seen["http_options"].timeout == pre_router.ROUTER_TIMEOUT_MS
    assert pre_router.ROUTER_TIMEOUT_MS <= 15000, "a deadline nobody reaches is not a deadline"
    assert result.source == "fallback"
    assert result.model_version == "profile-level"


def test_the_gate_opens_when_it_cannot_look(monkeypatch):
    """
    An unreachable vision model must not block a student's work — but must not pretend it looked.

    Failing open is the right call here and the opposite of the rule elsewhere in this codebase:
    refusing every drawing because Vertex is down would be worse than measuring one that should
    not have been measured. What matters is that `source` says which happened.
    """

    class Boom:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("no route to host")

    import google.genai

    monkeypatch.setattr(google.genai, "Client", Boom)

    result = pre_router.classify_drawing(b"not really a png")

    assert result.is_exercise is True
    assert result.source == "fallback"
    assert result.model_version == "none"
