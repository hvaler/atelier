"""
Pydantic models for orthographic (Monge / sistema diédrico) analysis.

The third measurement shape, and the third kind of reference. The project now has one of each:

- **Conic perspective** infers its reference. RANSAC estimates a vanishing point from the
  student's own lines, so a consistently wrong drawing yields a vanishing point that agrees with
  it. Weakest of the three, and `docs/PEDAGOGY.md` says so.
- **Orthographic** reads its reference off the page. The ground line is a line the student
  actually drew, so nothing is guessed — but if they drew it crooked, everything is measured
  against a crooked reference, which is why its tilt is reported as a measurement in its own right.
- **Axonometric** is handed its reference. The axes are constants of the projection system.

What is measured here is correspondence, not convergence. Two views of the same object, folded
into one page about the ground line: a point's plan and elevation must sit on the same line
perpendicular to it. That is the invariant, and a vertex in one view with no counterpart in the
other is the error an instructor circles in red.
"""

from pydantic import BaseModel, Field

from src.models.geometry import Point2D


class GroundLine(BaseModel):
    """The línea de tierra: the fold between the two projection planes, as drawn."""

    start: Point2D
    end: Point2D
    angle_deg: float = Field(
        ...,
        description=(
            "Tilt away from horizontal, in degrees. Reported rather than corrected: every other "
            "figure here is measured against this line, so if it is crooked the reader has to be "
            "told before they trust the rest."
        ),
    )
    length_px: float
    source: str = Field(
        "detected",
        description="'detected' when a ground line was found in the drawing, 'assumed' when one had to be placed.",
    )


class ReferenceLineMeasurement(BaseModel):
    """A línea de referencia: the segment carrying a point between the two views."""

    id: int
    start: Point2D
    end: Point2D
    perpendicularity_error_deg: float = Field(
        ..., description="Deviation from a true right angle to the ground line, in degrees"
    )
    crosses_ground_line: bool = Field(
        ...,
        description=(
            "Whether it actually spans both views. A reference line that stops at the ground line "
            "carries nothing across it, which is a different mistake from drawing it at a slant."
        ),
    )


class Correspondence(BaseModel):
    """One abscissa, and whether both views agree about it."""

    elevation_x: float | None = Field(None, description="Vertex abscissa in the elevation, if any")
    plan_x: float | None = Field(None, description="Vertex abscissa in the plan, if any")
    error_px: float | None = Field(
        None, description="Horizontal gap between the two, in pixels; null when one side is missing"
    )
    error_pct: float | None = Field(
        None,
        description=(
            "The same gap as a percentage of the drawing width. Pixels depend on how the page was "
            "photographed; this does not, and it is the figure worth comparing between drawings."
        ),
    )
    matched: bool = Field(..., description="Whether both views placed a vertex at this abscissa")


class DihedralAnalysisRequest(BaseModel):
    image_base64: str | None = Field(None, description="Base64-encoded image")
    correspondence_tolerance_pct: float = Field(
        1.5,
        gt=0.0,
        description=(
            "How far apart two abscissae may sit, as a percentage of drawing width, and still be "
            "read as the same vertex seen twice. Above this they are reported as a mismatch."
        ),
    )
    min_confidence_threshold: float = Field(0.35)
    generate_overlay: bool = Field(True)


class DihedralAnalysisResult(BaseModel):
    """Deterministic orthographic measurements produced exclusively by OpenCV (ADR-001)."""

    ground_line: GroundLine | None = Field(
        None, description="Null when no ground line could be found, in which case nothing else was measured"
    )
    reference_lines: list[ReferenceLineMeasurement] = Field(default_factory=list)
    correspondences: list[Correspondence] = Field(default_factory=list)

    systematic_offset_px: float | None = Field(
        None,
        description=(
            "How far the plan sits sideways from the elevation as a whole, in pixels, signed. A "
            "uniform shift is one mistake — the plan drawn in the wrong place — not one mistake "
            "per vertex, and it is removed before per-vertex matching so that what remains is "
            "genuinely unmatched rather than merely displaced. Null when the two views share too "
            "few vertices to establish an offset."
        ),
    )
    systematic_offset_pct: float | None = Field(
        None, description="The same offset as a percentage of drawing width"
    )

    avg_perpendicularity_error_deg: float = Field(0.0)
    max_perpendicularity_error_deg: float = Field(0.0)

    # Null, never zero, when nothing matched.
    #
    # These were plain floats defaulting to 0.0, and the golden case caught what that costs: a
    # plate whose plan was shifted far enough that no vertex paired at all reported an average
    # correspondence error of 0.00, which reads as perfect alignment. A worse drawing produced a
    # better number. The mean of an empty set is not zero, it is undefined, and saying so is the
    # difference between a measurement and a lie.
    avg_correspondence_error_px: float | None = Field(None)
    max_correspondence_error_px: float | None = Field(None)
    avg_correspondence_error_pct: float | None = Field(None)
    max_correspondence_error_pct: float | None = Field(None)
    matched_vertex_count: int = Field(0, description="Vertices the two views agreed on")

    unmatched_in_elevation: int = Field(
        0, description="Vertices in the elevation with no counterpart below the ground line"
    )
    unmatched_in_plan: int = Field(
        0, description="Vertices in the plan with no counterpart above the ground line"
    )

    elevation_line_count: int = Field(0, description="Segments above the ground line")
    plan_line_count: int = Field(0, description="Segments below the ground line")
    line_count: int = Field(0, description="Total segments extracted and analysed")
    views_detected: int = Field(0, description="How many of the two views carried any construction")

    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_low: bool = Field(False)
    image_width: int
    image_height: int
    overlay_image_base64: str | None = None

    def measured_values(self) -> set[float]:
        """Every number this analysis produced, for the anti-hallucination whitelist."""
        values: set[float] = {
            round(self.avg_perpendicularity_error_deg, 2),
            round(self.max_perpendicularity_error_deg, 2),
            float(self.matched_vertex_count),
            float(self.unmatched_in_elevation),
            float(self.unmatched_in_plan),
            float(self.elevation_line_count),
            float(self.plan_line_count),
            float(self.line_count),
            float(self.views_detected),
            float(len(self.reference_lines)),
            float(len(self.correspondences)),
            round(self.confidence, 2),
            round(self.confidence * 100, 1),
        }
        for optional in (
            self.avg_correspondence_error_px,
            self.max_correspondence_error_px,
            self.avg_correspondence_error_pct,
            self.max_correspondence_error_pct,
            self.systematic_offset_px,
            self.systematic_offset_pct,
        ):
            if optional is not None:
                values.add(round(optional, 2))
                values.add(round(abs(optional), 2))

        if self.ground_line is not None:
            values.add(round(self.ground_line.angle_deg, 2))
            values.add(round(self.ground_line.length_px, 1))
        for ref in self.reference_lines:
            values.add(round(ref.perpendicularity_error_deg, 2))
        for corr in self.correspondences:
            if corr.error_px is not None:
                values.add(round(corr.error_px, 2))
            if corr.error_pct is not None:
                values.add(round(corr.error_pct, 2))
        return values
