"""
Golden-case tests for the axonometric engine.

The perspective suite has to tolerate an estimator: RANSAC guesses where the vanishing point was
meant to be, so its assertions are bounded ("within one pixel", "under five degrees"). Axonometry
has no estimator. The axes are constants of the projection, so an error injected at six degrees
must come back as six degrees, and these tests assert that tightly on purpose — a loose bound here
would hide the very property that makes this mode worth having.
"""

import math
from pathlib import Path

import cv2
import numpy as np
import pytest
from pydantic import ValidationError

from src.models.critique import CritiqueOutput, CritiqueRequest, MeasuredFindingItem, StudentProfile
from src.models.geometry import GeometryAnalysisResult
from src.tools.axonometry import (
    analyze_axonometric,
    analyze_axonometric_from_lines,
    angle_gap_deg,
    direction_deg,
    mean_direction_deg,
    resolve_axes,
)
from src.tools.validator import validate_critique_measurements

ISO = {"X": 30.0, "Y": 150.0, "Z": 90.0}


def segment_at(angle_deg: float, x: float = 100.0, y: float = 300.0, length: float = 120.0):
    """A segment running at a drawing-space angle, returned in image coordinates."""
    rad = math.radians(angle_deg)
    return (x, y, x + length * math.cos(rad), y - length * math.sin(rad))


def isometric_cube_lines(error_deg: float = 0.0, perturbed: str = "X", side: float = 180.0):
    """The twelve edges of an isometric cube, with one axis family tilted by a known amount."""
    drawn = dict(ISO)
    drawn[perturbed] = ISO[perturbed] + error_deg
    origin = (330.0, 430.0)

    def unit(label, table):
        rad = math.radians(table[label])
        return math.cos(rad), math.sin(rad)

    def vertex(a, b, c):
        dx = dy = 0.0
        for count, label in ((a, "X"), (b, "Y"), (c, "Z")):
            if count:
                ux, uy = unit(label, ISO)
                dx += side * count * ux
                dy += side * count * uy
        return origin[0] + dx, origin[1] - dy

    edges = []
    for b in (0, 1):
        for c in (0, 1):
            edges.append(((0, b, c), "X"))
    for a in (0, 1):
        for c in (0, 1):
            edges.append(((a, 0, c), "Y"))
    for a in (0, 1):
        for b in (0, 1):
            edges.append(((a, b, 0), "Z"))

    lines = []
    for start, label in edges:
        sx, sy = vertex(*start)
        ux, uy = unit(label, drawn)
        lines.append((sx, sy, sx + side * ux, sy - side * uy))
    return lines


class TestAngleMaths:
    def test_direction_is_measured_as_the_viewer_sees_it(self):
        """Image y grows downward; a line going up-right must read as a positive angle."""
        assert direction_deg(0, 100, 100, 0) == pytest.approx(45.0, abs=0.01)

    def test_direction_is_undirected(self):
        """The same line drawn right-to-left is the same line."""
        assert direction_deg(0, 100, 100, 0) == pytest.approx(direction_deg(100, 0, 0, 100), abs=0.01)

    def test_gap_wraps_around_180(self):
        assert angle_gap_deg(179.0, 1.0) == pytest.approx(2.0, abs=0.01)

    def test_mean_direction_wraps_around_180(self):
        """Averaging 179 and 1 naively gives 90 — a set of near-horizontal lines called vertical."""
        assert mean_direction_deg([179.0, 1.0]) % 180.0 == pytest.approx(0.0, abs=0.01)

    def test_mean_direction_of_a_single_family(self):
        assert mean_direction_deg([29.0, 30.0, 31.0]) == pytest.approx(30.0, abs=0.01)


class TestGoldenCases:
    def test_perfect_isometric_cube_measures_zero(self):
        result = analyze_axonometric_from_lines(isometric_cube_lines(0.0), 800, 600, system="isometric")
        assert result.avg_axis_error_deg == pytest.approx(0.0, abs=0.05)
        assert result.axes_supported == 3
        for axis in result.axes:
            assert axis.systematic_error_deg == pytest.approx(0.0, abs=0.05)

    def test_injected_six_degrees_comes_back_as_six_degrees(self):
        """The whole argument for this mode: the reference is a constant, so nothing is estimated."""
        result = analyze_axonometric_from_lines(
            isometric_cube_lines(6.0, perturbed="X"), 800, 600, system="isometric"
        )
        by_label = {a.label: a for a in result.axes}
        assert by_label["X"].systematic_error_deg == pytest.approx(6.0, abs=0.05)
        assert by_label["Y"].systematic_error_deg == pytest.approx(0.0, abs=0.05)
        assert by_label["Z"].systematic_error_deg == pytest.approx(0.0, abs=0.05)

    def test_a_worse_drawing_measures_worse(self):
        good = analyze_axonometric_from_lines(isometric_cube_lines(0.0), 800, 600)
        bad = analyze_axonometric_from_lines(isometric_cube_lines(9.0), 800, 600)
        assert bad.avg_axis_error_deg > good.avg_axis_error_deg

    def test_the_error_is_reported_on_the_axis_that_carries_it(self):
        """A tilted Y family must not be reported against X."""
        result = analyze_axonometric_from_lines(
            isometric_cube_lines(7.0, perturbed="Y"), 800, 600, system="isometric"
        )
        by_label = {a.label: a for a in result.axes}
        assert by_label["Y"].systematic_error_deg == pytest.approx(7.0, abs=0.05)
        assert abs(by_label["X"].systematic_error_deg) < 0.1

    def test_end_to_end_through_the_detector(self):
        """Same assertion, but through Canny and Hough rather than a hand-built line list."""
        # Resolved from this file, not from the working directory: a path that only works when
        # pytest is invoked from one folder turns into a silent skip everywhere else.
        sample = Path(__file__).resolve().parents[2] / "demo" / "dataset" / "07_isometric_error_6deg.png"
        image = cv2.imread(str(sample))
        if image is None:
            pytest.skip("calibration dataset not generated")
        result = analyze_axonometric(image, system="isometric", generate_overlay_image=False)
        by_label = {a.label: a for a in result.axes}
        assert by_label["X"].systematic_error_deg == pytest.approx(6.0, abs=0.3)


class TestHonesty:
    def test_nothing_is_silently_dropped(self):
        """Every detected segment appears in the output and in the average."""
        lines = isometric_cube_lines(0.0) + [segment_at(75.0)]  # one edge belonging to no axis
        result = analyze_axonometric_from_lines(lines, 800, 600)
        assert result.line_count == len(lines)
        assert len(result.lines) == len(lines)

    def test_a_grossly_wrong_edge_is_flagged_but_still_counted(self):
        """
        Excluding it would pull the average down exactly when the drawing got worse — the one
        direction an error metric must never move by itself.
        """
        clean = analyze_axonometric_from_lines(isometric_cube_lines(0.0), 800, 600)
        with_bad = analyze_axonometric_from_lines(
            isometric_cube_lines(0.0) + [segment_at(75.0)], 800, 600
        )
        assert with_bad.off_axis_line_count == 1
        assert with_bad.avg_axis_error_deg > clean.avg_axis_error_deg

    def test_an_empty_page_invents_no_axes(self):
        result = analyze_axonometric_from_lines([], 800, 600)
        assert result.confidence == 0.0
        assert result.confidence_low is True
        assert result.axes_supported == 0
        assert result.avg_axis_error_deg == 0.0

    def test_a_blank_image_through_the_detector_invents_nothing(self):
        blank = np.ones((600, 800, 3), dtype=np.uint8) * 255
        result = analyze_axonometric(blank, generate_overlay_image=False)
        assert result.confidence_low is True
        assert result.axes_supported < 2


class TestSystems:
    def test_cavalier_receding_angle_is_overridable(self):
        axes = {a.label: a.nominal_angle_deg for a in resolve_axes("cavalier", receding_angle_deg=30.0)}
        assert axes["Y"] == pytest.approx(30.0)
        assert axes["X"] == pytest.approx(0.0)
        assert axes["Z"] == pytest.approx(90.0)

    def test_overriding_cavalier_does_not_mutate_the_shared_table(self):
        """A per-request override that edited the module constant would poison every later call."""
        resolve_axes("cavalier", receding_angle_deg=30.0)
        assert resolve_axes("cavalier")[1].nominal_angle_deg == pytest.approx(45.0)

    def test_an_unknown_system_is_refused_rather_than_guessed(self):
        with pytest.raises(ValueError, match="Unknown axonometric system"):
            resolve_axes("trimetric-improvised")

    def test_the_same_drawing_measures_differently_under_different_systems(self):
        """An isometric cube is not a cavalier one, and the engine must not pretend otherwise."""
        lines = isometric_cube_lines(0.0)
        iso = analyze_axonometric_from_lines(lines, 800, 600, system="isometric")
        cav = analyze_axonometric_from_lines(lines, 800, 600, system="cavalier")
        assert cav.avg_axis_error_deg > iso.avg_axis_error_deg


class TestValidatorIsSubjectAgnostic:
    def _critique(self, value: float) -> CritiqueOutput:
        return CritiqueOutput(
            student_name="Test",
            level="beginner",
            headline="h",
            measured_findings=[
                MeasuredFindingItem(
                    metric_name="average_axis_error",
                    measured_value=value,
                    unit="degrees",
                    pedagogical_context="c",
                )
            ],
            qualitative_observations=[],
            pedagogical_summary={"strengths": ["s"], "focus_area": "f", "encouragement": "e"},
            next_exercise={"title": "t", "description": "d", "target_metric": "m", "difficulty": "beginner"},
        )

    def test_a_real_axonometric_figure_passes(self):
        result = analyze_axonometric_from_lines(isometric_cube_lines(6.0), 800, 600)
        ok, errors = validate_critique_measurements(
            self._critique(result.avg_axis_error_deg), result, had_image=True
        )
        assert ok, errors

    def test_an_invented_axonometric_figure_is_rejected(self):
        """The gate that guards perspective must guard this too, or it guards nothing."""
        result = analyze_axonometric_from_lines(isometric_cube_lines(6.0), 800, 600)
        ok, errors = validate_critique_measurements(self._critique(41.7), result, had_image=True)
        assert not ok
        assert any("Hallucinated" in e for e in errors)


class TestCritiqueRequestShape:
    def _axo(self):
        return analyze_axonometric_from_lines(isometric_cube_lines(0.0), 800, 600)

    def _geom(self):
        return GeometryAnalysisResult(
            k_requested=1,
            k_detected=1,
            avg_convergence_error_deg=0.8,
            max_convergence_error_deg=2.5,
            line_count=16,
            confidence=1.0,
            image_width=800,
            image_height=600,
        )

    def test_one_analysis_is_accepted(self):
        req = CritiqueRequest(axonometry=self._axo(), student=StudentProfile(student_id="s", name="S"))
        assert req.projection == "axonometric"
        assert req.analysis is req.axonometry

    def test_neither_is_refused(self):
        with pytest.raises(ValidationError, match="exactly one"):
            CritiqueRequest(student=StudentProfile(student_id="s", name="S"))

    def test_both_is_refused(self):
        """Two analyses would whitelist the union of both number sets."""
        with pytest.raises(ValidationError, match="exactly one"):
            CritiqueRequest(
                geometry=self._geom(),
                axonometry=self._axo(),
                student=StudentProfile(student_id="s", name="S"),
            )
