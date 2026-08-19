"""Pydantic data models for append-only memory events and collaborative dialog (ADR-003, ADR-005)."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.models.axonometry import AxonometricAnalysisResult
from src.models.critique import CritiqueOutput, NextExerciseRecommendation, StudentProfile
from src.models.dihedral import DihedralAnalysisResult
from src.models.geometry import GeometryAnalysisResult


def get_current_utc_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


class FeedbackEvent(BaseModel):
    """Immutable feedback event captured from the student (CAPTURE step)."""

    feedback_id: str
    exercise_id: str
    student_id: str
    helpful: bool = Field(..., description="Whether the student found the critique helpful")
    note: str | None = Field(None, description="Optional text feedback or clarification from student")
    created_at: str = Field(default_factory=get_current_utc_iso)


class ExerciseRecord(BaseModel):
    """Immutable record of an uploaded exercise and its analysis / critique."""

    exercise_id: str
    student_id: str
    image_uri: str | None = Field(None, description="GCS URI or local path")
    source: str = Field("ui", description="'ui' or 'folder'")
    student_intent: str | None = Field(None, description="What the student intended to practice (ASK)")
    student_difficulty: str | None = Field(None, description="What felt hardest during the drawing (ASK)")
    geometry_analysis: GeometryAnalysisResult | None = Field(
        None, description="Conic perspective measurements, when that is what was drawn"
    )
    axonometric_analysis: AxonometricAnalysisResult | None = Field(
        None,
        description=(
            "Parallel-projection measurements, when that is what was drawn. Kept in its own field "
            "rather than coerced into the perspective one: an average axis deviation and an "
            "average convergence error are both 'degrees' and are not the same measurement, and a "
            "progress curve that mixed them would be a line through two different quantities."
        ),
    )
    dihedral_analysis: DihedralAnalysisResult | None = Field(
        None,
        description=(
            "Orthographic measurements, when that is what was drawn. A third field rather than a "
            "shared one for the same reason as the second: a correspondence error in pixels and a "
            "convergence error in degrees are not comparable, and a single progress curve through "
            "all three would be a line through three different quantities."
        ),
    )
    critique: CritiqueOutput
    feedback_events: list[FeedbackEvent] = Field(default_factory=list)
    created_at: str = Field(default_factory=get_current_utc_iso)


class ProgressPoint(BaseModel):
    timestamp: str
    exercise_id: str
    avg_convergence_error_deg: float
    k_points: int


class DerivedProfile(BaseModel):
    """Dynamically derived student profile computed from immutable event history (ADAPT step)."""

    student: StudentProfile
    total_exercises: int
    overall_avg_error_deg: float
    progress_curve: list[ProgressPoint]
    recurring_issues: list[str]
    derived_tone_preference: str
    recent_helpful_ratio: float
    current_practice_focus: str
    recommended_next_exercise: NextExerciseRecommendation


class AskPromptData(BaseModel):
    """Clarifying questions presented to the student before analyzing (ASK step)."""

    student_id: str
    student_name: str
    intent_question: str
    difficulty_question: str
    quick_intent_suggestions: list[str]
    quick_difficulty_suggestions: list[str]
