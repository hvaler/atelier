"""
Deterministic axonometric analysis: parallel projection measured against a fixed reference.

**Why this is not the perspective engine with different constants.** In conic perspective the
engine does not know where the vanishing point was supposed to be. It estimates one with RANSAC
from the student's own lines and then measures deviation from its own estimate — so a drawing that
is consistently wrong produces a vanishing point that agrees with it, and the reported error is
small. That is a real weakness, honestly stated in `docs/PEDAGOGY.md`.

Axonometry does not have it. The axes of an isometric projection are at 30, 90 and 150 degrees by
definition, not by inference. Nothing is estimated: every segment is compared against a constant.
The measurement is therefore *more* trustworthy here than in the case this project started with,
which is the opposite of what "we also support another mode" usually means.

Angle convention throughout: **drawing space**, degrees anticlockwise from horizontal as the
viewer sees the page, folded to [0, 180). Image coordinates grow downward, so the y delta is
negated once, here, and nowhere else.
"""

import math

import cv2
import numpy as np

from src.models.axonometry import (
    AxisMeasurement,
    AxisSegment,
    AxisSpec,
    AxonometricAnalysisResult,
)
from src.models.geometry import Point2D
from src.tools.geometry import encode_image_base64, preprocess_and_detect_lines

#: The projection systems, and the angles that define them.
#:
#: Isometric is unambiguous: the three axes are 120 degrees apart in space and project 60 degrees
#: apart on the page. Dimetric and cavalier are *conventions*, and more than one is taught, so the
#: figures used here are named rather than assumed — dimetric follows the normalised 7 deg / 41 deg 25'
#: convention, and cavalier defaults to a 45 degree receding axis with 30 and 60 also accepted.
AXIS_SYSTEMS: dict[str, list[AxisSpec]] = {
    "isometric": [
        AxisSpec(label="X", nominal_angle_deg=30.0),
        AxisSpec(label="Y", nominal_angle_deg=150.0),
        AxisSpec(label="Z", nominal_angle_deg=90.0),
    ],
    "dimetric": [
        AxisSpec(label="X", nominal_angle_deg=7.0),
        AxisSpec(label="Y", nominal_angle_deg=138.58),
        AxisSpec(label="Z", nominal_angle_deg=90.0),
    ],
    "cavalier": [
        AxisSpec(label="X", nominal_angle_deg=0.0),
        AxisSpec(label="Y", nominal_angle_deg=45.0),
        AxisSpec(label="Z", nominal_angle_deg=90.0),
    ],
}

#: Deviation above which a segment is called off-axis. It is flagged, not removed.
OFF_AXIS_THRESHOLD_DEG = 10.0


def direction_deg(x1: float, y1: float, x2: float, y2: float) -> float:
    """Direction of a segment in drawing space, folded to [0, 180)."""
    # Negating dy converts image coordinates (y down) to the orientation a person reading the
    # drawing would describe. Folding to 180 makes direction undirected: a line drawn right-to-left
    # is the same line.
    return math.degrees(math.atan2(-(y2 - y1), x2 - x1)) % 180.0


def angle_gap_deg(a: float, b: float) -> float:
    """Smallest angle between two undirected directions, in [0, 90]."""
    diff = abs(a - b) % 180.0
    return min(diff, 180.0 - diff)


def mean_direction_deg(angles: list[float]) -> float:
    """
    Circular mean of undirected directions.

    Doubling before averaging and halving after is what makes 179 and 1 average to 0 rather than
    to 90. Averaging them naively is the classic way to report that a set of near-horizontal lines
    points straight up.
    """
    doubled = [math.radians(2.0 * a) for a in angles]
    s = sum(math.sin(d) for d in doubled)
    c = sum(math.cos(d) for d in doubled)
    return (math.degrees(math.atan2(s, c)) / 2.0) % 180.0


def resolve_axes(system: str, receding_angle_deg: float | None = None) -> list[AxisSpec]:
    """The axis directions for a system, with the cavalier receding axis overridable."""
    if system not in AXIS_SYSTEMS:
        raise ValueError(f"Unknown axonometric system '{system}'. Known: {sorted(AXIS_SYSTEMS)}")

    axes = [AxisSpec(**spec.model_dump()) for spec in AXIS_SYSTEMS[system]]
    if system == "cavalier" and receding_angle_deg is not None:
        for axis in axes:
            if axis.label == "Y":
                axis.nominal_angle_deg = float(receding_angle_deg) % 180.0
    return axes


def analyze_axonometric_from_lines(
    lines_raw: list[tuple[float, float, float, float]],
    img_width: int,
    img_height: int,
    system: str = "isometric",
    receding_angle_deg: float | None = None,
    off_axis_threshold_deg: float = OFF_AXIS_THRESHOLD_DEG,
    min_confidence_threshold: float = 0.35,
    original_image: np.ndarray | None = None,
) -> AxonometricAnalysisResult:
    """Measure detected segments against a projection system's fixed axes."""
    axes = resolve_axes(system, receding_angle_deg)

    segments: list[AxisSegment] = []
    per_axis_angles: list[list[float]] = [[] for _ in axes]
    per_axis_errors: list[list[float]] = [[] for _ in axes]
    all_errors: list[float] = []

    for idx, (x1, y1, x2, y2) in enumerate(lines_raw):
        theta = direction_deg(x1, y1, x2, y2)

        # Nearest axis, always. Nothing is discarded for being too wrong: dropping a segment
        # because it misses badly would pull the average error down exactly when the drawing got
        # worse, which is the one direction the number must never move on its own.
        gaps = [angle_gap_deg(theta, axis.nominal_angle_deg) for axis in axes]
        best = int(np.argmin(gaps))
        err = float(gaps[best])

        per_axis_angles[best].append(theta)
        per_axis_errors[best].append(err)
        all_errors.append(err)

        length = math.hypot(x2 - x1, y2 - y1)
        segments.append(
            AxisSegment(
                id=idx,
                start=Point2D(x=float(x1), y=float(y1), norm_x=float(x1 / img_width), norm_y=float(y1 / img_height)),
                end=Point2D(x=float(x2), y=float(y2), norm_x=float(x2 / img_width), norm_y=float(y2 / img_height)),
                angle_deg=round(theta, 2),
                length_px=round(float(length), 1),
                axis_index=best,
                axis_error_deg=round(err, 2),
                off_axis=bool(err > off_axis_threshold_deg),
            )
        )

    measurements: list[AxisMeasurement] = []
    parallelism_error = 0.0
    for i, axis in enumerate(axes):
        angles = per_axis_angles[i]
        errors = per_axis_errors[i]
        measured = mean_direction_deg(angles) if angles else None

        systematic = None
        if measured is not None:
            # Signed, and folded so that a 179-vs-1 pair reads as +2 rather than -178.
            raw = (measured - axis.nominal_angle_deg + 90.0) % 180.0 - 90.0
            systematic = round(raw, 2)

        if len(angles) > 1:
            # Spread within the family: in a parallel projection these edges must stay parallel to
            # each other, which is the invariant convergence-to-a-point replaces in perspective.
            spread = max(angle_gap_deg(a, b) for a in angles for b in angles)
            parallelism_error = max(parallelism_error, spread)

        measurements.append(
            AxisMeasurement(
                index=i,
                label=axis.label,
                nominal_angle_deg=round(axis.nominal_angle_deg, 2),
                measured_angle_deg=round(measured, 2) if measured is not None else None,
                systematic_error_deg=systematic,
                supporting_lines=len(angles),
                avg_error_deg=round(float(np.mean(errors)), 2) if errors else 0.0,
                max_error_deg=round(float(np.max(errors)), 2) if errors else 0.0,
            )
        )

    axes_supported = sum(1 for m in measurements if m.supporting_lines > 0)
    off_axis_count = sum(1 for s in segments if s.off_axis)

    if not lines_raw:
        confidence = 0.0
    else:
        inliers = sum(1 for e in all_errors if e <= 5.0)
        inlier_ratio = inliers / max(1, len(all_errors))
        lines_factor = min(1.0, len(lines_raw) / 8.0)
        # An axonometric solid shows all three axes. Two means the drawing is a flat face, or the
        # detector only found part of it; either way the reading is worth less.
        axis_factor = 1.0 if axes_supported == len(axes) else (0.5 if axes_supported == 2 else 0.2)
        confidence = round(0.5 * inlier_ratio + 0.3 * lines_factor + 0.2 * axis_factor, 2)

    confidence_low = bool(
        confidence < min_confidence_threshold or len(lines_raw) < 4 or axes_supported < 2
    )

    overlay_base64 = None
    if original_image is not None:
        overlay_base64 = generate_axonometric_overlay(original_image, axes, segments, measurements)

    return AxonometricAnalysisResult(
        system=system,
        axes=measurements,
        avg_axis_error_deg=round(float(np.mean(all_errors)), 2) if all_errors else 0.0,
        max_axis_error_deg=round(float(np.max(all_errors)), 2) if all_errors else 0.0,
        parallelism_error_deg=round(parallelism_error, 2),
        off_axis_line_count=off_axis_count,
        line_count=len(lines_raw),
        axes_supported=axes_supported,
        confidence=confidence,
        confidence_low=confidence_low,
        image_width=img_width,
        image_height=img_height,
        lines=segments,
        overlay_image_base64=overlay_base64,
    )


#: BGR, matching the perspective overlay so the two modes read the same way.
_ACCURATE = (0, 210, 0)
_DRIFT = (0, 200, 255)
_DIVERGING = (0, 0, 230)
_REFERENCE = (255, 255, 0)


def generate_axonometric_overlay(
    image: np.ndarray,
    axes: list[AxisSpec],
    segments: list[AxisSegment],
    measurements: list[AxisMeasurement],
) -> str:
    """Colour every segment by its deviation, and draw the reference axes it was measured against."""
    overlay = image.copy()
    h, w = overlay.shape[:2]

    for seg in segments:
        err = seg.axis_error_deg
        if err < 2.5:
            colour, thickness = _ACCURATE, 2
        elif err <= 6.0:
            colour, thickness = _DRIFT, 2
        else:
            colour, thickness = _DIVERGING, 2
        cv2.line(
            overlay,
            (int(seg.start.x), int(seg.start.y)),
            (int(seg.end.x), int(seg.end.y)),
            colour,
            thickness,
            cv2.LINE_AA,
        )

    # The reference rosette. Perspective can point at a vanishing point on the page; a parallel
    # projection has nothing to point at, so the reference has to be drawn as directions. Without
    # it the overlay would show colours with no visible statement of what they were measured
    # against.
    cx, cy = int(w * 0.13), int(h * 0.85)
    ray = int(min(w, h) * 0.10)
    cv2.circle(overlay, (cx, cy), 4, (255, 255, 255), -1, cv2.LINE_AA)
    for axis, m in zip(axes, measurements):
        rad = math.radians(axis.nominal_angle_deg)
        ex, ey = int(cx + ray * math.cos(rad)), int(cy - ray * math.sin(rad))
        cv2.line(overlay, (cx, cy), (ex, ey), _REFERENCE, 2, cv2.LINE_AA)
        # Push the label along the ray rather than always to its right, so a left-pointing axis
        # does not have its own name written across it.
        label = f"{axis.label} {axis.nominal_angle_deg:.0f}deg"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        lx = ex + 6 if math.cos(rad) >= 0 else ex - tw - 6
        ly = ey - 6 if math.sin(rad) >= 0 else ey + th + 6
        cv2.putText(overlay, label, (lx, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.4, _REFERENCE, 1, cv2.LINE_AA)

        # A systematic drift is drawn as a second, dashed-looking ray so the gap between "where it
        # should point" and "where this drawing points" is visible rather than only tabulated.
        if m.measured_angle_deg is not None and abs(m.systematic_error_deg or 0.0) >= 1.0:
            mrad = math.radians(m.measured_angle_deg)
            mx, my = int(cx + ray * 0.8 * math.cos(mrad)), int(cy - ray * 0.8 * math.sin(mrad))
            cv2.line(overlay, (cx, cy), (mx, my), _DIVERGING, 1, cv2.LINE_AA)

    return encode_image_base64(overlay)


def analyze_axonometric(
    image: np.ndarray,
    system: str = "isometric",
    receding_angle_deg: float | None = None,
    off_axis_threshold_deg: float = OFF_AXIS_THRESHOLD_DEG,
    min_confidence_threshold: float = 0.35,
    generate_overlay_image: bool = True,
) -> AxonometricAnalysisResult:
    """Detect segments in an image and measure them against a projection system."""
    lines_raw, _edges = preprocess_and_detect_lines(image)
    h, w = image.shape[:2]
    return analyze_axonometric_from_lines(
        lines_raw,
        img_width=w,
        img_height=h,
        system=system,
        receding_angle_deg=receding_angle_deg,
        off_axis_threshold_deg=off_axis_threshold_deg,
        min_confidence_threshold=min_confidence_threshold,
        original_image=image if generate_overlay_image else None,
    )
