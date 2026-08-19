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

DATASET_DIR = Path(__file__).resolve().parents[2] / "demo" / "dataset"


def test_dataset_pngs_recover_the_vanishing_point():
    """
    The detector, on real image files, must find the vanishing point it was drawn around.

    This test used to open with `if not dataset_dir.exists(): return` against a CWD-relative
    path that never resolves under CI's working directory, and every assertion inside was
    additionally wrapped in `if img is not None`. It reported PASSED without executing a single
    assertion — while the pipeline it claimed to cover was measuring 29 degrees of convergence
    error on a drawing constructed to have none.
    """
    img = cv2.imread(str(DATASET_DIR / "01_1point_perfect.png"))
    assert img is not None, f"calibration dataset missing; run demo/generate_calibration_dataset.py ({DATASET_DIR})"

    result = analyze_geometry(img, k_points=1)

    assert result.k_detected == 1
    vp = result.vanishing_points[0].point
    # The generator draws every receding edge towards (400, 250).
    assert abs(vp.x - 400.0) < 15.0, f"F1 x drifted to {vp.x}"
    assert abs(vp.y - 250.0) < 15.0, f"F1 y drifted to {vp.y}"
    assert result.avg_convergence_error_deg < 2.0, (
        f"a drawing built with zero error measured {result.avg_convergence_error_deg} deg"
    )


def test_dataset_pngs_measure_the_injected_error():
    """A deliberately wrong edge must measure worse than a correct one, in the right order."""
    measured = {}
    for name in ("01_1point_perfect.png", "02_1point_error_4deg.png", "03_1point_error_9deg.png"):
        img = cv2.imread(str(DATASET_DIR / name))
        assert img is not None, f"missing {name}"
        measured[name] = analyze_geometry(img, k_points=1).max_convergence_error_deg

    perfect = measured["01_1point_perfect.png"]
    slight = measured["02_1point_error_4deg.png"]
    bad = measured["03_1point_error_9deg.png"]

    # The generator perturbs one of the four receding edges, so the *worst* line carries the
    # injected error. Ordering is the property that matters: the number has to move with the
    # drawing. It did not before — the perfect drawing measured worse than the bad one.
    assert perfect < slight < bad, f"ordering broken: {perfect} / {slight} / {bad}"
    assert perfect < 4.0, f"zero-error drawing measured {perfect} deg on its worst line"
    assert bad > 8.0, f"9-degree error drawing only reached {bad} deg"


def test_dataset_two_point_reports_a_level_horizon():
    """
    In two-point perspective a consistent rotation does not scatter convergence — it lifts one
    vanishing point off the horizon. The symptom is a tilted horizon, so that is what is asserted.
    """
    flat = analyze_geometry(cv2.imread(str(DATASET_DIR / "04_2point_perfect.png")), k_points=2)
    tilted = analyze_geometry(cv2.imread(str(DATASET_DIR / "05_2point_error_6deg.png")), k_points=2)

    assert flat.k_detected == 2
    assert flat.horizon_line is not None and tilted.horizon_line is not None
    assert abs(flat.horizon_line.angle_deg) < 1.5, (
        f"a level horizon measured {flat.horizon_line.angle_deg} deg of tilt"
    )
    assert abs(tilted.horizon_line.angle_deg) > abs(flat.horizon_line.angle_deg), (
        "the drawing with a rotated vanishing point should show the more tilted horizon"
    )
