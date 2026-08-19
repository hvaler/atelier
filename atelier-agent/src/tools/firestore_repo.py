"""
Append-only student memory in Google Cloud Firestore (ADR-003 & ADR-005).

`google-cloud-firestore` was declared as a dependency from the first commit and imported
nowhere. Student history lived in module-level dicts on a Cloud Run service that runs with
`--min-instances=0`, so **every scale-to-zero erased it**. The two verbs that make this a
collaborative partner rather than a critique generator — CAPTURE (record what happened) and
ADAPT (change because of it) — were writing to memory that could not outlive a quiet afternoon.

Shape, chosen so that "append-only" is a property of the storage rather than a promise in a
document:

    students/{student_id}                                   profile, the one mutable document
    students/{student_id}/exercises/{exercise_id}           written once, never updated
    students/{student_id}/exercises/{exercise_id}/feedback/{feedback_id}   one document per event

Feedback is a subcollection and not an array field on the exercise, because appending to an
array is a write to the exercise document and this claims not to rewrite history. A new
document per event is the same claim, enforced by the database instead of by convention.

`derive_profile` is inherited from `MemoryRepository` untouched. It reads only `get_student` and
`get_student_exercises`, so pointing those two at Firestore is the whole migration — and the
best logic in the service keeps exactly one implementation.
"""

import logging
import uuid

from src.config import settings
from src.models.memory import (
    ExerciseRecord,
    FeedbackEvent,
    StudentProfile,
    get_current_utc_iso,
)
from src.tools.memory import MemoryRepository

logger = logging.getLogger(__name__)

STUDENTS = "students"
EXERCISES = "exercises"
FEEDBACK = "feedback"
DIGESTS = "digests"


class FirestoreMemoryRepository(MemoryRepository):
    """The same repository surface, backed by Firestore."""

    backend = "firestore"

    def __init__(self) -> None:
        from google.cloud import firestore

        self._db = firestore.Client(project=settings.gcp_project, database=settings.firestore_db)
        # Deliberately not calling super().__init__(): it seeds the demo students into dicts this
        # class does not use. Seeding happens through `ensure_seed_students`, which is idempotent
        # against the database rather than against process memory.
        self.ensure_seed_students()

    # ---- seeding -------------------------------------------------------------------------

    def ensure_seed_students(self) -> None:
        """
        Create the two profiles if they are absent. Never overwrites a real one.

        They are difficulty levels rather than people. A level decides the register of the rubric
        and the tone of the critique; there is nobody in it to name, so the `name` field carries
        the level word and nothing downstream interpolates it into prose.
        """
        for student in (
            StudentProfile(
                student_id="level-basic",
                name="basic",
                level="beginner",
                tone_preference="encouraging",
                recurring_issues=[],
            ),
            StudentProfile(
                student_id="level-advanced",
                name="advanced",
                level="advanced",
                tone_preference="technical",
                recurring_issues=[],
            ),
        ):
            ref = self._db.collection(STUDENTS).document(student.student_id)
            if not ref.get().exists:
                ref.set(student.model_dump())

    # ---- students ------------------------------------------------------------------------

    def register_student(self, student: StudentProfile) -> StudentProfile:
        self._db.collection(STUDENTS).document(student.student_id).set(student.model_dump())
        return student

    def get_student(self, student_id: str) -> StudentProfile | None:
        snapshot = self._db.collection(STUDENTS).document(student_id).get()
        return StudentProfile(**snapshot.to_dict()) if snapshot.exists else None

    def list_students(self) -> list[StudentProfile]:
        return [StudentProfile(**doc.to_dict()) for doc in self._db.collection(STUDENTS).stream()]

    # ---- exercises and feedback ----------------------------------------------------------

    def save_exercise(self, exercise: ExerciseRecord) -> ExerciseRecord:
        (
            self._db.collection(STUDENTS)
            .document(exercise.student_id)
            .collection(EXERCISES)
            .document(exercise.exercise_id)
            .set(exercise.model_dump(exclude={"feedback_events"}))
        )
        return exercise

    def record_feedback(
        self,
        exercise_id: str,
        student_id: str,
        helpful: bool,
        note: str | None = None,
    ) -> FeedbackEvent | None:
        exercise_ref = (
            self._db.collection(STUDENTS)
            .document(student_id)
            .collection(EXERCISES)
            .document(exercise_id)
        )
        if not exercise_ref.get().exists:
            # The caller gets None and the endpoint turns it into a 404. Silently creating the
            # exercise here would let the UI report "Profile Adapted" for an exercise that never
            # happened, which is the failure this whole pass exists to remove.
            return None

        event = FeedbackEvent(
            feedback_id=f"fb-{uuid.uuid4().hex[:8]}",
            exercise_id=exercise_id,
            student_id=student_id,
            helpful=helpful,
            note=note,
            created_at=get_current_utc_iso(),
        )
        exercise_ref.collection(FEEDBACK).document(event.feedback_id).set(event.model_dump())
        return event

    def get_student_exercises(self, student_id: str) -> list[ExerciseRecord]:
        exercises: list[ExerciseRecord] = []
        collection = (
            self._db.collection(STUDENTS).document(student_id).collection(EXERCISES).stream()
        )
        for doc in collection:
            data = doc.to_dict()
            data["feedback_events"] = [
                FeedbackEvent(**fb.to_dict()) for fb in doc.reference.collection(FEEDBACK).stream()
            ]
            exercises.append(ExerciseRecord(**data))

        # Chronological, because `derive_profile` reads "the last three feedback events" and
        # Firestore returns documents in key order, which is not time order.
        exercises.sort(key=lambda ex: ex.created_at or "")
        for exercise in exercises:
            exercise.feedback_events.sort(key=lambda fb: fb.created_at or "")
        return exercises

    # ---- weekly digests ------------------------------------------------------------------

    def save_digest(self, digest) -> None:
        (
            self._db.collection(STUDENTS)
            .document(digest.student_id)
            .collection(DIGESTS)
            .document(digest.week_id)
            .set(digest.model_dump())
        )

    def get_digests(self, student_id: str) -> list:
        from src.models.digest import WeeklyDigest

        docs = self._db.collection(STUDENTS).document(student_id).collection(DIGESTS).stream()
        digests = [WeeklyDigest(**d.to_dict()) for d in docs]
        digests.sort(key=lambda d: d.week_id or "")
        return digests
