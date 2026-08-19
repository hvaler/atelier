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
    ExerciseSummary,
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
                student_id="level-basic",
                name="basic",
                level="beginner",
                tone_preference="encouraging",
                recurring_issues=[],
            )
        )
        self.register_student(
            StudentProfile(
                student_id="level-advanced",
                name="advanced",
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

        overall_avg = float(np.mean(all_errors)) if all_errors else None

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
        if not recurring_issues and overall_avg is not None and overall_avg > 4.0:
            recurring_issues.append("General horizon alignment and construction pressure")

        # 4. Determine current focus and guide next exercise
        if recurring_issues:
            current_focus = recurring_issues[0]
        elif student.level == "beginner":
            current_focus = "1-Point frontal cube alignment"
        else:
            current_focus = "2-Point oblique volumetric proportions"

        # 5. Formulate the next exercise (GUIDE), from the documented ladder.
        next_ex = next_exercise_on_ladder(student.level, current_focus)

        return DerivedProfile(
            student=student,
            total_exercises=len(exercises),
            overall_avg_error_deg=round(overall_avg, 2) if overall_avg is not None else None,
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


def summarise_exercise(record: ExerciseRecord) -> ExerciseSummary:
    """
    Reduce a stored exercise to the one line a history list shows.

    Each system contributes a different headline figure, because each measures a different thing.
    Showing "0.8" for all three under one column header would invite comparing an axis deviation
    with a convergence error, and they are not the same quantity.
    """
    projection = "unknown"
    metric_name = ""
    metric_value: float | None = None
    metric_unit = "degrees"

    if record.geometry_analysis is not None:
        projection = "conic"
        metric_name = "average convergence error"
        metric_value = record.geometry_analysis.avg_convergence_error_deg
    elif record.axonometric_analysis is not None:
        projection = "axonometric"
        metric_name = "average axis error"
        metric_value = record.axonometric_analysis.avg_axis_error_deg
    elif record.dihedral_analysis is not None:
        projection = "orthographic"
        d = record.dihedral_analysis
        # The systematic offset is the more useful of the two when it exists; when it does not,
        # the residual is. Null stays null: an average over no matched pair is not zero.
        if d.systematic_offset_px is not None:
            metric_name = "systematic offset"
            metric_value = d.systematic_offset_px
            metric_unit = "pixels"
        else:
            metric_name = "correspondence error"
            metric_value = d.avg_correspondence_error_px
            metric_unit = "pixels"

    return ExerciseSummary(
        exercise_id=record.exercise_id,
        created_at=record.created_at,
        projection=projection,
        headline=record.critique.headline if record.critique else "",
        metric_name=metric_name,
        metric_value=metric_value,
        metric_unit=metric_unit,
        source=record.critique.source if record.critique else "fallback",
        student_intent=record.student_intent,
        feedback_count=len(record.feedback_events),
    )


# ---------------------------------------------------------------------------------------------
# The exercise ladder
# ---------------------------------------------------------------------------------------------
#
# Not a list invented to fill a field in a JSON schema. This is the order the published curricula
# put these constructions in, recorded and cited in `docs/PEDAGOGY.md` §5:
#
#     perspectiva cónica frontal  (one-point conical)
#             ↓
#     perspectiva cónica oblicua  (two-point oblique, F1 and F2 on the horizon)
#             ↓
#     puntos métricos y de distancia  (true dimensions carried into the perspective)
#             ↓
#     abatimientos y verdaderas magnitudes  (rabatment)
#             ↓
#     sombras  (cast shadows)
#             ↓
#     escenas complejas
#
# Sources, both public and quoted in PEDAGOGY.md: *Geometría Descriptiva* (2301113), E.T.S. de
# Ingeniería de Edificación, Universidad de Granada; *Geometría Descriptiva* (101002), E.
# Politécnica Superior de Zamora, Universidad de Salamanca.
#
# **The ladder stops where the engine does.** Rabatment, measuring points and cast shadows are
# documented rungs Atelier cannot yet assess, so nothing here prescribes them: recommending an
# exercise the system will then be unable to measure is the gap this project exists to close, not
# to reopen. They are recorded in the README gaps table instead.

#: Where the citable ladder comes from, carried on every recommendation so the agent can say so.
LADDER_SOURCE = "documented progression, docs/PEDAGOGY.md §5"


def next_exercise_on_ladder(level: str, current_focus: str) -> NextExerciseRecommendation:
    """
    The next rung, chosen by level and by what the measurements keep flagging.

    Deliberately deterministic: a student who has the same recurring issue twice should get the
    same targeted drill twice, not a different creative suggestion each time.
    """
    if level == "beginner":
        return NextExerciseRecommendation(
            title="Perspectiva cónica frontal: three aligned prisms",
            description=(
                "Draw the horizon line (LH) first and mark one vanishing point on it. Construct "
                "three rectangular prisms — left, centre, right — with their front faces parallel "
                "to the picture plane, so every receding edge runs to that single point. Keep the "
                "construction traces lighter than the definitive edges. "
                f"First rung of the {LADDER_SOURCE}."
            ),
            target_metric="convergence to a single vanishing point",
            difficulty="beginner",
        )

    if "F1" in current_focus:
        return NextExerciseRecommendation(
            title="Targeted F1 convergence drill",
            description=(
                "In perspectiva cónica oblicua, construct an elongated prism whose longer receding "
                "family runs strictly to F1, with F1 and F2 both marked on the horizon line before "
                "you start. The measurements keep flagging this family, so this drill isolates it. "
                f"Second rung of the {LADDER_SOURCE}."
            ),
            target_metric="F1 convergence error",
            difficulty="advanced",
        )

    return NextExerciseRecommendation(
        title="Perspectiva cónica oblicua: two interlocking volumes",
        description=(
            "Set the horizon line and both vanishing points, then construct two interlocking "
            "volumes so that every horizontal family resolves to F1 or F2 and the shared edges "
            "stay consistent between them. Keep verticals true. "
            f"Second rung of the {LADDER_SOURCE}; the rungs above it — measuring points, "
            "rabatment and cast shadows — are documented but not yet measurable here."
        ),
        target_metric="two-point oblique convergence",
        difficulty="advanced",
    )
