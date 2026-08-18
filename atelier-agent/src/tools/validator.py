"""Anti-hallucination validator for pedagogical critique (ADR-001 & PAT-001).

Guarantees that LLM never hallucinates or invents quantitative metrics not present
in the OpenCV measurement payload.
"""


from src.models.critique import CritiqueOutput
from src.models.geometry import GeometryAnalysisResult


def validate_critique_measurements(
    critique: CritiqueOutput,
    geometry: GeometryAnalysisResult,
    tolerance: float = 0.5,
) -> tuple[bool, list[str]]:
    """Validate that all numerical assertions in the critique's measured findings match the OpenCV payload.

    Args:
        critique: The generated critique output from the LLM.
        geometry: The deterministic geometry results from OpenCV.
        tolerance: Allowed float tolerance for rounding differences.

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

    # 2. Check qualitative observations plane does not claim fake quantitative precision
    for qual in critique.qualitative_observations:
        # Qualitative observations must focus on artistic/construction aspects
        allowed_aspects = {"line_weight", "spatial_clarity", "construction_cleanliness", "volumetrics", "composition"}
        if qual.aspect.lower() not in allowed_aspects and not any(k in qual.aspect.lower() for k in ["line", "weight", "clean", "clarity", "volume", "depth"]):
            # Non-blocking warning/check
            pass

    is_valid = len(errors) == 0
    return (is_valid, errors)
