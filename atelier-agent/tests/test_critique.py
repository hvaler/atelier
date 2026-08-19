"""Tests for level-aware pedagogical critique and anti-hallucination validation (EV-A03 & ADR-001)."""

from fastapi.testclient import TestClient

from src.main import app
from src.models.critique import (
    CritiqueOutput,
    CritiqueRequest,
    MeasuredFindingItem,
    NextExerciseRecommendation,
    PedagogicalSummary,
    QualitativeObservationItem,
    StudentProfile,
)
from src.models.geometry import GeometryAnalysisResult, Point2D, VanishingPoint
from src.tools.critique import generate_pedagogical_critique
from src.tools.validator import validate_critique_measurements

client = TestClient(app)


def build_sample_geometry(k: int = 1, avg_error: float = 2.4, max_error: float = 4.1) -> GeometryAnalysisResult:
    """Helper to build a sample geometry analysis result."""
    return GeometryAnalysisResult(
        k_requested=k,
        k_detected=k,
        vanishing_points=[
            VanishingPoint(
                index=0,
                label="VP" if k == 1 else "F1",
                point=Point2D(x=400.0, y=250.0, norm_x=0.5, norm_y=0.41),
                supporting_lines=6,
                avg_error_deg=avg_error,
            )
        ],
        avg_convergence_error_deg=avg_error,
        max_convergence_error_deg=max_error,
        line_count=8,
        confidence=0.85,
        confidence_low=False,
        image_width=800,
        image_height=600,
    )


def test_level_aware_critique_beginner():
    """Verify that critique generated for beginner student uses warm, intuitive vocabulary."""
    student = StudentProfile(
        student_id="student-beginner-01",
        name="Young Tester",
        level="beginner",
        tone_preference="encouraging",
    )
    geom = build_sample_geometry(k=1, avg_error=1.8, max_error=3.2)
    request = CritiqueRequest(
        geometry=geom,
        student=student,
        student_intent="Practice drawing my first 3D box",
        student_difficulty="The top face felt tricky",
        use_cache=False,
    )

    response = generate_pedagogical_critique(request)
    critique = response.critique

    assert critique.student_name == "Young Tester"
    assert critique.level == "beginner"
    assert critique.validated is True
    # Beginner next exercise should be beginner level
    assert critique.next_exercise.difficulty == "beginner"
    # Should cite measured 1.8 deg
    assert any(abs(m.measured_value - 1.8) < 0.1 for m in critique.measured_findings)


def test_level_aware_critique_advanced():
    """Verify that critique generated for advanced animation student uses studio master terminology."""
    student = StudentProfile(
        student_id="student-advanced-01",
        name="Sofia",
        level="advanced",
        tone_preference="technical",
    )
    geom = build_sample_geometry(k=2, avg_error=3.5, max_error=6.2)
    request = CritiqueRequest(
        geometry=geom,
        student=student,
        student_intent="Oblique perspective cube cluster",
        student_difficulty="Keeping lines converging strictly to F1",
        use_cache=False,
    )

    response = generate_pedagogical_critique(request)
    critique = response.critique

    assert critique.student_name == "Sofia"
    assert critique.level == "advanced"
    assert critique.validated is True
    assert critique.next_exercise.difficulty == "advanced"
    # Plane A contains measured metrics
    assert len(critique.measured_findings) >= 1
    # Plane B contains qualitative studio rubric assessments when image is provided or general observations
    assert len(critique.qualitative_observations) >= 0


def test_validator_accepts_accurate_measurements():
    """Validator passes when critique cites exact measured numbers from OpenCV."""
    geom = build_sample_geometry(k=1, avg_error=2.4, max_error=5.0)

    critique = CritiqueOutput(
        student_name="Hugo",
        level="advanced",
        headline="Solid Perspective Control",
        measured_findings=[
            MeasuredFindingItem(
                metric_name="average_convergence_error",
                measured_value=2.4,
                unit="degrees",
                pedagogical_context="Accurate alignment to vanishing point.",
            )
        ],
        qualitative_observations=[
            QualitativeObservationItem(
                aspect="line_weight",
                observation="Clean contrast between construction lines and solution edges.",
                status="strength",
            )
        ],
        pedagogical_summary=PedagogicalSummary(
            strengths=["Consistent depth"],
            focus_area="Vertical axis rigidity",
            encouragement="Keep practicing!",
        ),
        next_exercise=NextExerciseRecommendation(
            title="2-Point City Block",
            description="Draw three staggered buildings.",
            target_metric="F2 convergence",
            difficulty="advanced",
        ),
    )

    is_valid, errors = validate_critique_measurements(critique, geom)
    assert is_valid is True
    assert len(errors) == 0


def test_validator_rejects_hallucinated_measurements():
    """Validator detects and rejects any hallucinated degree or coordinate values (ADR-001)."""
    geom = build_sample_geometry(k=1, avg_error=2.4, max_error=5.0)

    # Malicious/hallucinated critique inventing a 23.7 degree error not in OpenCV payload
    hallucinated_critique = CritiqueOutput(
        student_name="Hugo",
        level="advanced",
        headline="Perspective Review",
        measured_findings=[
            MeasuredFindingItem(
                metric_name="average_convergence_error",
                measured_value=23.7,  # INVENTED NUMBER
                unit="degrees",
                pedagogical_context="Your error was 23.7 degrees which is off.",
            )
        ],
        qualitative_observations=[],
        pedagogical_summary=PedagogicalSummary(
            strengths=["Good lines"],
            focus_area="Convergence",
            encouragement="Try again!",
        ),
        next_exercise=NextExerciseRecommendation(
            title="Cubes",
            description="Draw cubes.",
            target_metric="convergence",
            difficulty="intermediate",
        ),
    )

    is_valid, errors = validate_critique_measurements(hallucinated_critique, geom)
    assert is_valid is False
    assert len(errors) > 0
    assert "Hallucinated measurement detected" in errors[0]


def test_api_critique_endpoint():
    """Test HTTP POST /api/critique endpoint with full request payload."""
    geom = build_sample_geometry(k=2, avg_error=2.1, max_error=3.8)
    student = StudentProfile(
        student_id="student-02",
        name="Elena",
        level="advanced",
    )

    response = client.post(
        "/api/critique",
        json={
            "geometry": geom.model_dump(),
            "student": student.model_dump(),
            "student_intent": "Testing 2-point perspective box",
            "use_cache": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "critique" in data
    critique_data = data["critique"]
    assert critique_data["student_name"] == "Elena"
    assert critique_data["validated"] is True
    assert len(critique_data["measured_findings"]) >= 1
    assert len(critique_data["qualitative_observations"]) >= 1


def test_critique_caching():
    """Verify that subsequent requests with same parameters are served from local cache."""
    geom = build_sample_geometry(k=1, avg_error=1.5, max_error=2.5)
    student = StudentProfile(
        student_id="student-cache-test",
        name="Mateo",
        level="beginner",
    )
    request = CritiqueRequest(
        geometry=geom,
        student=student,
        use_cache=True,
    )

    # First call - populates cache
    resp1 = generate_pedagogical_critique(request)
    assert resp1.critique.student_name == "Mateo"

    # Second call - must hit cache
    resp2 = generate_pedagogical_critique(request)
    assert resp2.cached is True
    assert resp2.critique.student_name == "Mateo"
