"""Tests for deterministic geometry calculations and Golden Cases with known deliberate errors (PAT-005 & ADR-001)."""

import math
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from src.main import app
from src.tools.geometry import (
    analyze_geometry,
    analyze_geometry_from_lines,
    encode_image_base64,
)

client = TestClient(app)


def create_1point_perspective_lines(
    vp: tuple[float, float],
    error_deg_list: list[float],
    width: int = 800,
    height: int = 600,
) -> list[tuple[float, float, float, float]]:
    """Create line segments converging to a 1-point VP with known deliberate angular errors."""
    vp_x, vp_y = vp
    lines = []

    # Starting positions in lower half / corners
    start_points = [
        (50.0, 550.0),
        (200.0, 500.0),
        (600.0, 500.0),
        (750.0, 550.0),
        (100.0, 450.0),
        (700.0, 450.0),
    ]

    for idx, (sx, sy) in enumerate(start_points):
        err_deg = error_deg_list[idx % len(error_deg_list)]
        true_angle = math.atan2(vp_y - sy, vp_x - sx)
        perturbed_angle = true_angle + math.radians(err_deg)

        length = 150.0
        ex = sx + length * math.cos(perturbed_angle)
        ey = sy + length * math.sin(perturbed_angle)
        lines.append((sx, sy, ex, ey))

    return lines


def create_2point_perspective_lines(
    f1: tuple[float, float],
    f2: tuple[float, float],
    f1_errors_deg: list[float],
    f2_errors_deg: list[float],
    width: int = 1000,
    height: int = 600,
) -> list[tuple[float, float, float, float]]:
    """Create lines converging to F1 (left) and F2 (right) with deliberate angular errors."""
    lines = []

    # Center box corner
    corner_x, corner_y = 500.0, 400.0

    # Left-converging lines (towards F1)
    for err in f1_errors_deg:
        sx, sy = corner_x, corner_y + len(lines) * 15
        true_angle = math.atan2(f1[1] - sy, f1[0] - sx)
        angle = true_angle + math.radians(err)
        length = 140.0
        ex = sx + length * math.cos(angle)
        ey = sy + length * math.sin(angle)
        lines.append((sx, sy, ex, ey))

    # Right-converging lines (towards F2)
    for err in f2_errors_deg:
        sx, sy = corner_x, corner_y + len(lines) * 15
        true_angle = math.atan2(f2[1] - sy, f2[0] - sx)
        angle = true_angle + math.radians(err)
        length = 140.0
        ex = sx + length * math.cos(angle)
        ey = sy + length * math.sin(angle)
        lines.append((sx, sy, ex, ey))

    return lines


def test_1point_perspective_golden_case_zero_error():
    """Golden case: 1-point perspective with 0.0° constructed error."""
    vp_target = (400.0, 300.0)
    lines = create_1point_perspective_lines(vp=vp_target, error_deg_list=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    result = analyze_geometry_from_lines(lines, img_width=800, img_height=600, k_points=1)

    assert result.k_detected == 1
    assert result.confidence > 0.70
    assert not result.confidence_low
    assert len(result.vanishing_points) == 1

    detected_vp = result.vanishing_points[0]
    assert abs(detected_vp.point.x - vp_target[0]) < 5.0
    assert abs(detected_vp.point.y - vp_target[1]) < 5.0
    assert result.avg_convergence_error_deg < 0.5


def test_1point_perspective_measured_deliberate_errors():
    """Golden case: 1-point perspective with constructed errors: [0, 4.0, 8.0, 0, 4.0, 8.0] deg."""
    vp_target = (400.0, 250.0)
    known_errors = [0.0, 4.0, 8.0, 0.0, 4.0, 8.0]

    lines = create_1point_perspective_lines(vp=vp_target, error_deg_list=known_errors)
    result = analyze_geometry_from_lines(lines, img_width=800, img_height=600, k_points=1)

    assert result.k_detected == 1
    # Measured error should reflect the introduced perturbation (> 2.0° and max >= 5.0°)
    assert result.avg_convergence_error_deg >= 2.0
    assert result.max_convergence_error_deg >= 5.0


def test_2point_perspective_golden_case_two_foci():
    """Golden case: 2-point perspective with F1=(100, 250) and F2=(900, 250)."""
    f1_target = (100.0, 250.0)
    f2_target = (900.0, 250.0)

    lines = create_2point_perspective_lines(
        f1=f1_target,
        f2=f2_target,
        f1_errors_deg=[0.0, 0.0, 0.0],
        f2_errors_deg=[0.0, 0.0, 0.0],
        width=1000,
        height=600,
    )

    result = analyze_geometry_from_lines(lines, img_width=1000, img_height=600, k_points=2)

    assert result.k_detected == 2
    assert result.confidence > 0.70
    assert result.horizon_line is not None
    # Horizon angle should be near 0° (horizontal line at y=250)
    assert abs(result.horizon_line.angle_deg) < 2.0
    assert result.avg_convergence_error_deg < 0.5


def test_low_confidence_on_blank_or_insufficient_lines():
    """Ensure ADR-001 invariant: Low confidence or blank image produces explicit rejection, not invented geometry."""
    blank_image = np.ones((400, 400, 3), dtype=np.uint8) * 255
    result = analyze_geometry(blank_image, k_points=2)

    assert result.confidence_low is True
    assert result.confidence < 0.35
    assert result.k_detected == 0


def test_overlay_generation():
    """Verify that visual overlay is generated with correct image dimensions and encoded as Base64."""
    canvas = np.ones((500, 500, 3), dtype=np.uint8) * 240
    # Draw simple converging box lines on canvas
    cv2.line(canvas, (100, 450), (250, 250), (20, 20, 20), 2)
    cv2.line(canvas, (400, 450), (250, 250), (20, 20, 20), 2)
    cv2.line(canvas, (150, 400), (250, 250), (20, 20, 20), 2)
    cv2.line(canvas, (350, 400), (250, 250), (20, 20, 20), 2)

    result = analyze_geometry(canvas, k_points=1, generate_overlay_flag=True)

    assert result.overlay_image_base64 is not None
    assert len(result.overlay_image_base64) > 100


def test_api_analyze_endpoint():
    """Test HTTP POST /api/analyze endpoint with base64 drawing payload."""
    canvas = np.ones((400, 600, 3), dtype=np.uint8) * 250
    # Draw converging lines
    cv2.line(canvas, (50, 350), (300, 150), (10, 10, 10), 2)
    cv2.line(canvas, (550, 350), (300, 150), (10, 10, 10), 2)
    cv2.line(canvas, (100, 300), (300, 150), (10, 10, 10), 2)
    cv2.line(canvas, (500, 300), (300, 150), (10, 10, 10), 2)

    b64_img = encode_image_base64(canvas)

    response = client.post(
        "/api/analyze",
        json={
            "image_base64": b64_img,
            "k_points": 1,
            "generate_overlay": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "k_requested" in data
    assert "avg_convergence_error_deg" in data
    assert "confidence" in data
    assert "lines" in data
    assert data["k_requested"] == 1
    assert data["overlay_image_base64"] is not None

def test_analyze_from_dataset_png_files():
    """End-to-end test reading generated calibration PNG files from disk."""
    dataset_dir = Path("demo/dataset")
    if not dataset_dir.exists():
        return

    # Test 1-point perfect image
    img_1p = cv2.imread(str(dataset_dir / "01_1point_perfect.png"))
    if img_1p is not None:
        res_1p = analyze_geometry(img_1p, k_points=1)
        assert res_1p.k_detected >= 1
        assert res_1p.line_count >= 4
        assert not res_1p.confidence_low

    # Test 2-point perfect image
    img_2p = cv2.imread(str(dataset_dir / "04_2point_perfect.png"))
    if img_2p is not None:
        res_2p = analyze_geometry(img_2p, k_points=2)
        assert res_2p.line_count >= 4
        assert not res_2p.confidence_low
        assert res_2p.overlay_image_base64 is not None
