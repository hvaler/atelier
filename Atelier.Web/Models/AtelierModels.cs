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

    [JsonPropertyName("convergence_error_deg")]
    public double ConvergenceErrorDeg { get; set; }
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

    [JsonPropertyName("model_version")]
    public string ModelVersion { get; set; } = "gemini-3.5-flash";

    [JsonPropertyName("validated")]
    public bool Validated { get; set; } = true;
}

public class CritiqueRequestDto
{
    [JsonPropertyName("image_base64")]
    public string? ImageBase64 { get; set; }

    [JsonPropertyName("geometry")]
    public GeometryAnalysisResultDto Geometry { get; set; } = new();

    [JsonPropertyName("student")]
    public StudentProfileDto Student { get; set; } = new();

    [JsonPropertyName("student_intent")]
    public string? StudentIntent { get; set; }

    [JsonPropertyName("student_difficulty")]
    public string? StudentDifficulty { get; set; }

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
    public double OverallAvgErrorDeg { get; set; }

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
    public double WeeklyAvgConvergenceErrorDeg { get; set; }

    [JsonPropertyName("error_reduction_deg")]
    public double ErrorReductionDeg { get; set; }

    [JsonPropertyName("recurring_issues")]
    public List<string> RecurringIssues { get; set; } = [];

    [JsonPropertyName("weekly_summary")]
    public string WeeklySummary { get; set; } = string.Empty;

    [JsonPropertyName("recommended_focus")]
    public string RecommendedFocus { get; set; } = string.Empty;

    [JsonPropertyName("next_week_practice_plan")]
    public List<PracticePlanDayDto> NextWeekPracticePlan { get; set; } = [];
}
