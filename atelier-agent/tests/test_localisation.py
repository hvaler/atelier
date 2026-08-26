"""
Tests for the parts of the agent that change when the student changes language.

Translating an interface is usually cosmetic. Here it is not: the critique is prose written by a
model, and two of the agent's guarantees are enforced by reading that prose. A validator that only
recognises the word "degrees" stops being a validator the moment the prose is Spanish, and a cache
keyed without the language serves an English answer to a Spanish request. Both failures are
invisible — the screen looks right — so they are asserted here rather than trusted.
"""

from src.models.critique import CritiqueRequest, StudentProfile
from src.models.geometry import GeometryAnalysisResult
from src.tools.collaborative import ask_clarification
from src.tools.critique import get_cache_key
from src.tools.validator import _MEASUREMENT_IN_PROSE


def _request(language: str) -> CritiqueRequest:
    return CritiqueRequest(
        geometry=GeometryAnalysisResult(
            k_requested=1,
            k_detected=1,
            avg_convergence_error_deg=0.82,
            max_convergence_error_deg=2.53,
            line_count=32,
            confidence=1.0,
            image_width=800,
            image_height=600,
        ),
        student=StudentProfile(student_id="level-basic", name="basic", level="beginner"),
        language=language,
    )


class TestProseDegreeGate:
    """Plane B may not state a measurement — in either language."""

    def test_catches_spanish_degrees(self):
        assert _MEASUREMENT_IN_PROSE.search("la desviación es de 4,2 grados")

    def test_catches_spanish_singular(self):
        assert _MEASUREMENT_IN_PROSE.search("se desvía 1 grado del punto de fuga")

    def test_catches_english_degrees(self):
        assert _MEASUREMENT_IN_PROSE.search("tilted 3.1 degrees away")

    def test_catches_the_symbol_in_either_language(self):
        assert _MEASUREMENT_IN_PROSE.search("a 9° del punto de fuga")

    def test_lets_qualitative_prose_through(self):
        """The gate exists to stop numbers, not to stop Plane B from saying anything."""
        assert not _MEASUREMENT_IN_PROSE.search(
            "Tus líneas son firmes y el grosor distingue bien construcción de trazo definitivo."
        )


class TestCacheKey:
    def test_language_changes_the_key(self):
        """Otherwise the first English critique is replayed to a Spanish reader."""
        assert get_cache_key(_request("en")) != get_cache_key(_request("es"))

    def test_same_language_same_key(self):
        assert get_cache_key(_request("es")) == get_cache_key(_request("es"))


class TestAskQuestions:
    def test_spanish_questions_are_spanish(self):
        ask = ask_clarification("level-basic", language="es")
        assert "¿" in ask.difficulty_question
        assert all(s for s in ask.quick_intent_suggestions)

    def test_english_is_the_default(self):
        ask = ask_clarification("level-basic")
        assert "What" in ask.intent_question or "what" in ask.intent_question

    def test_unknown_language_falls_back_to_english_rather_than_emptiness(self):
        """A language we do not have is answered in one we do, not with blanks."""
        ask = ask_clarification("level-basic", language="eu")
        assert ask.intent_question
        assert len(ask.quick_intent_suggestions) == 3

    def test_the_two_levels_stay_distinct_in_spanish(self):
        """The basic level is asked about boxes; the advanced level about construction."""
        beginner = ask_clarification("level-basic", language="es")
        advanced = ask_clarification("level-advanced", language="es")
        assert beginner.intent_question != advanced.intent_question
        assert beginner.quick_intent_suggestions != advanced.quick_intent_suggestions
