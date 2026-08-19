"""
Deterministic orthographic analysis: two views, folded about a line the student drew.

What this measures is **correspondence**, which is a different invariant from anything else in the
engine. Conic perspective asks whether edges meet at a point; axonometry asks whether they stay
parallel to a fixed direction. Monge projection asks whether the two views agree about where
things are — a vertex in the elevation must have a counterpart directly below it in the plan.

The hard part of that, in principle, is knowing which mark is the plan *of which* vertex. This
module does not solve it and does not need to: in orthographic projection corresponding points
share an abscissa, so comparing the two views' sets of vertex abscissae answers the question
without ever pairing features. A vertex at x=340 in the elevation with nothing near x=340 in the
plan is an unmatched vertex, whatever it belongs to.

Cotas and alejamientos between elevation, plan and profile are **not** measured. Those need a
third view and real feature correspondence, and claiming them from two views would be inventing.
"""

import math

import cv2
import numpy as np

from src.models.dihedral import (
    Correspondence,
    DihedralAnalysisResult,
    GroundLine,
    ReferenceLineMeasurement,
)
from src.models.geometry import Point2D
from src.tools.axonometry import angle_gap_deg, direction_deg
from src.tools.geometry import encode_image_base64, preprocess_and_detect_lines

#: How near horizontal a segment must be to be a candidate ground line.
GROUND_LINE_TOLERANCE_DEG = 12.0

#: A ground line has to actually span the drawing; a short horizontal edge of the object does not.
GROUND_LINE_MIN_SPAN = 0.45

#: How far a segment must reach past the ground line, as a fraction of image height, before it
#: counts as crossing rather than merely touching.
CROSSING_MARGIN = 0.01

#: How close two endpoint abscissae must be to be the same drawn corner, as a fraction of width.
#:
#: This is about the detector, not the student. A drawn edge has thickness, so Canny finds both
#: sides of the stroke and one corner arrives as two abscissae a few pixels apart. Set below the
#: stroke width and every corner counts twice — which is what the first golden run did, reporting
#: two orphan vertices in a drawing that has none.
VERTEX_FRAGMENT_PCT = 1.0


def detect_ground_line(
    lines_raw: list[tuple[float, float, float, float]], img_width: int, img_height: int
) -> GroundLine | None:
    """
    Find the línea de tierra: the longest near-horizontal segment that spans the drawing.

    Returns None rather than guessing. Without a ground line there is no fold, no perpendicular to
    measure against and no way to say which view a mark belongs to — so the honest answer is that
    this is not a Monge drawing, not a set of numbers derived from an assumed line.
    """
    best: tuple[float, tuple[float, float, float, float]] | None = None
    for x1, y1, x2, y2 in lines_raw:
        theta = direction_deg(x1, y1, x2, y2)
        if angle_gap_deg(theta, 0.0) > GROUND_LINE_TOLERANCE_DEG:
            continue
        span = abs(x2 - x1)
        if span < GROUND_LINE_MIN_SPAN * img_width:
            continue
        if best is None or span > best[0]:
            best = (span, (x1, y1, x2, y2))

    if best is None:
        return None

    x1, y1, x2, y2 = best[1]
    if x2 < x1:
        x1, y1, x2, y2 = x2, y2, x1, y1

    theta = direction_deg(x1, y1, x2, y2)
    # Signed tilt in (-90, 90]: a line at 179 degrees is one degree the other way, not 179.
    tilt = theta if theta <= 90.0 else theta - 180.0

    return GroundLine(
        start=Point2D(x=float(x1), y=float(y1), norm_x=float(x1 / img_width), norm_y=float(y1 / img_height)),
        end=Point2D(x=float(x2), y=float(y2), norm_x=float(x2 / img_width), norm_y=float(y2 / img_height)),
        angle_deg=round(tilt, 2),
        length_px=round(math.hypot(x2 - x1, y2 - y1), 1),
        source="detected",
    )


def _ground_y_at(ground: GroundLine, x: float) -> float:
    """The ground line's height at a given abscissa, following its tilt rather than assuming none."""
    dx = ground.end.x - ground.start.x
    if abs(dx) < 1e-6:
        return ground.start.y
    slope = (ground.end.y - ground.start.y) / dx
    return ground.start.y + slope * (x - ground.start.x)


def cluster_abscissae(values: list[float], tolerance_px: float) -> list[float]:
    """
    Collapse endpoint abscissae into vertex positions.

    Hough returns several collinear fragments per drawn edge, so a single corner arrives as a
    handful of endpoints a pixel or two apart. Averaging each cluster gives one abscissa per
    vertex, which is what the correspondence check compares.
    """
    if not values:
        return []
    ordered = sorted(values)
    clusters: list[list[float]] = [[ordered[0]]]
    for v in ordered[1:]:
        if v - clusters[-1][-1] <= tolerance_px:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [float(np.mean(c)) for c in clusters]


def estimate_systematic_offset(
    elevation: list[float], plan: list[float], img_width: float
) -> float | None:
    """
    How far the plan sits sideways from the elevation, taken as a whole.

    A student who places the plan a centimetre to the right has made **one** mistake, and every
    vertex inherits it. Reported per vertex it looks like four unrelated failures; reported once it
    is a single sentence with a single correction. This is the orthographic counterpart of the
    systematic axis error the axonometric engine reports.

    Estimated as the median of each elevation vertex's nearest plan neighbour, which survives a
    genuinely orphaned vertex pulling on the average. Returns None when there is not enough on both
    sides of the fold to establish anything — guessing an offset from one pair would let a single
    stray mark redefine where the plan is.
    """
    if len(elevation) < 2 or len(plan) < 2:
        return None

    deltas = [min((p - e for p in plan), key=abs) for e in elevation]
    offset = float(np.median(deltas))

    # An "offset" larger than a quarter of the page is not a shifted plan, it is two views that do
    # not correspond at all, and subtracting it would manufacture agreement that is not there.
    if abs(offset) > 0.25 * img_width:
        return None
    return offset


def analyze_dihedral_from_lines(
    lines_raw: list[tuple[float, float, float, float]],
    img_width: int,
    img_height: int,
    correspondence_tolerance_pct: float = 1.5,
    min_confidence_threshold: float = 0.35,
    original_image: np.ndarray | None = None,
) -> DihedralAnalysisResult:
    """Measure the two views against each other, about the ground line the student drew."""
    ground = detect_ground_line(lines_raw, img_width, img_height)

    if ground is None:
        return DihedralAnalysisResult(
            ground_line=None,
            line_count=len(lines_raw),
            confidence=0.0,
            confidence_low=True,
            image_width=img_width,
            image_height=img_height,
            overlay_image_base64=None,
        )

    margin = CROSSING_MARGIN * img_height
    ground_theta = direction_deg(ground.start.x, ground.start.y, ground.end.x, ground.end.y)

    elevation_x: list[float] = []
    plan_x: list[float] = []
    reference_lines: list[ReferenceLineMeasurement] = []
    elevation_count = plan_count = 0

    for idx, (x1, y1, x2, y2) in enumerate(lines_raw):
        gy1 = _ground_y_at(ground, x1)
        gy2 = _ground_y_at(ground, x2)
        # Image y grows downward, so "above the ground line" is a smaller y.
        above1, above2 = y1 < gy1 - margin, y2 < gy2 - margin
        below1, below2 = y1 > gy1 + margin, y2 > gy2 + margin

        if above1 and above2:
            elevation_count += 1
            elevation_x.extend((x1, x2))
        elif below1 and below2:
            plan_count += 1
            plan_x.extend((x1, x2))
        elif (above1 and below2) or (below1 and above2):
            # A segment spanning the fold is a reference line: the thing that carries a point from
            # one view to the other, and which the system requires to be perpendicular to the LT.
            theta = direction_deg(x1, y1, x2, y2)
            err = abs(90.0 - angle_gap_deg(theta, ground_theta))
            reference_lines.append(
                ReferenceLineMeasurement(
                    id=idx,
                    start=Point2D(x=float(x1), y=float(y1), norm_x=float(x1 / img_width), norm_y=float(y1 / img_height)),
                    end=Point2D(x=float(x2), y=float(y2), norm_x=float(x2 / img_width), norm_y=float(y2 / img_height)),
                    perpendicularity_error_deg=round(err, 2),
                    crosses_ground_line=True,
                )
            )
        # Segments lying along the ground line itself are neither view and are not counted.

    fragment_tolerance = max(3.0, (VERTEX_FRAGMENT_PCT / 100.0) * img_width)
    # The matching tolerance has to stay clear of the clustering one, or a vertex could be merged
    # with its neighbour and matched against it in the same breath.
    tolerance_px = max(
        (correspondence_tolerance_pct / 100.0) * img_width, 2.0 * fragment_tolerance
    )
    elev_vertices = cluster_abscissae(elevation_x, fragment_tolerance)
    plan_vertices = cluster_abscissae(plan_x, fragment_tolerance)

    # A uniform sideways shift is one mistake, not one per vertex. Estimate it first and take it
    # out, so that what is left over is a vertex the other view genuinely never answered rather
    # than one that was simply displaced along with all the others.
    offset = estimate_systematic_offset(elev_vertices, plan_vertices, img_width)
    shifted_plan = [px - offset for px in plan_vertices] if offset is not None else list(plan_vertices)

    correspondences: list[Correspondence] = []
    errors_px: list[float] = []
    used_plan: set[int] = set()

    for ex in elev_vertices:
        best_i, best_d = None, None
        for i, px in enumerate(shifted_plan):
            if i in used_plan:
                continue
            d = abs(px - ex)
            if best_d is None or d < best_d:
                best_i, best_d = i, d

        if best_i is not None and best_d is not None and best_d <= tolerance_px:
            used_plan.add(best_i)
            errors_px.append(best_d)
            correspondences.append(
                Correspondence(
                    elevation_x=round(ex, 1),
                    plan_x=round(plan_vertices[best_i], 1),
                    error_px=round(best_d, 2),
                    error_pct=round(100.0 * best_d / img_width, 2),
                    matched=True,
                )
            )
        else:
            correspondences.append(
                Correspondence(elevation_x=round(ex, 1), plan_x=None, error_px=None, error_pct=None, matched=False)
            )

    for i, px in enumerate(plan_vertices):
        if i not in used_plan:
            correspondences.append(
                Correspondence(elevation_x=None, plan_x=round(px, 1), error_px=None, error_pct=None, matched=False)
            )

    unmatched_elev = sum(1 for c in correspondences if c.elevation_x is not None and not c.matched)
    unmatched_plan = sum(1 for c in correspondences if c.plan_x is not None and not c.matched)
    matched_count = len(errors_px)

    perp_errors = [r.perpendicularity_error_deg for r in reference_lines]
    views = (1 if elevation_count else 0) + (1 if plan_count else 0)

    if views < 2:
        confidence = 0.0
    else:
        matched_ratio = len(errors_px) / max(1, len(elev_vertices))
        aligned = sum(1 for e in errors_px if e <= tolerance_px / 2.0)
        aligned_ratio = aligned / max(1, len(errors_px)) if errors_px else 0.0
        lines_factor = min(1.0, len(lines_raw) / 10.0)
        ref_factor = 1.0 if reference_lines else 0.4
        confidence = round(
            0.35 * matched_ratio + 0.25 * aligned_ratio + 0.25 * lines_factor + 0.15 * ref_factor, 2
        )

    confidence_low = bool(confidence < min_confidence_threshold or views < 2 or len(lines_raw) < 6)

    overlay = None
    if original_image is not None:
        overlay = generate_dihedral_overlay(original_image, ground, reference_lines, correspondences)

    return DihedralAnalysisResult(
        ground_line=ground,
        reference_lines=reference_lines,
        correspondences=correspondences,
        avg_perpendicularity_error_deg=round(float(np.mean(perp_errors)), 2) if perp_errors else 0.0,
        max_perpendicularity_error_deg=round(float(np.max(perp_errors)), 2) if perp_errors else 0.0,
        systematic_offset_px=round(offset, 2) if offset is not None else None,
        systematic_offset_pct=round(100.0 * offset / img_width, 2) if offset is not None else None,
        # Null, not zero. An average over nothing is undefined, and reporting it as 0.00 told the
        # reader that a plate whose views do not correspond at all was perfectly aligned.
        avg_correspondence_error_px=round(float(np.mean(errors_px)), 2) if errors_px else None,
        max_correspondence_error_px=round(float(np.max(errors_px)), 2) if errors_px else None,
        avg_correspondence_error_pct=round(100.0 * float(np.mean(errors_px)) / img_width, 2) if errors_px else None,
        max_correspondence_error_pct=round(100.0 * float(np.max(errors_px)) / img_width, 2) if errors_px else None,
        matched_vertex_count=matched_count,
        unmatched_in_elevation=unmatched_elev,
        unmatched_in_plan=unmatched_plan,
        elevation_line_count=elevation_count,
        plan_line_count=plan_count,
        line_count=len(lines_raw),
        views_detected=views,
        confidence=confidence,
        confidence_low=confidence_low,
        image_width=img_width,
        image_height=img_height,
        overlay_image_base64=overlay,
    )


#: BGR, matching the other two overlays so all three modes read the same way.
_ACCURATE = (0, 210, 0)
_DRIFT = (0, 200, 255)
_DIVERGING = (0, 0, 230)
_GROUND = (255, 255, 0)


def generate_dihedral_overlay(
    image: np.ndarray,
    ground: GroundLine,
    reference_lines: list[ReferenceLineMeasurement],
    correspondences: list[Correspondence],
) -> str:
    """Draw the ground line, the reference lines by squareness, and every correspondence."""
    overlay = image.copy()
    h, w = overlay.shape[:2]

    cv2.line(
        overlay,
        (int(ground.start.x), int(ground.start.y)),
        (int(ground.end.x), int(ground.end.y)),
        _GROUND,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        f"LT ({ground.angle_deg:+.1f}deg)",
        (int(ground.start.x) + 6, max(18, int(ground.start.y) - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        _GROUND,
        2,
        cv2.LINE_AA,
    )

    for ref in reference_lines:
        err = ref.perpendicularity_error_deg
        colour = _ACCURATE if err < 1.0 else _DRIFT if err <= 3.0 else _DIVERGING
        cv2.line(
            overlay,
            (int(ref.start.x), int(ref.start.y)),
            (int(ref.end.x), int(ref.end.y)),
            colour,
            2,
            cv2.LINE_AA,
        )

    # Every vertex abscissa, marked on the ground line. A matched pair gets a tick; a vertex the
    # other view never answered gets a cross, because "you drew a corner here that has no
    # counterpart" is the single most useful thing this analysis can say.
    for corr in correspondences:
        x = corr.elevation_x if corr.elevation_x is not None else corr.plan_x
        if x is None:
            continue
        gx = int(max(0, min(w - 1, x)))
        gy = int(max(0, min(h - 1, _ground_y_at(ground, x))))
        if corr.matched:
            colour = _ACCURATE if (corr.error_px or 0.0) < 3.0 else _DRIFT
            cv2.circle(overlay, (gx, gy), 5, colour, -1, cv2.LINE_AA)
        else:
            cv2.drawMarker(overlay, (gx, gy), _DIVERGING, cv2.MARKER_TILTED_CROSS, 14, 2, cv2.LINE_AA)

    return encode_image_base64(overlay)


def analyze_dihedral(
    image: np.ndarray,
    correspondence_tolerance_pct: float = 1.5,
    min_confidence_threshold: float = 0.35,
    generate_overlay_image: bool = True,
) -> DihedralAnalysisResult:
    """Detect segments in an image and measure the two orthographic views against each other."""
    lines_raw, _edges = preprocess_and_detect_lines(image)
    h, w = image.shape[:2]
    return analyze_dihedral_from_lines(
        lines_raw,
        img_width=w,
        img_height=h,
        correspondence_tolerance_pct=correspondence_tolerance_pct,
        min_confidence_threshold=min_confidence_threshold,
        original_image=image if generate_overlay_image else None,
    )
