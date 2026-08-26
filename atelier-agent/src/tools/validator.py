"""Anti-hallucination validator for pedagogical critique (ADR-001 & PAT-001).

Guarantees that the LLM never invents a quantitative metric absent from the OpenCV payload, and
that Plane B never describes a drawing the model was not shown.
"""

import re
from typing import Protocol

from src.models.critique import CritiqueOutput


class MeasuredAnalysis(Protocol):
    """Anything the engine produced that can say which numbers it measured.

    Deliberately a protocol and not a base class: `GeometryAnalysisResult` and
    `AxonometricAnalysisResult` have genuinely different shapes — one has vanishing points, the
    other has axes — and forcing a shared parent would push perspective vocabulary into a system
    that has no vanishing point. What they share is a promise, not a structure.
    """

    def measured_values(self) -> set[float]: ...

#: Any figure in degrees appearing in Plane B prose. Plane B is the qualitative plane; every
#: number in this system belongs to Plane A, where it can be checked against OpenCV.
# Spanish is listed alongside English because the critique is written in the student's language:
# a gate that only recognises "degrees" would wave through "4,2 grados" and quietly stop being a
# gate the moment the interface was translated.
#: Pixels are here because the orthographic system reports its error in them, not in degrees.
#: A gate that only knew about degrees let "the plan is 18 px out" through Plane B, which is a
#: measurement wearing the clothes of an observation.
_MEASUREMENT_IN_PROSE = re.compile(
    r"\d+(?:[.,]\d+)?\s*"
    r"(?:°|deg\b|degs\b|degrees\b|grado\b|grados\b"
    r"|px\b|pixel\b|pixels\b|p[íi]xel\b|p[íi]xeles\b)",
    re.IGNORECASE,
)


def validate_critique_measurements(
    critique: CritiqueOutput,
    geometry: MeasuredAnalysis,
    tolerance: float = 0.5,
    had_image: bool = True,
) -> tuple[bool, list[str]]:
    """Validate that the critique only asserts things it is entitled to assert.

    Args:
        critique: The generated critique output from the LLM.
        geometry: The deterministic geometry results from OpenCV.
        tolerance: How far a cited number may sit from a measured one and still be accepted,
            in degrees. Defaults to 0.5 so the function stays usable on its own; production
            passes `settings.validator_tolerance_deg`, which reads `VALIDATOR_TOLERANCE_DEG`.
            0.0 demands an exact match.
        had_image: Whether the drawing was actually sent to the model. When it was not, Plane B
            must be empty: an observation about line weight is not an opinion, it is a claim
            about a picture, and a model that was shown no picture cannot make it.

    Returns:
        (is_valid, list_of_error_messages)
    """
    errors: list[str] = []

    # The whitelist is whatever the analysis says it measured. Asking the analysis rather than
    # reading its fields is what lets a second projection system be added without quietly
    # arriving unguarded.
    valid_numbers = geometry.measured_values()

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
        match = _MEASUREMENT_IN_PROSE.search(qual.observation)
        if match:
            errors.append(
                f"Plane B observation '{qual.aspect}' states a measurement ({match.group(0).strip()}). "
                "Numbers belong to Plane A, where they are checked against OpenCV."
            )

    is_valid = len(errors) == 0
    return (is_valid, errors)
