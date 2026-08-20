using System.Text.Json.Serialization;

namespace Atelier.Web.Models;

public class StudentProfileDto
{
    [JsonPropertyName("student_id")]
    public string StudentId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("level")]
    public string Level { get; set; } = "beginner"; // "beginner" or "advanced"

    [JsonPropertyName("tone_preference")]
    public string? TonePreference { get; set; } = "encouraging";

    [JsonPropertyName("recurring_issues")]
    public List<string> RecurringIssues { get; set; } = [];
}

public class Point2DDto
{
    [JsonPropertyName("x")]
    public double X { get; set; }

    [JsonPropertyName("y")]
    public double Y { get; set; }

    [JsonPropertyName("norm_x")]
    public double NormX { get; set; }

    [JsonPropertyName("norm_y")]
    public double NormY { get; set; }
}

public class LineSegmentDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("start")]
    public Point2DDto Start { get; set; } = new();

    [JsonPropertyName("end")]
    public Point2DDto End { get; set; } = new();

    [JsonPropertyName("angle_deg")]
    public double AngleDeg { get; set; }

    [JsonPropertyName("length_px")]
    public double LengthPx { get; set; }

    [JsonPropertyName("vp_index")]
    public int? VpIndex { get; set; }

    /// <summary>
    /// How far this line misses the vanishing point, in degrees — or null when the line is
    /// structural and was never expected to converge.
    ///
    /// Nullable because the agent's field always was: verticals, and the horizontals of a
    /// one-point front face, carry no convergence error because converging is not something
    /// they were ever supposed to do. This DTO declared it non-nullable, which was harmless
    /// only while the engine wrongly measured every line — the moment it stopped, the whole
    /// response failed to deserialise and the page reported the agent as unreachable.
    /// </summary>
    [JsonPropertyName("convergence_error_deg")]
    public double? ConvergenceErrorDeg { get; set; }
}

public class VanishingPointDto
{
    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("label")]
    public string Label { get; set; } = "VP";

    [JsonPropertyName("point")]
    public Point2DDto Point { get; set; } = new();

    [JsonPropertyName("supporting_lines")]
    public int SupportingLines { get; set; }

    [JsonPropertyName("avg_error_deg")]
    public double AvgErrorDeg { get; set; }
}

public class HorizonLineDto
{
    [JsonPropertyName("start")]
    public Point2DDto Start { get; set; } = new();

    [JsonPropertyName("end")]
    public Point2DDto End { get; set; } = new();

    [JsonPropertyName("slope")]
    public double Slope { get; set; }

    [JsonPropertyName("intercept")]
    public double Intercept { get; set; }

    [JsonPropertyName("angle_deg")]
    public double AngleDeg { get; set; }
}

public class GeometryAnalysisResultDto
{
    [JsonPropertyName("k_requested")]
    public int KRequested { get; set; } = 1;

    [JsonPropertyName("k_detected")]
    public int KDetected { get; set; }

    [JsonPropertyName("vanishing_points")]
    public List<VanishingPointDto> VanishingPoints { get; set; } = [];

    [JsonPropertyName("horizon_line")]
    public HorizonLineDto? HorizonLine { get; set; }

    [JsonPropertyName("avg_convergence_error_deg")]
    public double AvgConvergenceErrorDeg { get; set; }

    [JsonPropertyName("max_convergence_error_deg")]
    public double MaxConvergenceErrorDeg { get; set; }

    [JsonPropertyName("line_count")]
    public int LineCount { get; set; }

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }

    [JsonPropertyName("confidence_low")]
    public bool ConfidenceLow { get; set; }

    [JsonPropertyName("image_width")]
    public int ImageWidth { get; set; }

    [JsonPropertyName("image_height")]
    public int ImageHeight { get; set; }

    [JsonPropertyName("lines")]
    public List<LineSegmentDto> Lines { get; set; } = [];

    [JsonPropertyName("overlay_image_base64")]
    public string? OverlayImageBase64 { get; set; }
}

/// <summary>
/// One projected spatial axis: where it must point, and what this drawing did with it.
/// </summary>
public class AxisMeasurementDto
{
    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("label")]
    public string Label { get; set; } = string.Empty;

    [JsonPropertyName("nominal_angle_deg")]
    public double NominalAngleDeg { get; set; }

    /// <summary>Mean direction of the edges assigned to this axis; null when none were.</summary>
    [JsonPropertyName("measured_angle_deg")]
    public double? MeasuredAngleDeg { get; set; }

    /// <summary>
    /// Measured minus nominal. This is the figure with teaching value: a whole family off by the
    /// same amount is a set square placed wrong, which is a different correction from an unsteady
    /// hand, and the two are indistinguishable if only the per-line average is shown.
    /// </summary>
    [JsonPropertyName("systematic_error_deg")]
    public double? SystematicErrorDeg { get; set; }

    [JsonPropertyName("supporting_lines")]
    public int SupportingLines { get; set; }

    [JsonPropertyName("avg_error_deg")]
    public double AvgErrorDeg { get; set; }

    [JsonPropertyName("max_error_deg")]
    public double MaxErrorDeg { get; set; }
}

public class AxisSegmentDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("start")]
    public Point2DDto Start { get; set; } = new();

    [JsonPropertyName("end")]
    public Point2DDto End { get; set; } = new();

    [JsonPropertyName("angle_deg")]
    public double AngleDeg { get; set; }

    [JsonPropertyName("length_px")]
    public double LengthPx { get; set; }

    [JsonPropertyName("axis_index")]
    public int AxisIndex { get; set; }

    [JsonPropertyName("axis_error_deg")]
    public double AxisErrorDeg { get; set; }

    [JsonPropertyName("off_axis")]
    public bool OffAxis { get; set; }
}

/// <summary>
/// Measurements of a parallel projection. A separate shape from <see cref="GeometryAnalysisResultDto"/>
/// because there is no vanishing point and no horizon in an axonometric drawing: reusing that type
/// would mean two permanently null fields and a convergence error that measures no convergence.
/// </summary>
public class AxonometricAnalysisResultDto
{
    [JsonPropertyName("system")]
    public string System { get; set; } = "isometric";

    [JsonPropertyName("axes")]
    public List<AxisMeasurementDto> Axes { get; set; } = [];

    [JsonPropertyName("avg_axis_error_deg")]
    public double AvgAxisErrorDeg { get; set; }

    [JsonPropertyName("max_axis_error_deg")]
    public double MaxAxisErrorDeg { get; set; }

    /// <summary>
    /// The widest spread within one axis family. In a parallel projection those edges must stay
    /// parallel to each other, so this is the invariant that replaces convergence to a point.
    /// </summary>
    [JsonPropertyName("parallelism_error_deg")]
    public double ParallelismErrorDeg { get; set; }

    [JsonPropertyName("off_axis_line_count")]
    public int OffAxisLineCount { get; set; }

    [JsonPropertyName("line_count")]
    public int LineCount { get; set; }

    [JsonPropertyName("axes_supported")]
    public int AxesSupported { get; set; }

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }

    [JsonPropertyName("confidence_low")]
    public bool ConfidenceLow { get; set; }

    [JsonPropertyName("image_width")]
    public int ImageWidth { get; set; }

    [JsonPropertyName("image_height")]
    public int ImageHeight { get; set; }

    [JsonPropertyName("lines")]
    public List<AxisSegmentDto> Lines { get; set; } = [];

    [JsonPropertyName("overlay_image_base64")]
    public string? OverlayImageBase64 { get; set; }
}


public class GroundLineDto
{
    [JsonPropertyName("start")]
    public Point2DDto Start { get; set; } = new();

    [JsonPropertyName("end")]
    public Point2DDto End { get; set; } = new();

    /// <summary>
    /// Tilt away from horizontal. Reported rather than corrected: every other figure on the plate
    /// is measured against this line, so a crooked one has to be declared before the rest is
    /// trusted.
    /// </summary>
    [JsonPropertyName("angle_deg")]
    public double AngleDeg { get; set; }

    [JsonPropertyName("length_px")]
    public double LengthPx { get; set; }

    [JsonPropertyName("source")]
    public string Source { get; set; } = "detected";
}

public class ReferenceLineMeasurementDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("start")]
    public Point2DDto Start { get; set; } = new();

    [JsonPropertyName("end")]
    public Point2DDto End { get; set; } = new();

    [JsonPropertyName("perpendicularity_error_deg")]
    public double PerpendicularityErrorDeg { get; set; }

    [JsonPropertyName("crosses_ground_line")]
    public bool CrossesGroundLine { get; set; }
}

public class CorrespondenceDto
{
    [JsonPropertyName("elevation_x")]
    public double? ElevationX { get; set; }

    [JsonPropertyName("plan_x")]
    public double? PlanX { get; set; }

    [JsonPropertyName("error_px")]
    public double? ErrorPx { get; set; }

    [JsonPropertyName("error_pct")]
    public double? ErrorPct { get; set; }

    [JsonPropertyName("matched")]
    public bool Matched { get; set; }
}

/// <summary>
/// Measurements of a Monge plate: two orthographic views checked against each other about the
/// ground line. A third shape again, because what is measured here is correspondence rather than
/// convergence or parallelism, and there is no vanishing point and no axis to report.
/// </summary>
public class DihedralAnalysisResultDto
{
    /// <summary>Null when no ground line was found, in which case nothing else was measured.</summary>
    [JsonPropertyName("ground_line")]
    public GroundLineDto? GroundLine { get; set; }

    [JsonPropertyName("reference_lines")]
    public List<ReferenceLineMeasurementDto> ReferenceLines { get; set; } = [];

    [JsonPropertyName("correspondences")]
    public List<CorrespondenceDto> Correspondences { get; set; } = [];

    /// <summary>
    /// How far the plan sits sideways from the elevation as a whole. One mistake with one
    /// correction — the plan placed wrong on the page — rather than one broken vertex per corner.
    /// </summary>
    [JsonPropertyName("systematic_offset_px")]
    public double? SystematicOffsetPx { get; set; }

    [JsonPropertyName("systematic_offset_pct")]
    public double? SystematicOffsetPct { get; set; }

    [JsonPropertyName("avg_perpendicularity_error_deg")]
    public double AvgPerpendicularityErrorDeg { get; set; }

    [JsonPropertyName("max_perpendicularity_error_deg")]
    public double MaxPerpendicularityErrorDeg { get; set; }

    /// <summary>
    /// Nullable, and that is the point. These are averages over the vertices the two views agreed
    /// on; when they agreed on none there is no average, and reporting 0.00 would tell a student
    /// their plate was perfectly aligned at the exact moment it was least aligned.
    /// </summary>
    [JsonPropertyName("avg_correspondence_error_px")]
    public double? AvgCorrespondenceErrorPx { get; set; }

    [JsonPropertyName("max_correspondence_error_px")]
    public double? MaxCorrespondenceErrorPx { get; set; }

    [JsonPropertyName("avg_correspondence_error_pct")]
    public double? AvgCorrespondenceErrorPct { get; set; }

    [JsonPropertyName("max_correspondence_error_pct")]
    public double? MaxCorrespondenceErrorPct { get; set; }

    [JsonPropertyName("matched_vertex_count")]
    public int MatchedVertexCount { get; set; }

    [JsonPropertyName("unmatched_in_elevation")]
    public int UnmatchedInElevation { get; set; }

    [JsonPropertyName("unmatched_in_plan")]
    public int UnmatchedInPlan { get; set; }

    [JsonPropertyName("elevation_line_count")]
    public int ElevationLineCount { get; set; }

    [JsonPropertyName("plan_line_count")]
    public int PlanLineCount { get; set; }

    [JsonPropertyName("line_count")]
    public int LineCount { get; set; }

    [JsonPropertyName("views_detected")]
    public int ViewsDetected { get; set; }

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }

    [JsonPropertyName("confidence_low")]
    public bool ConfidenceLow { get; set; }

    [JsonPropertyName("image_width")]
    public int ImageWidth { get; set; }

    [JsonPropertyName("image_height")]
    public int ImageHeight { get; set; }

    [JsonPropertyName("overlay_image_base64")]
    public string? OverlayImageBase64 { get; set; }
}

public class DihedralAnalysisRequestDto
{
    [JsonPropertyName("image_base64")]
    public string? ImageBase64 { get; set; }

    [JsonPropertyName("correspondence_tolerance_pct")]
    public double CorrespondenceTolerancePct { get; set; } = 1.5;

    [JsonPropertyName("generate_overlay")]
    public bool GenerateOverlay { get; set; } = true;
}

public class AxonometricAnalysisRequestDto
{
    [JsonPropertyName("image_base64")]
    public string? ImageBase64 { get; set; }

    [JsonPropertyName("system")]
    public string System { get; set; } = "isometric";

    [JsonPropertyName("receding_angle_deg")]
    public double? RecedingAngleDeg { get; set; }

    [JsonPropertyName("generate_overlay")]
    public bool GenerateOverlay { get; set; } = true;
}

public class MeasuredFindingItemDto
{
    [JsonPropertyName("metric_name")]
    public string MetricName { get; set; } = string.Empty;

    [JsonPropertyName("measured_value")]
    public double MeasuredValue { get; set; }

    [JsonPropertyName("unit")]
    public string Unit { get; set; } = "degrees";

    [JsonPropertyName("pedagogical_context")]
    public string PedagogicalContext { get; set; } = string.Empty;
}

public class QualitativeObservationItemDto
{
    [JsonPropertyName("aspect")]
    public string Aspect { get; set; } = string.Empty;

    [JsonPropertyName("observation")]
    public string Observation { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = "strength";
}

public class PedagogicalSummaryDto
{
    [JsonPropertyName("strengths")]
    public List<string> Strengths { get; set; } = [];

    [JsonPropertyName("focus_area")]
    public string FocusArea { get; set; } = string.Empty;

    [JsonPropertyName("encouragement")]
    public string Encouragement { get; set; } = string.Empty;
}

public class NextExerciseRecommendationDto
{
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("target_metric")]
    public string TargetMetric { get; set; } = string.Empty;

    [JsonPropertyName("difficulty")]
    public string Difficulty { get; set; } = "appropriate";
}

public class CritiqueOutputDto
{
    [JsonPropertyName("student_name")]
    public string StudentName { get; set; } = string.Empty;

    [JsonPropertyName("level")]
    public string Level { get; set; } = "beginner";

    [JsonPropertyName("headline")]
    public string Headline { get; set; } = string.Empty;

    [JsonPropertyName("measured_findings")]
    public List<MeasuredFindingItemDto> MeasuredFindings { get; set; } = [];

    [JsonPropertyName("qualitative_observations")]
    public List<QualitativeObservationItemDto> QualitativeObservations { get; set; } = [];

    [JsonPropertyName("pedagogical_summary")]
    public PedagogicalSummaryDto PedagogicalSummary { get; set; } = new();

    [JsonPropertyName("next_exercise")]
    public NextExerciseRecommendationDto NextExercise { get; set; } = new();

    /// <summary>
    /// Where this critique came from: "vertex" when Gemini answered, "fallback" when the
    /// deterministic studio template did. Defaults to "fallback" for the same reason the server
    /// does — unless something proves a model was involved, none was. The green
    /// "Anti-Hallucination: Validated" badge is gated on this.
    /// </summary>
    [JsonPropertyName("source")]
    public string Source { get; set; } = "fallback";

    [JsonPropertyName("model_version")]
    public string ModelVersion { get; set; } = "deterministic-template";

    [JsonPropertyName("validated")]
    public bool Validated { get; set; }
}

/// <summary>
/// An exercise as the agent stores it. The UI used to mint an id locally and never send this,
/// so feedback arrived for an exercise that did not exist, the 404 was swallowed, and the screen
/// said "Profile Adapted" over an empty database.
/// </summary>
public class ExerciseRecordDto
{
    [JsonPropertyName("exercise_id")]
    public string ExerciseId { get; set; } = string.Empty;

    [JsonPropertyName("student_id")]
    public string StudentId { get; set; } = string.Empty;

    [JsonPropertyName("source")]
    public string Source { get; set; } = "upload";

    [JsonPropertyName("student_intent")]
    public string? StudentIntent { get; set; }

    [JsonPropertyName("student_difficulty")]
    public string? StudentDifficulty { get; set; }

    [JsonPropertyName("geometry_analysis")]
    public GeometryAnalysisResultDto? GeometryAnalysis { get; set; }

    /// <summary>
    /// Parallel-projection measurements, in their own field. An average axis deviation and an
    /// average convergence error are both degrees and are not the same quantity, so the
    /// progression curve reads only the conic field rather than mixing the two into one line.
    /// </summary>
    [JsonPropertyName("axonometric_analysis")]
    public AxonometricAnalysisResultDto? AxonometricAnalysis { get; set; }

    [JsonPropertyName("dihedral_analysis")]
    public DihedralAnalysisResultDto? DihedralAnalysis { get; set; }

    [JsonPropertyName("critique")]
    public CritiqueOutputDto? Critique { get; set; }
}


/// <summary>
/// One past exercise, small enough to list. Deliberately not the full record: that carries the
/// whole analysis including a base64 overlay, and twenty of those is a payload no list can use.
/// </summary>
public class ExerciseSummaryDto
{
    [JsonPropertyName("exercise_id")]
    public string ExerciseId { get; set; } = string.Empty;

    [JsonPropertyName("created_at")]
    public string CreatedAt { get; set; } = string.Empty;

    [JsonPropertyName("projection")]
    public string Projection { get; set; } = "conic";

    [JsonPropertyName("headline")]
    public string Headline { get; set; } = string.Empty;

    [JsonPropertyName("metric_name")]
    public string MetricName { get; set; } = string.Empty;

    /// <summary>Null when the figure was not measurable. Never coerced to zero.</summary>
    [JsonPropertyName("metric_value")]
    public double? MetricValue { get; set; }

    [JsonPropertyName("metric_unit")]
    public string MetricUnit { get; set; } = "degrees";

    [JsonPropertyName("source")]
    public string Source { get; set; } = "fallback";

    [JsonPropertyName("student_intent")]
    public string? StudentIntent { get; set; }

    [JsonPropertyName("feedback_count")]
    public int FeedbackCount { get; set; }
}

public class CritiqueRequestDto
{
    [JsonPropertyName("image_base64")]
    public string? ImageBase64 { get; set; }

    /// <summary>
    /// The conic-perspective measurements, when that is what was drawn. Exactly one of this and
    /// <see cref="Axonometry"/> must be set: with neither, Plane A has nothing to be grounded in;
    /// with both, the validator would whitelist the union of two unrelated sets of numbers.
    /// </summary>
    [JsonPropertyName("geometry")]
    public GeometryAnalysisResultDto? Geometry { get; set; }

    [JsonPropertyName("axonometry")]
    public AxonometricAnalysisResultDto? Axonometry { get; set; }

    [JsonPropertyName("dihedral")]
    public DihedralAnalysisResultDto? Dihedral { get; set; }

    [JsonPropertyName("student")]
    public StudentProfileDto Student { get; set; } = new();

    [JsonPropertyName("student_intent")]
    public string? StudentIntent { get; set; }

    [JsonPropertyName("student_difficulty")]
    public string? StudentDifficulty { get; set; }

    /// <summary>
    /// Which language the critique prose comes back in. Set from the interface culture, not
    /// asked for separately: someone who switched the page to Spanish has already said which
    /// language they want to be taught in.
    /// </summary>
    [JsonPropertyName("language")]
    public string Language { get; set; } = "en";

    [JsonPropertyName("use_cache")]
    public bool UseCache { get; set; } = true;
}

public class CritiqueResponseDto
{
    [JsonPropertyName("critique")]
    public CritiqueOutputDto Critique { get; set; } = new();

    [JsonPropertyName("cached")]
    public bool Cached { get; set; }

    [JsonPropertyName("validation_retries")]
    public int ValidationRetries { get; set; }
}

public class AskPromptDataDto
{
    [JsonPropertyName("student_id")]
    public string StudentId { get; set; } = string.Empty;

    [JsonPropertyName("student_name")]
    public string StudentName { get; set; } = string.Empty;

    [JsonPropertyName("intent_question")]
    public string IntentQuestion { get; set; } = string.Empty;

    [JsonPropertyName("difficulty_question")]
    public string DifficultyQuestion { get; set; } = string.Empty;

    [JsonPropertyName("quick_intent_suggestions")]
    public List<string> QuickIntentSuggestions { get; set; } = [];

    [JsonPropertyName("quick_difficulty_suggestions")]
    public List<string> QuickDifficultySuggestions { get; set; } = [];
}

public class ProgressPointDto
{
    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;

    [JsonPropertyName("exercise_id")]
    public string ExerciseId { get; set; } = string.Empty;

    [JsonPropertyName("avg_convergence_error_deg")]
    public double AvgConvergenceErrorDeg { get; set; }

    [JsonPropertyName("k_points")]
    public int KPoints { get; set; } = 1;
}

public class DerivedProfileDto
{
    [JsonPropertyName("student")]
    public StudentProfileDto Student { get; set; } = new();

    [JsonPropertyName("total_exercises")]
    public int TotalExercises { get; set; }

    [JsonPropertyName("overall_avg_error_deg")]
    /// <summary>
    /// Null when no conic exercise has been recorded. Never coerced to zero: a mean over an empty
    /// set is undefined, and 0.0° reads as a perfect average on a profile with nothing in it.
    /// </summary>
    public double? OverallAvgErrorDeg { get; set; }

    [JsonPropertyName("progress_curve")]
    public List<ProgressPointDto> ProgressCurve { get; set; } = [];

    [JsonPropertyName("recurring_issues")]
    public List<string> RecurringIssues { get; set; } = [];

    [JsonPropertyName("derived_tone_preference")]
    public string DerivedTonePreference { get; set; } = "encouraging";

    [JsonPropertyName("recent_helpful_ratio")]
    public double RecentHelpfulRatio { get; set; } = 1.0;

    [JsonPropertyName("current_practice_focus")]
    public string CurrentPracticeFocus { get; set; } = string.Empty;

    [JsonPropertyName("recommended_next_exercise")]
    public NextExerciseRecommendationDto RecommendedNextExercise { get; set; } = new();
}

public class FeedbackRequestDto
{
    [JsonPropertyName("student_id")]
    public string StudentId { get; set; } = string.Empty;

    [JsonPropertyName("helpful")]
    public bool Helpful { get; set; }

    [JsonPropertyName("note")]
    public string? Note { get; set; }
}

public class PracticePlanDayDto
{
    [JsonPropertyName("day")]
    public string Day { get; set; } = string.Empty;

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("target_metric")]
    public string TargetMetric { get; set; } = string.Empty;
}

public class WeeklyDigestDto
{
    [JsonPropertyName("digest_id")]
    public string DigestId { get; set; } = string.Empty;

    [JsonPropertyName("student_id")]
    public string StudentId { get; set; } = string.Empty;

    [JsonPropertyName("student_name")]
    public string StudentName { get; set; } = string.Empty;

    [JsonPropertyName("week_id")]
    public string WeekId { get; set; } = string.Empty;

    [JsonPropertyName("total_drawings")]
    public int TotalDrawings { get; set; }

    [JsonPropertyName("weekly_avg_convergence_error_deg")]
    /// <summary>Null when the week held no conic exercise. Rendered as a dash, never as zero.</summary>
    public double? WeeklyAvgConvergenceErrorDeg { get; set; }

    [JsonPropertyName("error_reduction_deg")]
    /// <summary>Null when there were fewer than two conic exercises to compare.</summary>
    public double? ErrorReductionDeg { get; set; }

    [JsonPropertyName("recurring_issues")]
    public List<string> RecurringIssues { get; set; } = [];

    [JsonPropertyName("weekly_summary")]
    public string WeeklySummary { get; set; } = string.Empty;

    [JsonPropertyName("recommended_focus")]
    public string RecommendedFocus { get; set; } = string.Empty;

    [JsonPropertyName("next_week_practice_plan")]
    public List<PracticePlanDayDto> NextWeekPracticePlan { get; set; } = [];
}

/// <summary>
/// What the gate decided about the photograph, before anything was measured.
/// </summary>
public class DrawingGateResultDto
{
    [JsonPropertyName("is_exercise")]
    public bool IsExercise { get; set; } = true;

    /// <summary>
    /// "conic" when the receding edges converge, "axonometric" when they stay parallel, "none"
    /// when this is not an exercise. This is what selects the reference the drawing is measured
    /// against, and the two have nothing in common: one estimates a vanishing point from the
    /// drawing itself, the other compares against angles fixed by the projection system.
    /// </summary>
    [JsonPropertyName("projection")]
    public string Projection { get; set; } = "conic";

    [JsonPropertyName("exercise_type")]
    public string ExerciseType { get; set; } = "not-an-exercise";

    [JsonPropertyName("axonometric_system")]
    public string? AxonometricSystem { get; set; }

    [JsonPropertyName("recommended_k")]
    public int RecommendedK { get; set; }

    [JsonPropertyName("reasoning")]
    public string Reasoning { get; set; } = string.Empty;

    /// <summary>"vertex" when the model looked, "fallback" when it could not be reached.</summary>
    [JsonPropertyName("source")]
    public string Source { get; set; } = "fallback";
}

/// <summary>
/// Which perspective model to measure against, chosen from the student's own description.
/// </summary>
public class RoutingResultDto
{
    [JsonPropertyName("exercise_type")]
    public string ExerciseType { get; set; } = "one-point-conical";

    [JsonPropertyName("recommended_k")]
    public int RecommendedK { get; set; } = 1;

    [JsonPropertyName("reasoning")]
    public string Reasoning { get; set; } = string.Empty;

    /// <summary>"gemma" when the router model decided, "fallback" when the profile level did.</summary>
    [JsonPropertyName("source")]
    public string Source { get; set; } = "fallback";
}
