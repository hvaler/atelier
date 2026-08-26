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
        name="basic",
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

    assert critique.student_name == "basic"
    assert critique.level == "beginner"
    # Provenance and validation have to agree. A critique the model wrote and the validator
    # passed says vertex/True; anything we substituted for it says fallback/False. Asserting
    # `validated is True` outright used to pass here only because the deterministic template
    # claimed it, which is the one thing this project must never do.
    assert critique.validated is (critique.source == "vertex")
    # Beginner next exercise should be beginner level
    assert critique.next_exercise.difficulty == "beginner"
    # Should cite measured 1.8 deg
    assert any(abs(m.measured_value - 1.8) < 0.1 for m in critique.measured_findings)


def test_level_aware_critique_advanced():
    """Verify that critique generated for advanced animation student uses studio master terminology."""
    student = StudentProfile(
        student_id="level-advanced",
        name="advanced",
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

    assert critique.student_name == "advanced"
    assert critique.level == "advanced"
    assert critique.validated is (critique.source == "vertex")
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

def test_plane_b_may_not_state_a_measurement_in_pixels():
    """Plane B blocked degrees but not pixels, and the orthographic system reports pixels.

    An observation is a claim about the picture. The moment it carries a figure it is a
    measurement, and measurements live in Plane A where they are checked against OpenCV.
    "18 px" is as much a measurement as "6 degrees"; the gate used to see only the second.
    """
    geom = build_sample_geometry(k=1, avg_error=2.4, max_error=5.0)

    critique = CritiqueOutput(
        student_name="beginner-01",
        level="beginner",
        headline="Orthographic review",
        measured_findings=[
            MeasuredFindingItem(
                metric_name="average_convergence_error",
                measured_value=2.4,
                unit="degrees",
                pedagogical_context="Measured by OpenCV.",
            )
        ],
        qualitative_observations=[
            QualitativeObservationItem(
                aspect="correspondence",
                observation="The plan sits about 18 px to the left of the elevation.",
                status="improvement",
            )
        ],
        pedagogical_summary=PedagogicalSummary(
            strengths=["Clean line weight"],
            focus_area="Correspondence",
            encouragement="Keep going.",
        ),
        next_exercise=NextExerciseRecommendation(
            title="Two views of a prism",
            description="Draw plan and elevation of a prism.",
            target_metric="correspondence",
            difficulty="beginner",
        ),
    )

    is_valid, errors = validate_critique_measurements(critique, geom)
    assert is_valid is False
    assert any("states a measurement" in e for e in errors)


def test_plane_b_still_allows_prose_without_figures():
    """The gate must not become so wide that it blocks the qualitative plane entirely."""
    geom = build_sample_geometry(k=1, avg_error=2.4, max_error=5.0)

    critique = CritiqueOutput(
        student_name="beginner-01",
        level="beginner",
        headline="Orthographic review",
        measured_findings=[
            MeasuredFindingItem(
                metric_name="average_convergence_error",
                measured_value=2.4,
                unit="degrees",
                pedagogical_context="Measured by OpenCV.",
            )
        ],
        qualitative_observations=[
            QualitativeObservationItem(
                aspect="correspondence",
                observation="The plan sits a little to the left of the elevation.",
                status="improvement",
            )
        ],
        pedagogical_summary=PedagogicalSummary(
            strengths=["Clean line weight"],
            focus_area="Correspondence",
            encouragement="Keep going.",
        ),
        next_exercise=NextExerciseRecommendation(
            title="Two views of a prism",
            description="Draw plan and elevation of a prism.",
            target_metric="correspondence",
            difficulty="beginner",
        ),
    )

    is_valid, errors = validate_critique_measurements(critique, geom)
    assert is_valid is True, errors


def test_a_server_error_from_vertex_serves_the_template_and_says_so(monkeypatch):
    """A 5xx from Vertex must not reach the student as a 500, and must not pass as a critique.

    The handler at critique.py:225 is deliberately broad. Broad handlers rot quietly, so this
    pins the two things that make it acceptable: the student still gets something usable, and
    the provenance says no model wrote it.
    """
    import src.tools.critique as critique_module
    from google import genai

    # Patched at the SDK boundary, not on call_vertex_ai_critique: replacing the whole function
    # would remove the very handler this test exists to pin.
    def explode(*_args, **_kwargs):
        raise RuntimeError("503 Service Unavailable: backend overloaded")

    monkeypatch.setattr(genai, "Client", explode)

    # The disk cache would answer before the model is ever reached, and it still holds entries
    # written by an older code path that stamped fallbacks as validated=True. Nothing invalidates
    # them, so the test says what it means instead of depending on what is on this machine.
    monkeypatch.setattr(critique_module, "load_from_cache", lambda *_a, **_k: None)
    monkeypatch.setattr(critique_module, "save_to_cache", lambda *_a, **_k: None)

    geom = build_sample_geometry(k=1, avg_error=2.4, max_error=5.0)
    request = CritiqueRequest(
        geometry=geom,
        student=StudentProfile(student_id="level-basic", name="basic", level="beginner"),
    )

    response = critique_module.generate_pedagogical_critique(request)

    assert response.critique.source == "fallback"
    assert response.critique.model_version == "deterministic-template"
    assert response.critique.measured_findings, "the student is still given the geometry"
    assert response.cached is False and response.validation_retries == 3

    # The three deterministic fallbacks now agree: none of them claims validated. Before
    # 2026-08-26 the conic one returned True (critique.py:167) while the other two returned
    # False, so the field meant different things depending on the projection system.
    assert response.critique.validated is False


def _critique_citing(value: float) -> CritiqueOutput:
    """A critique whose single Plane A figure is whatever the caller says."""
    return CritiqueOutput(
        student_name="beginner-01",
        level="beginner",
        headline="Perspective review",
        measured_findings=[
            MeasuredFindingItem(
                metric_name="average_convergence_error",
                measured_value=value,
                unit="degrees",
                pedagogical_context="Cited figure.",
            )
        ],
        qualitative_observations=[],
        pedagogical_summary=PedagogicalSummary(
            strengths=["Steady lines"],
            focus_area="Convergence",
            encouragement="Keep going.",
        ),
        next_exercise=NextExerciseRecommendation(
            title="Cubes",
            description="Draw cubes.",
            target_metric="convergence",
            difficulty="beginner",
        ),
    )


def test_tolerance_default_accepts_a_near_miss():
    """OpenCV measured 2.4; the model wrote 2.8. At the default 0.5 that is rounding, not invention."""
    geom = build_sample_geometry(k=1, avg_error=2.4, max_error=5.0)

    is_valid, errors = validate_critique_measurements(_critique_citing(2.8), geom)

    assert is_valid is True, errors


def test_tolerance_can_be_tightened_to_demand_an_exact_match():
    """The same near miss is rejected when a deployment asks for a stricter gate.

    VALIDATOR_TOLERANCE_DEG exists because 0.5 is wide: with ten numbers on the whitelist, a
    fabricated figure has a real chance of landing inside half a degree of one of them.
    """
    geom = build_sample_geometry(k=1, avg_error=2.4, max_error=5.0)

    is_valid, errors = validate_critique_measurements(_critique_citing(2.8), geom, tolerance=0.0)

    assert is_valid is False
    assert any("Hallucinated measurement detected" in e for e in errors)

    # And the exact value still passes at zero tolerance, so the gate is strict, not broken.
    is_valid_exact, _ = validate_critique_measurements(_critique_citing(2.4), geom, tolerance=0.0)
    assert is_valid_exact is True


def test_the_configured_tolerance_is_the_one_production_uses(monkeypatch):
    """A setting nothing reads is decoration. This pins that the caller passes it through."""
    import src.tools.critique as critique_module

    seen = {}

    def spy(critique, geometry, tolerance=0.5, had_image=True):
        seen["tolerance"] = tolerance
        return (True, [])

    monkeypatch.setattr(critique_module.settings, "validator_tolerance_deg", 0.125)
    monkeypatch.setattr(critique_module, "validate_critique_measurements", spy)
    monkeypatch.setattr(critique_module, "load_from_cache", lambda *_a, **_k: None)
    monkeypatch.setattr(critique_module, "save_to_cache", lambda *_a, **_k: None)
    monkeypatch.setattr(
        critique_module, "call_vertex_ai_critique", lambda *_a, **_k: _critique_citing(2.4)
    )

    geom = build_sample_geometry(k=1, avg_error=2.4, max_error=5.0)
    critique_module.generate_pedagogical_critique(
        CritiqueRequest(
            geometry=geom,
            student=StudentProfile(student_id="level-basic", name="basic", level="beginner"),
        )
    )

    assert seen["tolerance"] == 0.125


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
    assert critique_data["validated"] is (critique_data["source"] == "vertex")
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
