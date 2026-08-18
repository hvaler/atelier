"""Tests for Gemma pre-router on Vertex AI (+0.2 pts ATA Bonus)."""

from fastapi.testclient import TestClient

from src.main import app
from src.tools.gemma_router import classify_drawing_with_gemma

client = TestClient(app)


def test_classify_drawing_with_gemma_beginner():
    """Verify Gemma classifies beginner drawing to 1-point box with appropriate Canny edge thresholds."""
    result = classify_drawing_with_gemma(image_width=800, image_height=600, student_level_hint="beginner")

    assert result.recommended_k == 1
    assert result.level_estimate == "beginner"
    assert result.exercise_type == "1-point-box"
    assert result.confidence >= 0.80


def test_classify_drawing_with_gemma_advanced():
    """Verify Gemma classifies advanced drawing to 2-point oblique setup."""
    result = classify_drawing_with_gemma(image_width=1000, image_height=700, student_level_hint="advanced")

    assert result.recommended_k == 2
    assert result.level_estimate == "advanced"
    assert result.exercise_type == "2-point-oblique"


def test_api_router_classify_endpoint():
    """Verify HTTP POST /api/router/classify endpoint."""
    response = client.post(
        "/api/router/classify",
        json={"image_width": 900, "image_height": 600, "student_level_hint": "advanced"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_k"] == 2
    assert data["exercise_type"] == "2-point-oblique"
