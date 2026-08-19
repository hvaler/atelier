"""Append-only memory repository and dynamic profile derivation engine (ADR-003, ADR-005, PAT-004)."""

import logging
import uuid

import numpy as np

from src.config import settings
from src.models.critique import (
    NextExerciseRecommendation,
    StudentProfile,
)
from src.models.memory import (
    DerivedProfile,
    ExerciseRecord,
    FeedbackEvent,
    ProgressPoint,
    get_current_utc_iso,
)

logger = logging.getLogger(__name__)


class MemoryRepository:
    """Append-only storage for students, exercises and feedback, held in process memory.

    Kept as the CI, test and local-development implementation. `FirestoreMemoryRepository`
    subclasses it and overrides only the storage primitives, so `derive_profile` below — the
    logic that actually adapts to a student — exists exactly once.
    """

    backend = "memory"

    def __init__(self):
        self._students: dict[str, StudentProfile] = {}
        self._exercises: dict[str, list[ExerciseRecord]] = {}  # student_id -> list of records
        self._digests: dict[str, list] = {}

        # Initialize default demo profiles for multi-student support from day 1
        self.register_student(
            StudentProfile(
                student_id="young-tester-01",
                name="Young Tester (Age 9)",
                level="beginner",
                tone_preference="encouraging",
                recurring_issues=[],
            )
        )
        self.register_student(
            StudentProfile(
                student_id="sofia-01",
                name="Sofia",
                level="advanced",
                tone_preference="technical",
                recurring_issues=[],
            )
        )

    def register_student(self, student: StudentProfile) -> StudentProfile:
        """Register or update initial student profile."""
        self._students[student.student_id] = student
        if student.student_id not in self._exercises:
            self._exercises[student.student_id] = []
        return student

    def get_student(self, student_id: str) -> StudentProfile | None:
        """Retrieve student profile by ID."""
        return self._students.get(student_id)

    def list_students(self) -> list[StudentProfile]:
        """List all registered student profiles."""
        return list(self._students.values())

    def save_exercise(self, exercise: ExerciseRecord) -> ExerciseRecord:
        """Append an immutable exercise record to student's history (ADR-005)."""
        if exercise.student_id not in self._exercises:
            self._exercises[exercise.student_id] = []
        self._exercises[exercise.student_id].append(exercise)
        return exercise

    def record_feedback(
        self,
        exercise_id: str,
        student_id: str,
        helpful: bool,
        note: str | None = None,
    ) -> FeedbackEvent | None:
        """Append an immutable feedback event to an exercise (CAPTURE step)."""
        student_exs = self._exercises.get(student_id, [])
        for ex in student_exs:
            if ex.exercise_id == exercise_id:
                event = FeedbackEvent(
                    feedback_id=f"fb-{uuid.uuid4().hex[:8]}",
                    exercise_id=exercise_id,
                    student_id=student_id,
                    helpful=helpful,
                    note=note,
                    created_at=get_current_utc_iso(),
                )
                ex.feedback_events.append(event)
                return event
        return None

    def get_student_exercises(self, student_id: str) -> list[ExerciseRecord]:
        """Retrieve all chronological exercise records for a student."""
        return self._exercises.get(student_id, [])

    def save_digest(self, digest) -> None:
        """Append a weekly digest. Routed through the repository so digests follow the same
        backend as everything else — they used to live in a second module-level dict, which is
        how one half of the state ends up persisted and the other half does not."""
        self._digests.setdefault(digest.student_id, []).append(digest)

    def get_digests(self, student_id: str) -> list:
        """Chronological weekly digests for a student."""
        return self._digests.get(student_id, [])

    def derive_profile(self, student_id: str) -> DerivedProfile:
        """Derive student's effective learning profile dynamically from event stream (ADAPT step)."""
        student = self.get_student(student_id)
        if not student:
            raise ValueError(f"Student '{student_id}' not found.")

        exercises = self.get_student_exercises(student_id)

        # 1. Progress curve
        progress_curve: list[ProgressPoint] = []
        all_errors: list[float] = []

        # Conic exercises only. Axonometric ones are stored, critiqued and counted towards tone
        # adaptation, but they do not join this curve: convergence error and axis deviation are
        # both measured in degrees and are not the same quantity, so a single line through both
        # would read as progress or regression that nobody actually made.
        for ex in exercises:
            if ex.geometry_analysis is None:
                continue
            err = ex.geometry_analysis.avg_convergence_error_deg
            all_errors.append(err)
            progress_curve.append(
                ProgressPoint(
                    timestamp=ex.created_at,
                    exercise_id=ex.exercise_id,
                    avg_convergence_error_deg=err,
                    k_points=ex.geometry_analysis.k_requested,
                )
            )

        overall_avg = float(np.mean(all_errors)) if all_errors else 0.0

        # 2. Analyze feedback events to derive tone preference
        all_feedbacks: list[FeedbackEvent] = []
        for ex in exercises:
            all_feedbacks.extend(ex.feedback_events)

        if all_feedbacks:
            helpful_count = sum(1 for fb in all_feedbacks if fb.helpful)
            helpful_ratio = helpful_count / len(all_feedbacks)

            recent_feedbacks = all_feedbacks[-3:]
            recent_unhelpful = sum(1 for fb in recent_feedbacks if not fb.helpful)

            # If recent feedbacks indicate frustration/unhelpful critiques, adapt tone to be warmer & direct
            if recent_unhelpful >= 2:
                derived_tone = "encouraging"
            elif helpful_ratio >= 0.8 and student.level == "advanced":
                derived_tone = "technical"
            else:
                derived_tone = student.tone_preference or "balanced"
        else:
            helpful_ratio = 1.0
            derived_tone = student.tone_preference or ("encouraging" if student.level == "beginner" else "technical")

        # 3. Detect recurring technical issues from geometry history
        recurring_issues: list[str] = []
        f1_errors = []
        f2_errors = []

        for ex in exercises:
            if ex.geometry_analysis is None:
                continue
            for vp in ex.geometry_analysis.vanishing_points:
                if vp.label == "F1" and vp.avg_error_deg > 3.5:
                    f1_errors.append(vp.avg_error_deg)
                elif vp.label == "F2" and vp.avg_error_deg > 3.5:
                    f2_errors.append(vp.avg_error_deg)
                elif vp.label == "VP" and vp.avg_error_deg > 3.0:
                    f1_errors.append(vp.avg_error_deg)

        if len(f1_errors) >= 2:
            recurring_issues.append("Left Vanishing Point (F1) angle divergence")
        if len(f2_errors) >= 2:
            recurring_issues.append("Right Vanishing Point (F2) depth consistency")
        if not recurring_issues and overall_avg > 4.0:
            recurring_issues.append("General horizon alignment and construction pressure")

        # 4. Determine current focus and guide next exercise
        if recurring_issues:
            current_focus = recurring_issues[0]
        elif student.level == "beginner":
            current_focus = "1-Point frontal cube alignment"
        else:
            current_focus = "2-Point oblique volumetric proportions"

        # 5. Formulate next exercise recommendation (GUIDE)
        if student.level == "beginner":
            next_ex = NextExerciseRecommendation(
                title="1-Point Perspective: 3 Aligned Cubes",
                description="Draw three boxes (one left, one center, one right) all pointing to the same dot on the horizon.",
                target_metric="1-point VP consistency",
                difficulty="beginner",
            )
        elif "F1" in current_focus:
            next_ex = NextExerciseRecommendation(
                title="Targeted F1 Convergence Drill",
                description="Draw an elongated rectangular prism where the longer receding side angles strictly to F1.",
                target_metric="F1 left VP convergence",
                difficulty="advanced",
            )
        else:
            next_ex = NextExerciseRecommendation(
                title="2-Point Architectural Complex",
                description="Construct two interlocking geometric volumes ensuring all horizontal edges converge to F1/F2.",
                target_metric="2-point oblique perspective",
                difficulty="advanced",
            )

        return DerivedProfile(
            student=student,
            total_exercises=len(exercises),
            overall_avg_error_deg=round(overall_avg, 2),
            progress_curve=progress_curve,
            recurring_issues=recurring_issues,
            derived_tone_preference=derived_tone,
            recent_helpful_ratio=round(helpful_ratio, 2),
            current_practice_focus=current_focus,
            recommended_next_exercise=next_ex,
        )


# Global singleton repository instance
def _build_memory_repo() -> MemoryRepository:
    """Pick the backend, and never downgrade quietly."""
    if settings.memory_backend != "firestore":
        logger.info("Student memory backend: in-process dicts (MEMORY_BACKEND=%s).", settings.memory_backend)
        return MemoryRepository()

    try:
        from src.tools.firestore_repo import FirestoreMemoryRepository

        repo = FirestoreMemoryRepository()
        logger.info("Student memory backend: Firestore (%s).", settings.firestore_db)
        return repo
    except Exception as exc:  # noqa: BLE001 - reported, not swallowed
        # Falling back keeps the service answering, which matters more than failing pure. But it
        # is stated: the previous design lost every student's history on each cold start and
        # nothing anywhere said so.
        logger.error(
            "Firestore memory is configured but unavailable (%s: %s). Falling back to process "
            "memory — student history will NOT survive a cold start.",
            type(exc).__name__,
            exc,
        )
        return MemoryRepository()


memory_repo = _build_memory_repo()
