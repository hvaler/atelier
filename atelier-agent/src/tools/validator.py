"""Anti-hallucination validator for pedagogical critique (ADR-001 & PAT-001).

Guarantees that the LLM never invents a quantitative metric absent from the OpenCV payload, and
that Plane B never describes a drawing the model was not shown.
"""

import re

from src.models.critique import CritiqueOutput
from src.models.geometry import GeometryAnalysisResult

#: Any figure in degrees appearing in Plane B prose. Plane B is the qualitative plane; every
#: number in this system belongs to Plane A, where it can be checked against OpenCV.
_DEGREES_IN_PROSE = re.compile(r"\d+(?:\.\d+)?\s*(?:°|deg\b|degs\b|degrees\b)", re.IGNORECASE)


def validate_critique_measurements(
    critique: CritiqueOutput,
    geometry: GeometryAnalysisResult,
    tolerance: float = 0.5,
    had_image: bool = True,
) -> tuple[bool, list[str]]:
    """Validate that the critique only asserts things it is entitled to assert.

    Args:
        critique: The generated critique output from the LLM.
        geometry: The deterministic geometry results from OpenCV.
        tolerance: Allowed float tolerance for rounding differences.
        had_image: Whether the drawing was actually sent to the model. When it was not, Plane B
            must be empty: an observation about line weight is not an opinion, it is a claim
            about a picture, and a model that was shown no picture cannot make it.

    Returns:
        (is_valid, list_of_error_messages)
    """
    errors: list[str] = []

    # Valid set of allowable measured numerical values
    valid_numbers = {
        round(geometry.avg_convergence_error_deg, 2),
        round(geometry.max_convergence_error_deg, 2),
        float(geometry.k_requested),
        float(geometry.k_detected),
        float(geometry.line_count),
        round(geometry.confidence, 2),
        round(geometry.confidence * 100, 1),
    }

    for vp in geometry.vanishing_points:
        valid_numbers.add(round(vp.avg_error_deg, 2))
        valid_numbers.add(float(vp.supporting_lines))
        valid_numbers.add(round(vp.point.x, 1))
        valid_numbers.add(round(vp.point.y, 1))

    if geometry.horizon_line is not None:
        valid_numbers.add(round(geometry.horizon_line.angle_deg, 2))

    # 1. Validate each MeasuredFindingItem
    if not critique.measured_findings:
        errors.append("Critique must contain at least one measured finding item in Plane A.")

    for item in critique.measured_findings:
        val = item.measured_value
        # Check if the cited value is close to any valid measured number
        is_matched = any(abs(val - target) <= tolerance for target in valid_numbers)
        if not is_matched:
            errors.append(
                f"Hallucinated measurement detected in '{item.metric_name}': cited {val} {item.unit}, "
                f"which does not exist in OpenCV payload (allowed: {sorted(valid_numbers)})."
            )

    # 2. Plane B. This branch used to end in a literal `pass`, so the qualitative plane was
    #    unguarded — which is where the invented prose actually lived.
    if not had_image and critique.qualitative_observations:
        errors.append(
            f"Plane B carries {len(critique.qualitative_observations)} observation(s) about a "
            "drawing that was never sent to the model. Without the image these describe nothing."
        )

    for qual in critique.qualitative_observations:
        match = _DEGREES_IN_PROSE.search(qual.observation)
        if match:
            errors.append(
                f"Plane B observation '{qual.aspect}' states a measurement ({match.group(0).strip()}). "
                "Numbers belong to Plane A, where they are checked against OpenCV."
            )

    is_valid = len(errors) == 0
    return (is_valid, errors)
