"""Append-only memory repository and dynamic profile derivation engine (ADR-003, ADR-005, PAT-004)."""

import uuid

import numpy as np

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


class MemoryRepository:
    """In-memory & Firestore-compatible append-only storage for students, exercises, and feedback."""

    def __init__(self):
        self._students: dict[str, StudentProfile] = {}
        self._exercises: dict[str, list[ExerciseRecord]] = {}  # student_id -> list of records

        # Initialize default demo profiles for multi-student support from day 1
        self.register_student(
            StudentProfile(
                student_id="clara-01",
                name="Clara",
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

    def derive_profile(self, student_id: str) -> DerivedProfile:
        """Derive student's effective learning profile dynamically from event stream (ADAPT step)."""
        student = self.get_student(student_id)
        if not student:
            raise ValueError(f"Student '{student_id}' not found.")

        exercises = self.get_student_exercises(student_id)

        # 1. Progress curve
        progress_curve: list[ProgressPoint] = []
        all_errors: list[float] = []

        for ex in exercises:
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
memory_repo = MemoryRepository()
