"""Collaborative Partner Agent orchestration: The 4 verbs (ASK, GUIDE, CAPTURE, ADAPT)."""


from src.models.critique import NextExerciseRecommendation, StudentProfile
from src.models.memory import (
    AskPromptData,
    DerivedProfile,
    FeedbackEvent,
)
from src.tools.memory import memory_repo

# The ASK step is the first thing a student reads, and it is written here rather than by a model:
# these are fixed questions, and a fixed question in the wrong language is a worse answer than a
# generated one. Keyed by (language, level) so the beginner and advanced registers stay distinct
# in both — the basic level is asked about boxes, the advanced level about construction axes.
_ASK_SCRIPTS: dict[tuple[str, str], dict[str, object]] = {
    ("en", "beginner"): {
        "intent": "What kind of 3D shape or box were you practising today?",
        "difficulty": "Which line or corner felt the most tricky to get right?",
        "intents": [
            "My first 3D box on a table",
            "A box floating in the sky",
            "A house shape with a pointy roof",
        ],
        "difficulties": [
            "Drawing straight lines",
            "Making the back face look right",
            "Aiming towards the horizon dot",
        ],
    },
    ("en", "advanced"): {
        "intent": "Which exercise or spatial construction were you working on?",
        "difficulty": "Which construction axis or plane felt hardest to calibrate?",
        "intents": [
            "2-Point perspective volumetric cube cluster",
            "Stepped architectural elevation",
            "Foreshortened ground plane with True Heights on LT",
        ],
        "difficulties": [
            "Converging secondary edges strictly to F1",
            "Maintaining true 90° verticals without slant",
            "Controlling line weight between construction and solution",
        ],
    },
    ("es", "beginner"): {
        "intent": "¿Qué caja o forma en 3D estabas practicando hoy?",
        "difficulty": "¿Qué línea o esquina te ha costado más?",
        "intents": [
            "Mi primera caja en 3D sobre una mesa",
            "Una caja flotando en el cielo",
            "Una casa con el tejado en punta",
        ],
        "difficulties": [
            "Hacer las líneas rectas",
            "Que la cara de atrás quede bien",
            "Apuntar al punto del horizonte",
        ],
    },
    ("es", "advanced"): {
        "intent": "¿Qué ejercicio o construcción espacial estabas haciendo?",
        "difficulty": "¿Qué eje de construcción o plano te ha costado más calibrar?",
        "intents": [
            "Grupo de cubos volumétricos en perspectiva de 2 puntos",
            "Alzado arquitectónico escalonado",
            "Plano de tierra escorzado con alturas verdaderas sobre la LT",
        ],
        "difficulties": [
            "Hacer converger las aristas secundarias exactamente en F1",
            "Mantener las verticales a 90° sin inclinación",
            "Controlar el grosor entre línea de construcción y línea definitiva",
        ],
    },
}


def ask_clarification(student_id: str, language: str = "en") -> AskPromptData:
    """Verb 1: ASK clarifying questions before analyzing the drawing.

    "Ask clarifying questions, guide the user step-by-step..."
    """
    student = memory_repo.get_student(student_id)
    if not student:
        student = StudentProfile(student_id=student_id, name="Student", level="advanced")

    level = "beginner" if student.level == "beginner" else "advanced"
    script = _ASK_SCRIPTS.get((language, level)) or _ASK_SCRIPTS[("en", level)]

    return AskPromptData(
        student_id=student.student_id,
        student_name=student.name,
        # No name interpolation. The profiles are levels, not people: there is nobody to greet,
        # and a question addressed to "basic" would read worse than one addressed to no one.
        intent_question=script["intent"],
        difficulty_question=script["difficulty"],
        quick_intent_suggestions=list(script["intents"]),
        quick_difficulty_suggestions=list(script["difficulties"]),
    )


def guide_next_exercise(student_id: str) -> NextExerciseRecommendation:
    """Verb 2: GUIDE - Propose targeted follow-up exercise based on recurring error pattern."""
    profile = memory_repo.derive_profile(student_id)
    return profile.recommended_next_exercise


def capture_feedback(
    exercise_id: str,
    student_id: str,
    helpful: bool,
    note: str | None = None,
) -> FeedbackEvent:
    """Verb 3: CAPTURE - Save explicit student feedback event to append-only memory."""
    event = memory_repo.record_feedback(
        exercise_id=exercise_id,
        student_id=student_id,
        helpful=helpful,
        note=note,
    )
    if not event:
        raise ValueError(f"Exercise '{exercise_id}' not found for student '{student_id}'.")
    return event


def adapt_profile(student_id: str) -> DerivedProfile:
    """Verb 4: ADAPT - Dynamically derive updated learning profile and tone from feedback events."""
    return memory_repo.derive_profile(student_id)
