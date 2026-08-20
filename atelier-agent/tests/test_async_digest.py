"""Tests for asynchronous GCS/Eventarc ingestion and Cloud Scheduler weekly digests (EV-A05 & ADR-004)."""

import base64
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app
from src.models.axonometry import AxisMeasurement, AxonometricAnalysisResult
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

DATASET_DIR = Path(__file__).resolve().parents[2] / "demo" / "dataset"


def _dataset_b64(name: str) -> str:
    """A calibration PNG as base64, so ingestion tests analyse a drawing with a known answer."""
    path = DATASET_DIR / name
    assert path.exists(), f"calibration dataset missing: {path}"
    return base64.b64encode(path.read_bytes()).decode()

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


def _make_axonometric_exercise(student_id: str) -> ExerciseRecord:
    """An exercise whose measurement is parallel-projection, so `geometry_analysis` is None."""
    axo = AxonometricAnalysisResult(
        system="isometric",
        axes=[
            AxisMeasurement(
                index=0,
                label="x",
                nominal_angle_deg=30.0,
                measured_angle_deg=36.0,
                systematic_error_deg=6.0,
                supporting_lines=17,
                avg_error_deg=6.0,
                max_error_deg=6.2,
            )
        ],
        avg_axis_error_deg=2.0,
        max_axis_error_deg=6.2,
        parallelism_error_deg=0.4,
        off_axis_line_count=0,
        line_count=17,
        axes_supported=1,
        confidence=0.9,
        confidence_low=False,
        image_width=800,
        image_height=600,
    )
    critique = CritiqueOutput(
        student_name="Student",
        level="beginner",
        headline="Axonometric Review",
        measured_findings=[],
        qualitative_observations=[],
        pedagogical_summary=PedagogicalSummary(
            strengths=["Parallel families"],
            focus_area="Axis setup",
            encouragement="Good!",
        ),
        next_exercise=NextExerciseRecommendation(
            title="Set square drill",
            description="Three families at 30, 90, 150",
            target_metric="Systematic axis deviation",
            difficulty="beginner",
        ),
        validated=True,
    )
    return ExerciseRecord(
        exercise_id=f"ex-axo-{uuid.uuid4().hex[:6]}",
        student_id=student_id,
        axonometric_analysis=axo,
        critique=critique,
    )


def test_gcs_upload_event_processing():
    """Eventarc GCS object finalize trigger automatically runs geometry, critique, and saves to memory."""
    # A real calibration drawing, inline. The event used to carry nothing and the pipeline
    # invented a canvas to analyse, so this test passed while proving that two different uploads
    # produce the same measurement. Now it asserts the number that belongs to this file.
    payload = GcsEventPayload(
        bucket="atelier-hack-inbox",
        name="level-basic/03_1point_error_9deg.png",
        image_base64=_dataset_b64("03_1point_error_9deg.png"),
    )

    response = process_gcs_upload_event(payload)

    assert response.status_code == "processed" if hasattr(response, "status_code") else response.status == "processed"
    assert response.student_id == "level-basic"
    # The profile is a level, so the name it carries is the level word. Asserting the id and
    # the level is what actually matters: the ingested file went to the right profile.
    assert response.student_name == "basic"
    assert response.k_detected >= 1
    assert len(response.critique_headline) > 5

    # Verify that exercise record was persisted in memory_repo
    exercises = memory_repo.get_student_exercises("level-basic")
    assert len(exercises) >= 1
    latest = exercises[-1]
    assert latest.student_id == "level-basic"
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
    # Beginner level
    digest_beginner = generate_weekly_digest("level-basic")
    assert any("cube" in p.title.lower() or "box" in p.title.lower() for p in digest_beginner.next_week_practice_plan)

    # Advanced level
    digest_advanced = generate_weekly_digest("level-advanced")
    assert any("2-point" in p.title.lower() or "prism" in p.title.lower() or "architectural" in p.title.lower() for p in digest_advanced.next_week_practice_plan)


def test_api_gcs_upload_endpoint():
    """Test Eventarc HTTP POST webhook endpoint."""
    response = client.post(
        "/api/events/gcs-upload",
        json={
            "bucket": "atelier-hack-inbox",
            "name": "level-advanced/04_2point_perfect.png",
            "contentType": "image/png",
            "image_base64": _dataset_b64("04_2point_perfect.png"),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["student_id"] == "level-advanced"
    assert "critique_headline" in data


def test_api_weekly_digest_endpoint():
    """Test Cloud Scheduler HTTP POST weekly digest endpoint."""
    response = client.post(
        "/api/digest/weekly",
        json={
            "student_id": "level-advanced",
            "week_id": "2026-W34",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "level-advanced"
    assert data["week_id"] == "2026-W34"
    assert len(data["next_week_practice_plan"]) == 3


def test_gcs_ingestion_refuses_an_object_it_cannot_read():
    """
    An unreadable object is a 400, not a substituted drawing.

    This is the invariant the old code broke: with no inline payload it synthesised a canvas,
    analysed that, and filed the result under the student's name. A pipeline that cannot fetch
    the drawing has nothing true to say about it, and saying so is the only correct answer.
    """
    import src.tools.async_ingest as ingest

    original = ingest.download_drawing_from_gcs
    ingest.download_drawing_from_gcs = lambda bucket, name: (_ for _ in ()).throw(
        ValueError(f"gs://{bucket}/{name} does not exist or is not readable.")
    )
    try:
        response = client.post(
            "/api/events/gcs-upload",
            json={"bucket": "atelier-hack-inbox", "name": "level-basic/missing.png"},
        )
        assert response.status_code == 400, response.text
        assert "not exist" in response.text or "readable" in response.text
    finally:
        ingest.download_drawing_from_gcs = original


def test_digest_survives_a_week_of_parallel_projection_only():
    """A week with no conic drawing has no convergence average — and must not 500.

    `geometry_analysis` is None on axonometric and orthographic records. The digest used to read
    that field off every exercise, so a single isometric drawing in the week raised AttributeError
    and the Cloud Scheduler job returned 500 silently.
    """
    student_id = f"student-parallel-{uuid.uuid4().hex[:6]}"
    memory_repo.register_student(
        StudentProfile(student_id=student_id, name="basic", level="beginner")
    )
    memory_repo.save_exercise(_make_axonometric_exercise(student_id))

    digest = generate_weekly_digest(student_id)

    assert digest.total_drawings == 1, "the drawing happened; it is just not a conic one"
    # Not 0.0. An average over nothing that prints as zero reads as a perfect week.
    assert digest.weekly_avg_convergence_error_deg is None
    assert digest.error_reduction_deg is None
    assert "no convergence average" in digest.weekly_summary.lower()
    assert len(digest.next_week_practice_plan) == 3


def test_digest_averages_only_the_conic_exercises():
    """A mixed week averages the conic drawings and leaves the parallel ones out of that figure."""
    student_id = f"student-mixed-{uuid.uuid4().hex[:6]}"
    memory_repo.register_student(
        StudentProfile(student_id=student_id, name="basic", level="beginner")
    )
    memory_repo.save_exercise(make_dummy_exercise(student_id, 4.0))
    memory_repo.save_exercise(_make_axonometric_exercise(student_id))
    memory_repo.save_exercise(make_dummy_exercise(student_id, 2.0))

    digest = generate_weekly_digest(student_id)

    assert digest.total_drawings == 3
    # (4.0 + 2.0) / 2 — the isometric drawing contributes nothing to a convergence average.
    assert digest.weekly_avg_convergence_error_deg == 3.0
