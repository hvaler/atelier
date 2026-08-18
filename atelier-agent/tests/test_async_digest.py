"""Tests for asynchronous GCS/Eventarc ingestion and Cloud Scheduler weekly digests (EV-A05 & ADR-004)."""

import uuid

from fastapi.testclient import TestClient

from src.main import app
from src.models.critique import (
    CritiqueOutput,
    NextExerciseRecommendation,
    PedagogicalSummary,
    StudentProfile,
)
from src.models.digest import GcsEventPayload
from src.models.geometry import GeometryAnalysisResult, Point2D, VanishingPoint
from src.models.memory import ExerciseRecord
from src.tools.async_ingest import process_gcs_upload_event
from src.tools.digest import generate_weekly_digest
from src.tools.memory import memory_repo

client = TestClient(app)


def make_dummy_exercise(student_id: str, avg_error: float) -> ExerciseRecord:
    """Helper to create dummy exercise record with specific convergence error."""
    geom = GeometryAnalysisResult(
        k_requested=1,
        k_detected=1,
        vanishing_points=[
            VanishingPoint(index=0, label="VP", point=Point2D(x=400.0, y=250.0), supporting_lines=4, avg_error_deg=avg_error)
        ],
        avg_convergence_error_deg=avg_error,
        max_convergence_error_deg=avg_error + 1.5,
        line_count=6,
        confidence=0.85,
        confidence_low=False,
        image_width=800,
        image_height=600,
    )
    critique = CritiqueOutput(
        student_name="Student",
        level="beginner",
        headline="Practice Review",
        measured_findings=[],
        qualitative_observations=[],
        pedagogical_summary=PedagogicalSummary(
            strengths=["Good box"],
            focus_area="Horizon",
            encouragement="Nice!",
        ),
        next_exercise=NextExerciseRecommendation(
            title="Drill",
            description="Practice 3 boxes",
            target_metric="1-point VP",
            difficulty="beginner",
        ),
        validated=True,
    )
    return ExerciseRecord(
        exercise_id=f"ex-digest-{uuid.uuid4().hex[:6]}",
        student_id=student_id,
        geometry_analysis=geom,
        critique=critique,
    )


def test_gcs_upload_event_processing():
    """Eventarc GCS object finalize trigger automatically runs geometry, critique, and saves to memory."""
    payload = GcsEventPayload(
        bucket="atelier-inbox",
        name="young-tester-01/drawing_box_01.png",
    )

    response = process_gcs_upload_event(payload)

    assert response.status_code == "processed" if hasattr(response, "status_code") else response.status == "processed"
    assert response.student_id == "young-tester-01"
    assert "Tester" in response.student_name or "Student" in response.student_name
    assert response.k_detected >= 1
    assert len(response.critique_headline) > 5

    # Verify that exercise record was persisted in memory_repo
    exercises = memory_repo.get_student_exercises("young-tester-01")
    assert len(exercises) >= 1
    latest = exercises[-1]
    assert latest.student_id == "young-tester-01"
    assert latest.source == "folder"


def test_weekly_digest_generation_with_improvement():
    """Weekly digest computes progress error reduction and prescribes 3-day practice plan."""
    student_id = f"student-digest-{uuid.uuid4().hex[:6]}"
    memory_repo.register_student(
        StudentProfile(
            student_id=student_id,
            name="Lucas",
            level="beginner",
        )
    )

    # Add 4 exercises showing progressive improvement (5.0° -> 4.0° -> 2.5° -> 1.5°)
    errors = [5.0, 4.0, 2.5, 1.5]
    for err in errors:
        ex = make_dummy_exercise(student_id=student_id, avg_error=err)
        memory_repo.save_exercise(ex)

    digest = generate_weekly_digest(student_id=student_id, week_id="2026-W34")

    assert digest.student_id == student_id
    assert digest.student_name == "Lucas"
    assert digest.total_drawings == 4
    # Error reduction should be positive (initial avg 4.5° - recent avg 2.0° = 2.5°)
    assert digest.error_reduction_deg > 0.0
    assert "decreased" in digest.weekly_summary or "consistency" in digest.weekly_summary
    # 3 practice days
    assert len(digest.next_week_practice_plan) == 3
    days = [p.day for p in digest.next_week_practice_plan]
    assert days == ["Monday", "Wednesday", "Friday"]


def test_weekly_digest_beginner_vs_advanced_plans():
    """Beginner students get 1-point foundation drills, advanced get complex 2-point architectural drills."""
    # Beginner: young-tester-01
    digest_beginner = generate_weekly_digest("young-tester-01")
    assert any("cube" in p.title.lower() or "box" in p.title.lower() for p in digest_beginner.next_week_practice_plan)

    # Advanced: Sofia
    digest_sofia = generate_weekly_digest("sofia-01")
    assert any("2-point" in p.title.lower() or "prism" in p.title.lower() or "architectural" in p.title.lower() for p in digest_sofia.next_week_practice_plan)


def test_api_gcs_upload_endpoint():
    """Test Eventarc HTTP POST webhook endpoint."""
    response = client.post(
        "/api/events/gcs-upload",
        json={
            "bucket": "atelier-inbox-test",
            "name": "sofia-01/oblique_perspective_02.png",
            "contentType": "image/png",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["student_id"] == "sofia-01"
    assert "critique_headline" in data


def test_api_weekly_digest_endpoint():
    """Test Cloud Scheduler HTTP POST weekly digest endpoint."""
    response = client.post(
        "/api/digest/weekly",
        json={
            "student_id": "sofia-01",
            "week_id": "2026-W34",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "sofia-01"
    assert data["week_id"] == "2026-W34"
    assert len(data["next_week_practice_plan"]) == 3
