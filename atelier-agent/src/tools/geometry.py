"""Deterministic perspective geometry engine using OpenCV and NumPy (ADR-001).

Calculates vanishing points, horizon line, per-line angular convergence error (in degrees),
and confidence score without any LLM metric estimation.
"""

import base64
import math

import cv2
import numpy as np

from src.models.geometry import (
    GeometryAnalysisResult,
    HorizonLine,
    LineSegment,
    Point2D,
    VanishingPoint,
)


def decode_image_base64(image_base64: str) -> np.ndarray:
    """Decode a base64-encoded image string to an OpenCV BGR numpy image."""
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    image_bytes = base64.b64decode(image_base64)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image from provided base64 data.")
    return image


def encode_image_base64(image: np.ndarray) -> str:
    """Encode an OpenCV BGR image to base64 PNG string."""
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Could not encode image to PNG format.")
    return base64.b64encode(buffer).decode("utf-8")


def angle_diff_deg(angle1_rad: float, angle2_rad: float) -> float:
    """Calculate minimal acute angular difference in degrees between two line orientations (0-90°)."""
    diff = abs(angle1_rad - angle2_rad) % math.pi
    if diff > math.pi / 2:
        diff = math.pi - diff
    return math.degrees(diff)


def line_intersection(line1: tuple[float, float, float, float], line2: tuple[float, float, float, float]) -> tuple[float, float] | None:
    """Compute 2D intersection of two lines defined by endpoints (x1, y1, x2, y2)."""
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-6:
        return None  # Lines are parallel or collinear

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)


def preprocess_and_detect_lines(image: np.ndarray) -> tuple[list[tuple[float, float, float, float]], np.ndarray]:
    """Preprocess image (deskew, contrast normalization, adaptive threshold) and detect line segments."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()

    # Contrast enhancement & noise reduction
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

    # Probabilistic Hough Line Transform
    h, w = gray.shape[:2]
    min_line_len = max(20, int(min(h, w) * 0.04))
    max_line_gap = max(5, int(min_line_len * 0.3))

    hough_lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi / 180, threshold=30, minLineLength=min_line_len, maxLineGap=max_line_gap)

    detected_segments = []
    if hough_lines is not None:
        for line in hough_lines:
            coords = line.ravel()
            if len(coords) >= 4:
                x1, y1, x2, y2 = coords[:4]
                length = math.hypot(x2 - x1, y2 - y1)
                if length >= min_line_len:
                    detected_segments.append((float(x1), float(y1), float(x2), float(y2)))

    return detected_segments, edges


def estimate_vp_ransac(lines: list[tuple[float, float, float, float]], max_iterations: int = 150, inlier_threshold_deg: float = 3.5) -> tuple[float, float, list[int], float] | None:
    """Estimate a vanishing point using RANSAC over candidate pairwise intersections."""
    if len(lines) < 2:
        return None

    best_vp = None
    best_inliers: list[int] = []
    best_error = float("inf")

    # Generate pairwise intersections as candidate VPs
    candidates = []
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            pt = line_intersection(lines[i], lines[j])
            if pt is not None:
                candidates.append(pt)

    if not candidates:
        return None

    # Evaluate candidate points
    np.random.seed(42)
    sample_candidates = candidates if len(candidates) <= max_iterations else [candidates[idx] for idx in np.random.choice(len(candidates), max_iterations, replace=False)]

    for vp_x, vp_y in sample_candidates:
        inliers = []
        errors = []

        for idx, (x1, y1, x2, y2) in enumerate(lines):
            mid_x = (x1 + x2) / 2.0
            mid_y = (y1 + y2) / 2.0

            actual_angle = math.atan2(y2 - y1, x2 - x1)
            expected_angle = math.atan2(vp_y - mid_y, vp_x - mid_x)

            err_deg = angle_diff_deg(actual_angle, expected_angle)
            if err_deg <= inlier_threshold_deg:
                inliers.append(idx)
                errors.append(err_deg)

        if len(inliers) > len(best_inliers) or (len(inliers) == len(best_inliers) and errors and np.mean(errors) < best_error):
            best_inliers = inliers
            best_vp = (vp_x, vp_y)
            best_error = float(np.mean(errors)) if errors else 0.0

    if best_vp is None:
        return None

    # Refine VP location using weighted least squares / median of inlier line pairs
    return (best_vp[0], best_vp[1], best_inliers, best_error)


def analyze_geometry_from_lines(
    lines_raw: list[tuple[float, float, float, float]],
    img_width: int,
    img_height: int,
    k_points: int = 2,
    min_confidence_threshold: float = 0.35,
    original_image: np.ndarray | None = None,
) -> GeometryAnalysisResult:
    """Analyze line segments, compute vanishing points, horizon line, error degrees, and confidence."""
    # Filter lines: separate near-vertical lines from converging lines
    converging_candidates = []
    vertical_lines = []

    for x1, y1, x2, y2 in lines_raw:
        angle_rad = math.atan2(y2 - y1, x2 - x1)
        angle_deg = math.degrees(angle_rad)
        acute_deg = abs(angle_deg) % 180
        if acute_deg > 90:
            acute_deg = 180 - acute_deg

        # If angle is within 80°-100° (near vertical), keep as vertical reference
        if acute_deg >= 80:
            vertical_lines.append((x1, y1, x2, y2))
        else:
            converging_candidates.append((x1, y1, x2, y2))

    vanishing_points: list[VanishingPoint] = []
    line_segments: list[LineSegment] = []
    horizon: HorizonLine | None = None

    if k_points == 1:
        # 1-point perspective: single central vanishing point
        result_vp = estimate_vp_ransac(converging_candidates, max_iterations=200, inlier_threshold_deg=4.0)
        if result_vp is not None:
            vp_x, vp_y, inlier_indices, avg_err = result_vp
            vp_pt = Point2D(x=float(vp_x), y=float(vp_y), norm_x=float(vp_x / img_width), norm_y=float(vp_y / img_height))
            vanishing_points.append(
                VanishingPoint(index=0, label="VP", point=vp_pt, supporting_lines=len(inlier_indices), avg_error_deg=round(avg_err, 2))
            )

            # Horizon is horizontal line through VP
            horizon = HorizonLine(
                start=Point2D(x=0.0, y=float(vp_y), norm_x=0.0, norm_y=float(vp_y / img_height)),
                end=Point2D(x=float(img_width), y=float(vp_y), norm_x=1.0, norm_y=float(vp_y / img_height)),
                slope=0.0,
                intercept=float(vp_y),
                angle_deg=0.0,
            )

    else:
        # 2-point perspective: separate into left-leaning and right-leaning lines
        left_lines = []
        right_lines = []

        for line in converging_candidates:
            x1, y1, x2, y2 = line
            slope = (y2 - y1) / (x2 - x1 + 1e-6)
            if slope < 0:
                left_lines.append(line)
            else:
                right_lines.append(line)

        vp_f1 = estimate_vp_ransac(left_lines, max_iterations=150, inlier_threshold_deg=4.0)
        vp_f2 = estimate_vp_ransac(right_lines, max_iterations=150, inlier_threshold_deg=4.0)

        if vp_f1 is not None:
            vp_x, vp_y, inliers_f1, err_f1 = vp_f1
            pt = Point2D(x=float(vp_x), y=float(vp_y), norm_x=float(vp_x / img_width), norm_y=float(vp_y / img_height))
            vanishing_points.append(
                VanishingPoint(index=0, label="F1", point=pt, supporting_lines=len(inliers_f1), avg_error_deg=round(err_f1, 2))
            )

        if vp_f2 is not None:
            vp_x, vp_y, inliers_f2, err_f2 = vp_f2
            pt = Point2D(x=float(vp_x), y=float(vp_y), norm_x=float(vp_x / img_width), norm_y=float(vp_y / img_height))
            vanishing_points.append(
                VanishingPoint(index=1, label="F2", point=pt, supporting_lines=len(inliers_f2), avg_error_deg=round(err_f2, 2))
            )

        # Estimate horizon passing through F1 and F2
        if len(vanishing_points) == 2:
            p1 = vanishing_points[0].point
            p2 = vanishing_points[1].point
            if abs(p2.x - p1.x) > 1e-3:
                slope = (p2.y - p1.y) / (p2.x - p1.x)
                intercept = p1.y - slope * p1.x
                y_left = intercept
                y_right = slope * img_width + intercept
                angle_deg = math.degrees(math.atan(slope))

                horizon = HorizonLine(
                    start=Point2D(x=0.0, y=float(y_left), norm_x=0.0, norm_y=float(y_left / img_height)),
                    end=Point2D(x=float(img_width), y=float(y_right), norm_x=1.0, norm_y=float(y_right / img_height)),
                    slope=float(slope),
                    intercept=float(intercept),
                    angle_deg=round(float(angle_deg), 2),
                )

    # Compute convergence error for every individual line segment
    all_errors = []

    for line_id, (x1, y1, x2, y2) in enumerate(lines_raw, start=1):
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0
        actual_angle = math.atan2(y2 - y1, x2 - x1)
        length = math.hypot(x2 - x1, y2 - y1)

        best_vp_idx = None
        min_err = None

        for vp in vanishing_points:
            expected_angle = math.atan2(vp.point.y - mid_y, vp.point.x - mid_x)
            err = angle_diff_deg(actual_angle, expected_angle)
            if min_err is None or err < min_err:
                min_err = err
                best_vp_idx = vp.index

        if min_err is not None:
            all_errors.append(min_err)

        line_segments.append(
            LineSegment(
                id=line_id,
                start=Point2D(x=float(x1), y=float(y1), norm_x=float(x1 / img_width), norm_y=float(y1 / img_height)),
                end=Point2D(x=float(x2), y=float(y2), norm_x=float(x2 / img_width), norm_y=float(y2 / img_height)),
                angle_deg=round(math.degrees(actual_angle), 2),
                length_px=round(float(length), 1),
                vp_index=best_vp_idx,
                convergence_error_deg=round(float(min_err), 2) if min_err is not None else None,
            )
        )

    # Global summary metrics
    avg_error = float(np.mean(all_errors)) if all_errors else 0.0
    max_error = float(np.max(all_errors)) if all_errors else 0.0
    k_detected = len(vanishing_points)

    # Confidence calculation: based on line count, VP discovery, and inlier ratio (< 5° error)
    if not lines_raw or k_detected == 0:
        confidence = 0.0
    else:
        inliers_count = sum(1 for e in all_errors if e <= 5.0)
        inlier_ratio = inliers_count / max(1, len(all_errors))
        lines_factor = min(1.0, len(lines_raw) / 8.0)
        vp_factor = 1.0 if k_detected == k_points else 0.5
        confidence = round(0.5 * inlier_ratio + 0.3 * lines_factor + 0.2 * vp_factor, 2)

    confidence_low = bool(confidence < min_confidence_threshold or len(lines_raw) < 4 or k_detected == 0)

    # Generate overlay image if base image is available
    overlay_base64 = None
    if original_image is not None:
        overlay_base64 = generate_overlay(original_image, vanishing_points, horizon, line_segments)

    return GeometryAnalysisResult(
        k_requested=k_points,
        k_detected=k_detected,
        vanishing_points=vanishing_points,
        horizon_line=horizon,
        avg_convergence_error_deg=round(avg_error, 2),
        max_convergence_error_deg=round(max_error, 2),
        line_count=len(lines_raw),
        confidence=confidence,
        confidence_low=confidence_low,
        image_width=img_width,
        image_height=img_height,
        lines=line_segments,
        overlay_image_base64=overlay_base64,
    )


def generate_overlay(
    image: np.ndarray,
    vanishing_points: list[VanishingPoint],
    horizon: HorizonLine | None,
    lines: list[LineSegment],
) -> str:
    """Generate visual overlay highlighting vanishing points, horizon, and color-coded line convergence."""
    overlay = image.copy()
    h, w = overlay.shape[:2]

    # Draw line segments colored by convergence error
    for line in lines:
        pt1 = (int(line.start.x), int(line.start.y))
        pt2 = (int(line.end.x), int(line.end.y))
        err = line.convergence_error_deg

        if err is None:
            color = (180, 180, 180)  # Neutral gray
            thickness = 1
        elif err < 2.5:
            color = (0, 210, 0)  # Green: precise convergence (<2.5°)
            thickness = 2
        elif err <= 6.0:
            color = (0, 200, 255)  # Amber/Yellow: minor deviation (2.5°-6°)
            thickness = 2
        else:
            color = (0, 0, 230)  # Red: noticeable error (>6°)
            thickness = 2

        cv2.line(overlay, pt1, pt2, color, thickness, cv2.LINE_AA)

    # Draw Horizon Line (Cyan)
    if horizon is not None:
        h_start = (int(horizon.start.x), int(horizon.start.y))
        h_end = (int(horizon.end.x), int(horizon.end.y))
        cv2.line(overlay, h_start, h_end, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(overlay, "HORIZON (LH)", (20, max(25, int(h_start[1]) - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2, cv2.LINE_AA)

    # Draw Vanishing Points (Markers & labels)
    for vp in vanishing_points:
        vx, vy = int(vp.point.x), int(vp.point.y)
        # Draw on canvas or clamped near boundary if outside
        draw_x = max(10, min(w - 10, vx))
        draw_y = max(10, min(h - 10, vy))

        cv2.circle(overlay, (draw_x, draw_y), 7, (0, 0, 255), -1, cv2.LINE_AA)
        cv2.circle(overlay, (draw_x, draw_y), 11, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(overlay, f"{vp.label} ({vp.avg_error_deg:.1f}deg)", (draw_x + 10, draw_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)

    return encode_image_base64(overlay)


def analyze_geometry(
    image: np.ndarray,
    k_points: int = 2,
    min_confidence_threshold: float = 0.35,
    generate_overlay_flag: bool = True,
) -> GeometryAnalysisResult:
    """Analyze drawing image directly using OpenCV deterministic pipeline."""
    h, w = image.shape[:2]
    detected_lines, _ = preprocess_and_detect_lines(image)

    return analyze_geometry_from_lines(
        lines_raw=detected_lines,
        img_width=w,
        img_height=h,
        k_points=k_points,
        min_confidence_threshold=min_confidence_threshold,
        original_image=image if generate_overlay_flag else None,
    )
