"""
Golden-case tests for the orthographic (sistema diédrico) engine.

Two of these exist because the first golden run failed in ways worth keeping a test for. The
engine reported an average correspondence error of 0.00 px on a plate whose views did not
correspond at all — the mean of an empty set, printed as if it meant perfect alignment — and it
counted every drawn corner twice because a 2-pixel stroke gives Canny two edges. Both are asserted
below so neither can come back.
"""

import math
from pathlib import Path

import cv2
import numpy as np
import pytest
from pydantic import ValidationError

from src.models.critique import CritiqueOutput, CritiqueRequest, MeasuredFindingItem, StudentProfile
from src.tools.dihedral import (
    analyze_dihedral,
    analyze_dihedral_from_lines,
    cluster_abscissae,
    detect_ground_line,
    estimate_systematic_offset,
)
from src.tools.validator import validate_critique_measurements

W, H = 800, 600
LT_Y = 300.0


def plate(
    correspondence_shift: float = 0.0,
    reference_slant_deg: float = 0.0,
    lt_tilt_deg: float = 0.0,
    drop_right_plan_edge: bool = False,
):
    """A Monge plate as line segments: ground line, elevation above, plan below, reference lines."""
    mid = (60.0 + 740.0) / 2.0
    tilt = math.radians(lt_tilt_deg)

    def lt_y(x):
        return LT_Y - (x - mid) * math.tan(tilt)

    lines = [(60.0, lt_y(60.0), 740.0, lt_y(740.0))]

    ex1, ex2, ey1, ey2 = 260.0, 520.0, 140.0, 260.0
    lines += [
        (ex1, ey1, ex2, ey1),
        (ex1, ey2, ex2, ey2),
        (ex1, ey1, ex1, ey2),
        (ex2, ey1, ex2, ey2),
    ]

    px1, px2 = ex1 + correspondence_shift, ex2 + correspondence_shift
    py1, py2 = 350.0, 450.0
    lines += [(px1, py1, px2, py1), (px1, py1, px1, py2)]
    if not drop_right_plan_edge:
        lines += [(px1, py2, px2, py2), (px2, py1, px2, py2)]
    else:
        lines += [(px1, py2, px2 - 90.0, py2)]

    slant = math.radians(reference_slant_deg)
    for x_top in (ex1, ex2):
        dx = (py2 - ey2) * math.tan(slant)
        lines.append((x_top, ey2, x_top + dx, py2))

    return lines


class TestGroundLine:
    def test_the_ground_line_is_found(self):
        g = detect_ground_line(plate(), W, H)
        assert g is not None
        assert g.angle_deg == pytest.approx(0.0, abs=0.05)
        assert g.length_px > 0.45 * W

    def test_a_tilted_ground_line_is_reported_not_corrected(self):
        """Everything else is measured against it, so a crooked reference has to be declared."""
        g = detect_ground_line(plate(lt_tilt_deg=3.0), W, H)
        assert g is not None
        assert abs(g.angle_deg) == pytest.approx(3.0, abs=0.1)

    def test_no_ground_line_means_no_measurements(self):
        """A drawing with no fold is not a Monge plate, and inventing one would measure nothing."""
        result = analyze_dihedral_from_lines(
            [(100.0, 100.0, 100.0, 400.0), (200.0, 120.0, 200.0, 380.0)], W, H
        )
        assert result.ground_line is None
        assert result.confidence == 0.0
        assert result.confidence_low is True
        assert result.avg_correspondence_error_px is None

    def test_a_short_horizontal_edge_is_not_mistaken_for_the_ground_line(self):
        assert detect_ground_line([(300.0, 300.0, 380.0, 300.0)], W, H) is None


class TestGoldenCases:
    def test_a_correct_plate_reports_no_orphans(self):
        r = analyze_dihedral_from_lines(plate(), W, H)
        assert r.views_detected == 2
        assert r.unmatched_in_elevation == 0
        assert r.unmatched_in_plan == 0
        assert r.matched_vertex_count == 2
        assert r.avg_perpendicularity_error_deg == pytest.approx(0.0, abs=0.05)

    def test_an_injected_shift_comes_back_as_one_systematic_offset(self):
        """
        The reading that matters. A plan drawn 18 px to the right is one mistake with one
        correction, not four unrelated broken vertices — the same distinction the axonometric
        engine draws between a systematic and a per-line error.
        """
        r = analyze_dihedral_from_lines(plate(correspondence_shift=18.0), W, H)
        assert r.systematic_offset_px == pytest.approx(18.0, abs=0.5)
        assert r.unmatched_in_elevation == 0
        assert r.unmatched_in_plan == 0

    def test_a_shift_does_not_leak_into_perpendicularity(self):
        """The reference lines are square; only the plan moved."""
        r = analyze_dihedral_from_lines(plate(correspondence_shift=18.0), W, H)
        assert r.avg_perpendicularity_error_deg == pytest.approx(0.0, abs=0.1)

    def test_a_slanted_reference_line_is_measured_against_the_ground_line(self):
        r = analyze_dihedral_from_lines(plate(reference_slant_deg=4.0), W, H)
        assert r.avg_perpendicularity_error_deg == pytest.approx(4.0, abs=0.2)

    def test_an_orphan_vertex_is_found(self):
        """A corner drawn in one view and never answered in the other."""
        r = analyze_dihedral_from_lines(plate(drop_right_plan_edge=True), W, H)
        assert r.unmatched_in_elevation + r.unmatched_in_plan >= 1

    def test_end_to_end_through_the_detector(self):
        sample = Path(__file__).resolve().parents[2] / "demo" / "dataset" / "10_diedrico_error_18px.png"
        image = cv2.imread(str(sample))
        if image is None:
            pytest.skip("calibration dataset not generated")
        r = analyze_dihedral(image, generate_overlay_image=False)
        assert r.systematic_offset_px == pytest.approx(18.0, abs=1.0)


class TestHonesty:
    def test_an_average_over_nothing_is_null_not_zero(self):
        """
        The bug this test exists for: with no matched pair the engine reported 0.00 px, which
        reads as perfect alignment on the worst possible drawing.
        """
        # Two views whose vertices are nowhere near each other, and far enough apart that the
        # offset estimator refuses to manufacture agreement.
        lines = [
            (60.0, LT_Y, 740.0, LT_Y),
            (100.0, 150.0, 180.0, 150.0),
            (100.0, 150.0, 100.0, 250.0),
            (600.0, 400.0, 700.0, 400.0),
            (600.0, 400.0, 600.0, 500.0),
        ]
        r = analyze_dihedral_from_lines(lines, W, H)
        assert r.matched_vertex_count == 0
        assert r.avg_correspondence_error_px is None
        assert r.max_correspondence_error_px is None
        assert r.unmatched_in_elevation + r.unmatched_in_plan > 0

    def test_a_stroke_is_not_two_corners(self):
        """
        Canny finds both sides of a drawn line, so one corner arrives as two abscissae a few
        pixels apart. Clustering below the stroke width counted every corner twice.
        """
        assert cluster_abscissae([258.0, 263.0, 517.0, 521.0], 8.0) == pytest.approx([260.5, 519.0])

    def test_distinct_corners_stay_distinct(self):
        assert len(cluster_abscissae([260.0, 520.0], 8.0)) == 2

    def test_no_offset_is_invented_from_a_single_pair(self):
        assert estimate_systematic_offset([100.0], [400.0], W) is None

    def test_an_absurd_offset_is_refused(self):
        """Two views that do not correspond at all must not be shifted into agreement."""
        assert estimate_systematic_offset([50.0, 60.0], [700.0, 710.0], W) is None

    def test_a_blank_image_measures_nothing(self):
        blank = np.ones((H, W, 3), dtype=np.uint8) * 255
        r = analyze_dihedral(blank, generate_overlay_image=False)
        assert r.confidence_low is True
        assert r.avg_correspondence_error_px is None


class TestValidatorIsSubjectAgnostic:
    def _critique(self, value: float, name: str = "systematic_offset") -> CritiqueOutput:
        return CritiqueOutput(
            student_name="Test",
            level="advanced",
            headline="h",
            measured_findings=[
                MeasuredFindingItem(metric_name=name, measured_value=value, unit="pixels", pedagogical_context="c")
            ],
            qualitative_observations=[],
            pedagogical_summary={"strengths": ["s"], "focus_area": "f", "encouragement": "e"},
            next_exercise={"title": "t", "description": "d", "target_metric": "m", "difficulty": "advanced"},
        )

    def test_a_real_orthographic_figure_passes(self):
        r = analyze_dihedral_from_lines(plate(correspondence_shift=18.0), W, H)
        ok, errors = validate_critique_measurements(self._critique(r.systematic_offset_px), r, had_image=True)
        assert ok, errors

    def test_an_invented_orthographic_figure_is_rejected(self):
        r = analyze_dihedral_from_lines(plate(correspondence_shift=18.0), W, H)
        ok, errors = validate_critique_measurements(self._critique(73.4), r, had_image=True)
        assert not ok
        assert any("Hallucinated" in e for e in errors)


class TestCritiqueRequestShape:
    def _dihedral(self):
        return analyze_dihedral_from_lines(plate(), W, H)

    def test_orthographic_alone_is_accepted(self):
        req = CritiqueRequest(dihedral=self._dihedral(), student=StudentProfile(student_id="s", name="S"))
        assert req.projection == "orthographic"
        assert req.analysis is req.dihedral

    def test_two_analyses_are_refused(self):
        """Otherwise the whitelist becomes the union of two unrelated sets of numbers."""
        from src.tools.axonometry import analyze_axonometric_from_lines

        with pytest.raises(ValidationError, match="exactly one"):
            CritiqueRequest(
                dihedral=self._dihedral(),
                axonometry=analyze_axonometric_from_lines([(0.0, 0.0, 10.0, 10.0)], W, H),
                student=StudentProfile(student_id="s", name="S"),
            )
