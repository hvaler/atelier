"""Pydantic data models for deterministic geometry analysis (ADR-001)."""


from pydantic import BaseModel, Field


class Point2D(BaseModel):
    x: float = Field(..., description="X coordinate in image pixel space")
    y: float = Field(..., description="Y coordinate in image pixel space")
    norm_x: float | None = Field(None, description="Normalized X coordinate in [0, 1]")
    norm_y: float | None = Field(None, description="Normalized Y coordinate in [0, 1]")


class LineSegment(BaseModel):
    id: int = Field(..., description="Unique line identifier")
    start: Point2D
    end: Point2D
    angle_deg: float = Field(..., description="Segment angle in degrees [-180, 180]")
    length_px: float = Field(..., description="Length of the segment in pixels")
    vp_index: int | None = Field(None, description="Assigned vanishing point index (0, 1, ...)")
    convergence_error_deg: float | None = Field(
        None, description="Angular deviation in degrees from theoretical vanishing point"
    )


class VanishingPoint(BaseModel):
    index: int = Field(..., description="Vanishing point index (0 for F1, 1 for F2)")
    label: str = Field(..., description="Label, e.g. F1, F2, or VP")
    point: Point2D
    supporting_lines: int = Field(..., description="Number of lines converging to this point")
    avg_error_deg: float = Field(..., description="Average convergence error for supporting lines in degrees")


class HorizonLine(BaseModel):
    start: Point2D = Field(..., description="Left intersection with canvas border")
    end: Point2D = Field(..., description="Right intersection with canvas border")
    slope: float = Field(..., description="Horizon slope")
    intercept: float = Field(..., description="Horizon Y-intercept")
    angle_deg: float = Field(..., description="Tilt angle in degrees relative to horizontal")


class GeometryAnalysisRequest(BaseModel):
    image_base64: str | None = Field(None, description="Base64-encoded image")
    k_points: int = Field(2, ge=1, le=2, description="Perspective mode: 1 for 1-point (beginner), 2 for 2-point (advanced)")
    min_confidence_threshold: float = Field(0.35, description="Threshold below which analysis declares low confidence")
    generate_overlay: bool = Field(True, description="Whether to generate annotated visualization overlay")


class GeometryAnalysisResult(BaseModel):
    """Deterministic geometry measurements produced exclusively by OpenCV (ADR-001)."""

    k_requested: int = Field(..., description="Perspective mode requested (1 or 2)")
    k_detected: int = Field(..., description="Number of vanishing points successfully estimated")
    vanishing_points: list[VanishingPoint] = Field(default_factory=list, description="Estimated vanishing points")
    horizon_line: HorizonLine | None = Field(None, description="Estimated eye-level horizon line")
    avg_convergence_error_deg: float = Field(..., description="Average angular convergence error across all analyzed lines in degrees")
    max_convergence_error_deg: float = Field(..., description="Maximum angular convergence error observed in degrees")
    line_count: int = Field(..., description="Total line segments extracted and analyzed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score in [0.0, 1.0]")
    confidence_low: bool = Field(False, description="True if confidence is below threshold; agent must ask for clearer photo")
    image_width: int
    image_height: int
    lines: list[LineSegment] = Field(default_factory=list, description="Extracted line segments with individual metrics")
    overlay_image_base64: str | None = Field(None, description="Base64-encoded PNG with visual perspective overlay")

    def measured_values(self) -> set[float]:
        """
        Every number this analysis produced, for the anti-hallucination whitelist.

        The validator used to reach into these fields by name, which meant it only guarded conic
        perspective: a second projection system would have arrived carrying figures that nothing
        was checking, and the failure would have been silent because the critique would still
        look validated. Each analysis now declares its own numbers instead.
        """
        values: set[float] = {
            round(self.avg_convergence_error_deg, 2),
            round(self.max_convergence_error_deg, 2),
            float(self.k_requested),
            float(self.k_detected),
            float(self.line_count),
            round(self.confidence, 2),
            round(self.confidence * 100, 1),
        }
        for vp in self.vanishing_points:
            values.add(round(vp.avg_error_deg, 2))
            values.add(float(vp.supporting_lines))
            values.add(round(vp.point.x, 1))
            values.add(round(vp.point.y, 1))
        if self.horizon_line is not None:
            values.add(round(self.horizon_line.angle_deg, 2))
        return values
