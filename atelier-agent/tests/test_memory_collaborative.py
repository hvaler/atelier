"""Tests for append-only memory, multi-student profiles, and the 4 collaborative verbs (EV-A04 & ADR-005)."""

import uuid

from fastapi.testclient import TestClient

from src.main import app
from src.models.critique import (
    CritiqueOutput,
    NextExerciseRecommendation,
    PedagogicalSummary,
    StudentProfile,
)
from src.models.geometry import GeometryAnalysisResult, Point2D, VanishingPoint
from src.models.memory import ExerciseRecord
from src.tools.collaborative import (
    ask_clarification,
)
from src.tools.memory import MemoryRepository

client = TestClient(app)


def make_dummy_critique(name: str, level: str) -> CritiqueOutput:
    """Helper to create dummy critique output for tests."""
    return CritiqueOutput(
        student_name=name,
        level=level,
        headline="Practice Review",
        measured_findings=[],
        qualitative_observations=[],
        pedagogical_summary=PedagogicalSummary(
            strengths=["Good box symmetry"],
            focus_area="F1 convergence",
            encouragement="Well done!",
        ),
        next_exercise=NextExerciseRecommendation(
            title="Drill",
            description="Do 3 boxes",
            target_metric="F1",
            difficulty=level,
        ),
        validated=True,
    )


def make_dummy_geometry(f1_err: float = 2.0, f2_err: float = 2.0) -> GeometryAnalysisResult:
    """Helper to create dummy geometry result with specified VP errors."""
    return GeometryAnalysisResult(
        k_requested=2,
        k_detected=2,
        vanishing_points=[
            VanishingPoint(index=0, label="F1", point=Point2D(x=100.0, y=250.0), supporting_lines=4, avg_error_deg=f1_err),
            VanishingPoint(index=1, label="F2", point=Point2D(x=800.0, y=250.0), supporting_lines=4, avg_error_deg=f2_err),
        ],
        avg_convergence_error_deg=round((f1_err + f2_err) / 2.0, 2),
        max_convergence_error_deg=max(f1_err, f2_err),
        line_count=8,
        confidence=0.85,
        confidence_low=False,
        image_width=800,
        image_height=600,
    )


def test_multi_student_initialization():
    """
    Two profiles exist from the start, and they are difficulty levels rather than people.

    The distinction is the point: a level decides the register of the rubric and the tone of the
    critique, and there is nobody in it to greet, so nothing downstream may interpolate a name.
    """
    repo = MemoryRepository()
    students = repo.list_students()

    assert len(students) >= 2
    # The "name" is the level word, because the profile is a level. Asserting on the pair rather
    # than on a person is the point of the change.
    names = {s.name for s in students}
    assert {"basic", "advanced"} <= names

    basic = repo.get_student("level-basic")
    assert basic.level == "beginner"

    advanced = repo.get_student("level-advanced")
    assert advanced.level == "advanced"


def test_verb1_ask_clarification():
    """Verb 1: ASK returns tailored questions based on student level."""
    ask_basic = ask_clarification("level-basic")
    assert len(ask_basic.intent_question) > 5
    assert "box" in ask_basic.intent_question.lower() or "3d" in ask_basic.intent_question.lower()
    assert len(ask_basic.quick_intent_suggestions) >= 2

    ask_advanced = ask_clarification("level-advanced")
    # No name is interpolated any more; what must hold is that the two levels ask
    # different questions, in the register of their level.
    assert ask_advanced.intent_question != ask_basic.intent_question
    # The advanced question asks about a construction rather than a box: the register is what
    # distinguishes the two levels now that neither carries a name.
    assert "construction" in ask_advanced.intent_question.lower() or "exercise" in ask_advanced.intent_question.lower()


def test_profile_adaptation_over_event_stream():
    """Verb 4: ADAPT - Verify that N events properly derive progress curve, recurring issues, and tone shift."""
    repo = MemoryRepository()
    test_id = f"student-adapt-{uuid.uuid4().hex[:6]}"
    repo.register_student(
        StudentProfile(
            student_id=test_id,
            name="Alex",
            level="advanced",
            tone_preference="technical",
        )
    )

    # Add 3 sequential exercises with high F1 error
    for i in range(3):
        ex_id = f"ex-{i+1}"
        geom = make_dummy_geometry(f1_err=6.5, f2_err=1.2)
        critique = make_dummy_critique("Alex", "advanced")
        ex = ExerciseRecord(
            exercise_id=ex_id,
            student_id=test_id,
            geometry_analysis=geom,
            critique=critique,
        )
        repo.save_exercise(ex)

        # Record feedback: first was unhelpful, second was unhelpful (tone too harsh/complex)
        if i < 2:
            repo.record_feedback(
                exercise_id=ex_id,
                student_id=test_id,
                helpful=False,
                note="Critique was too rigid and complex to follow",
            )
        else:
            repo.record_feedback(
                exercise_id=ex_id,
                student_id=test_id,
                helpful=True,
                note="Better!",
            )

    # Derive profile from event stream
    derived = repo.derive_profile(test_id)

    assert derived.total_exercises == 3
    assert len(derived.progress_curve) == 3
    # Recurring issue should detect F1 error pattern
    assert any("F1" in issue or "Left" in issue for issue in derived.recurring_issues)
    # Because 2 recent feedbacks were unhelpful, tone adapted to encouraging
    assert derived.derived_tone_preference == "encouraging"
    # Recommended next exercise focuses on F1
    assert "F1" in derived.recommended_next_exercise.target_metric or "F1" in derived.recommended_next_exercise.title


def test_verb2_guide_next_exercise():
    """Verb 2: GUIDE recommends appropriate next exercise."""
    repo = MemoryRepository()
    rec_tester = repo.derive_profile("level-basic").recommended_next_exercise
    assert rec_tester.difficulty == "beginner"

    rec_sofia = repo.derive_profile("level-advanced").recommended_next_exercise
    assert rec_sofia.difficulty == "advanced"


def test_verb3_capture_feedback():
    """Verb 3: CAPTURE records feedback event in memory."""
    repo = MemoryRepository()
    student_id = "level-advanced"
    ex_id = "ex-test-capture"

    ex = ExerciseRecord(
        exercise_id=ex_id,
        student_id=student_id,
        geometry_analysis=make_dummy_geometry(),
        critique=make_dummy_critique("advanced", "advanced"),
    )
    repo.save_exercise(ex)

    fb = repo.record_feedback(
        exercise_id=ex_id,
        student_id=student_id,
        helpful=True,
        note="Very clear explanation of the horizon line",
    )

    assert fb is not None
    assert fb.helpful is True
    assert "horizon" in fb.note


def test_api_collaborative_endpoints():
    """Test full HTTP REST API flow for the 4 collaborative verbs."""
    # 1. List students
    resp_list = client.get("/api/students")
    assert resp_list.status_code == 200
    students_data = resp_list.json()
    assert len(students_data) >= 2

    # 2. ASK questions for the basic level. The response carries no personal name to assert on;
    #    what must hold is that it asks something.
    resp_ask = client.get("/api/students/level-basic/ask")
    assert resp_ask.status_code == 200
    assert resp_ask.json()["intent_question"].endswith("?")

    # 3. Post new exercise
    ex_id = f"ex-api-{uuid.uuid4().hex[:6]}"
    geom = make_dummy_geometry(f1_err=2.5, f2_err=2.8)
    critique = make_dummy_critique("basic", "beginner")

    resp_save_ex = client.post(
        "/api/exercises",
        json={
            "exercise_id": ex_id,
            "student_id": "level-basic",
            "student_intent": "Drawing a box on the floor",
            "geometry_analysis": geom.model_dump(),
            "critique": critique.model_dump(),
        },
    )
    assert resp_save_ex.status_code == 201

    # 4. CAPTURE feedback
    resp_fb = client.post(
        f"/api/exercises/{ex_id}/feedback",
        json={
            "student_id": "level-basic",
            "helpful": True,
            "note": "Super helpful tips!",
        },
    )
    assert resp_fb.status_code == 201
    assert resp_fb.json()["helpful"] is True

    # 5. ADAPT / Get derived profile
    resp_prof = client.get("/api/students/level-basic/profile")
    assert resp_prof.status_code == 200
    prof_data = resp_prof.json()
    assert prof_data["total_exercises"] >= 1
    assert len(prof_data["progress_curve"]) >= 1

    # 6. GUIDE next exercise
    resp_guide = client.get("/api/students/level-basic/guide")
    assert resp_guide.status_code == 200
    assert resp_guide.json()["difficulty"] == "beginner"
