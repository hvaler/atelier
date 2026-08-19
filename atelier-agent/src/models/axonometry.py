"""
Pydantic models for axonometric (parallel-projection) analysis.

Separate from `models.geometry` on purpose. An axonometric drawing has **no vanishing point and
no horizon** — parallel edges stay parallel — so reusing `GeometryAnalysisResult` would mean
carrying two always-empty fields and a `convergence_error_deg` that measures no convergence.
Naming a measurement after something it does not measure is the failure this project exists to
avoid, so the two systems get two shapes and share only `Point2D`.

What they *do* share is the contract: everything here is produced by OpenCV, and
`measured_values()` is the whitelist the anti-hallucination validator checks the model against.
"""

from typing import Literal

from pydantic import BaseModel, Field

from src.models.geometry import Point2D

#: The projection systems the engine can measure against.
AxonometricSystemName = Literal["isometric", "dimetric", "cavalier"]


class AxisSpec(BaseModel):
    """One projected spatial axis and the direction it is *supposed* to run in."""

    label: str = Field(..., description="Axis label: X, Y or Z")
    nominal_angle_deg: float = Field(
        ...,
        description=(
            "Where this axis must point, in drawing space: degrees anticlockwise from horizontal "
            "as the viewer sees the page, folded to [0, 180). This is a constant of the "
            "projection system, not something estimated from the drawing."
        ),
    )


class AxisMeasurement(BaseModel):
    """What the drawing actually did with one axis."""

    index: int
    label: str
    nominal_angle_deg: float = Field(..., description="Where the axis should point, by definition of the system")
    measured_angle_deg: float | None = Field(
        None,
        description=(
            "Mean direction of the segments assigned to this axis, or null when none were. "
            "Averaged as a doubled angle, because 179 deg and 1 deg are two degrees apart, not 178."
        ),
    )
    systematic_error_deg: float | None = Field(
        None,
        description=(
            "measured_angle_deg minus nominal_angle_deg. A student who drew every receding edge "
            "at 25 deg instead of 30 has a small per-line error and a large systematic one; the "
            "two say different things and are reported separately."
        ),
    )
    supporting_lines: int = Field(0, description="Segments assigned to this axis")
    avg_error_deg: float = Field(0.0, description="Mean deviation of those segments from the nominal direction")
    max_error_deg: float = Field(0.0, description="Worst single deviation among them")


class AxisSegment(BaseModel):
    """A detected segment and how far it misses the axis it belongs to."""

    id: int
    start: Point2D
    end: Point2D
    angle_deg: float = Field(..., description="Direction in drawing space, folded to [0, 180)")
    length_px: float
    axis_index: int = Field(..., description="Index of the nearest axis in the system's axis list")
    axis_error_deg: float = Field(..., description="Angular deviation from that axis, in degrees")
    off_axis: bool = Field(
        False,
        description=(
            "True when the deviation exceeds the gross threshold. Reported, never dropped: a "
            "segment excluded for being too wrong would lower the average error, which is the "
            "one direction an error metric must never be allowed to move by itself."
        ),
    )


class AxonometricAnalysisRequest(BaseModel):
    image_base64: str | None = Field(None, description="Base64-encoded image")
    system: AxonometricSystemName = Field("isometric", description="Projection system to measure against")
    receding_angle_deg: float | None = Field(
        None,
        ge=0.0,
        lt=180.0,
        description=(
            "Cavalier only: the angle of the receding Y axis. 45 deg is the usual convention; "
            "30 and 60 are also taught. Ignored by the other systems, whose axes are fixed."
        ),
    )
    off_axis_threshold_deg: float = Field(
        10.0, gt=0.0, description="Deviation above which a segment is flagged as off-axis"
    )
    min_confidence_threshold: float = Field(0.35, description="Below this, the analysis declares itself unreliable")
    generate_overlay: bool = Field(True, description="Whether to render the annotated overlay")


class AxonometricAnalysisResult(BaseModel):
    """Deterministic axonometric measurements produced exclusively by OpenCV (ADR-001)."""

    system: str = Field(..., description="Projection system measured against")
    axes: list[AxisMeasurement] = Field(default_factory=list)
    avg_axis_error_deg: float = Field(..., description="Mean deviation across every analysed segment")
    max_axis_error_deg: float = Field(..., description="Worst single deviation observed")
    parallelism_error_deg: float = Field(
        0.0,
        description=(
            "The widest spread within any one axis family. In a parallel projection every edge of "
            "a family must stay parallel to the others, so this is the invariant that replaces "
            "convergence: it is what a vanishing point would be if it existed."
        ),
    )
    off_axis_line_count: int = Field(0, description="Segments beyond the gross threshold")
    line_count: int = Field(..., description="Total segments extracted and analysed")
    axes_supported: int = Field(0, description="How many of the system's axes had at least one segment")
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_low: bool = Field(False)
    image_width: int
    image_height: int
    lines: list[AxisSegment] = Field(default_factory=list)
    overlay_image_base64: str | None = None

    def measured_values(self) -> set[float]:
        """
        Every number this analysis produced, for the anti-hallucination whitelist.

        The validator asks the analysis what it measured rather than reaching into named fields,
        so a new projection system does not silently arrive with figures nothing is checking.
        """
        values: set[float] = {
            round(self.avg_axis_error_deg, 2),
            round(self.max_axis_error_deg, 2),
            round(self.parallelism_error_deg, 2),
            float(self.line_count),
            float(self.off_axis_line_count),
            float(self.axes_supported),
            round(self.confidence, 2),
            round(self.confidence * 100, 1),
        }
        for axis in self.axes:
            values.add(round(axis.nominal_angle_deg, 2))
            values.add(float(axis.supporting_lines))
            values.add(round(axis.avg_error_deg, 2))
            values.add(round(axis.max_error_deg, 2))
            if axis.measured_angle_deg is not None:
                values.add(round(axis.measured_angle_deg, 2))
            if axis.systematic_error_deg is not None:
                values.add(round(axis.systematic_error_deg, 2))
                values.add(round(abs(axis.systematic_error_deg), 2))
        return values
