"""Collaborative Partner Agent orchestration: The 4 verbs (ASK, GUIDE, CAPTURE, ADAPT)."""


from src.models.critique import NextExerciseRecommendation, StudentProfile
from src.models.memory import (
    AskPromptData,
    DerivedProfile,
    FeedbackEvent,
)
from src.tools.memory import memory_repo


def ask_clarification(student_id: str) -> AskPromptData:
    """Verb 1: ASK clarifying questions before analyzing the drawing.

    "Ask clarifying questions, guide the user step-by-step..."
    """
    student = memory_repo.get_student(student_id)
    if not student:
        student = StudentProfile(student_id=student_id, name="Student", level="advanced")

    is_beginner = student.level == "beginner"

    if is_beginner:
        intent_q = f"Hi {student.name}! What kind of 3D shape or box were you practicing today?"
        diff_q = "Which line or corner felt the most tricky to get right?"
        quick_intents = [
            "My first 3D box on a table",
            "A box floating in the sky",
            "A house shape with a pointy roof",
        ]
        quick_diffs = [
            "Drawing straight lines",
            "Making the back face look right",
            "Aiming towards the horizon dot",
        ]
    else:
        intent_q = f"Hello {student.name}. What perspective exercise or spatial setup were you working on?"
        diff_q = "Which construction axis or plane felt hardest to calibrate?"
        quick_intents = [
            "2-Point perspective volumetric cube cluster",
            "Stepped architectural elevation",
            "Foreshortened ground plane with True Heights on LT",
        ]
        quick_diffs = [
            "Converging secondary edges strictly to F1",
            "Maintaining true 90° verticals without slant",
            "Controlling line weight between construction and solution",
        ]

    return AskPromptData(
        student_id=student.student_id,
        student_name=student.name,
        intent_question=intent_q,
        difficulty_question=diff_q,
        quick_intent_suggestions=quick_intents,
        quick_difficulty_suggestions=quick_diffs,
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
