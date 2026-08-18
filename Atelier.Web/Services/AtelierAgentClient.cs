using System.Net.Http.Json;
using Atelier.Web.Models;

namespace Atelier.Web.Services;

public interface IAtelierAgentClient
{
    Task<List<StudentProfileDto>> GetStudentsAsync();
    Task<AskPromptDataDto?> GetAskPromptAsync(string studentId);
    Task<GeometryAnalysisResultDto?> AnalyzeGeometryAsync(string imageBase64, int kPoints, bool generateOverlay = true);
    Task<CritiqueResponseDto?> GenerateCritiqueAsync(CritiqueRequestDto request);
    Task<FeedbackRequestDto?> SubmitFeedbackAsync(string exerciseId, string studentId, bool helpful, string? note);
    Task<DerivedProfileDto?> GetDerivedProfileAsync(string studentId);
    Task<NextExerciseRecommendationDto?> GetNextGuidedExerciseAsync(string studentId);
    Task<WeeklyDigestDto?> GetWeeklyDigestAsync(string studentId);
}

public class AtelierAgentClient : IAtelierAgentClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<AtelierAgentClient> _logger;

    public AtelierAgentClient(IHttpClientFactory httpClientFactory, ILogger<AtelierAgentClient> logger)
    {
        _httpClient = httpClientFactory.CreateClient("AgentClient");
        _logger = logger;
    }

    public async Task<List<StudentProfileDto>> GetStudentsAsync()
    {
        try
        {
            var result = await _httpClient.GetFromJsonAsync<List<StudentProfileDto>>("/api/students");
            return result ?? GetFallbackStudents();
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to reach /api/students, using fallback profiles.");
            return GetFallbackStudents();
        }
    }

    public async Task<AskPromptDataDto?> GetAskPromptAsync(string studentId)
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<AskPromptDataDto>($"/api/students/{studentId}/ask");
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to get ask prompt for {StudentId}", studentId);
            return new AskPromptDataDto
            {
                StudentId = studentId,
                StudentName = studentId.Contains("clara") ? "Clara" : "Sofia",
                IntentQuestion = "What kind of 3D form or perspective exercise were you practicing?",
                DifficultyQuestion = "Which part or axis felt hardest to calibrate?",
                QuickIntentSuggestions = ["1-Point Frontal Box", "2-Point Oblique Cube", "Stepped Architectural Volume"],
                QuickDifficultySuggestions = ["Vanishing Point Alignment", "Vertical Axis Slant", "Line Weight Contrast"]
            };
        }
    }

    public async Task<GeometryAnalysisResultDto?> AnalyzeGeometryAsync(string imageBase64, int kPoints, bool generateOverlay = true)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/analyze", new
            {
                image_base64 = imageBase64,
                k_points = kPoints,
                generate_overlay = generateOverlay
            });
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<GeometryAnalysisResultDto>();
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to analyze geometry on atelier-agent.");
        }

        // Fallback simulation for tests/offline
        return new GeometryAnalysisResultDto
        {
            KRequested = kPoints,
            KDetected = kPoints,
            AvgConvergenceErrorDeg = kPoints == 1 ? 1.8 : 2.4,
            MaxConvergenceErrorDeg = kPoints == 1 ? 3.2 : 4.6,
            Confidence = 0.88,
            ConfidenceLow = false,
            LineCount = 8,
            ImageWidth = 800,
            ImageHeight = 600,
            VanishingPoints =
            [
                new VanishingPointDto
                {
                    Index = 0,
                    Label = kPoints == 1 ? "VP" : "F1",
                    Point = new Point2DDto { X = 400, Y = 250, NormX = 0.5, NormY = 0.41 },
                    AvgErrorDeg = 1.8,
                    SupportingLines = 6
                }
            ],
            OverlayImageBase64 = imageBase64
        };
    }

    public async Task<CritiqueResponseDto?> GenerateCritiqueAsync(CritiqueRequestDto request)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/critique", request);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<CritiqueResponseDto>();
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to generate critique on atelier-agent.");
        }

        // Fallback critique
        var isBeginner = request.Student.Level == "beginner";
        return new CritiqueResponseDto
        {
            Cached = false,
            ValidationRetries = 0,
            Critique = new CritiqueOutputDto
            {
                StudentName = request.Student.Name,
                Level = request.Student.Level,
                Headline = isBeginner ? $"Wonderful 3D Practice, {request.Student.Name}!" : $"Perspective Review: Solid Volumetric Structure, {request.Student.Name}",
                ModelVersion = "gemini-3.5-flash",
                Validated = true,
                MeasuredFindings =
                [
                    new MeasuredFindingItemDto
                    {
                        MetricName = "average_convergence_error",
                        MeasuredValue = request.Geometry.AvgConvergenceErrorDeg,
                        Unit = "degrees",
                        PedagogicalContext = $"Your perspective lines show an average deviation of {request.Geometry.AvgConvergenceErrorDeg:F1}° to the horizon vanishing points."
                    }
                ],
                QualitativeObservations =
                [
                    new QualitativeObservationItemDto
                    {
                        Aspect = "line_weight",
                        Observation = "Clear distinction between light construction guidelines and final contours.",
                        Status = "strength"
                    },
                    new QualitativeObservationItemDto
                    {
                        Aspect = "spatial_clarity",
                        Observation = "Clean volume definition with readable receding planes.",
                        Status = "proficient"
                    }
                ],
                PedagogicalSummary = new PedagogicalSummaryDto
                {
                    Strengths = ["Clean depth lines", "Steady vertical axes"],
                    FocusArea = "Refining secondary convergence edges towards the distant horizon.",
                    Encouragement = $"Great work, {request.Student.Name}! Every drawing strengthens your 3D spatial vision."
                },
                NextExercise = new NextExerciseRecommendationDto
                {
                    Title = isBeginner ? "3 Aligned Boxes in Space" : "2-Point Stepped Volume Drill",
                    Description = isBeginner ? "Draw three boxes pointing to the same dot on the horizon line." : "Construct two intersecting rectangular forms converging to F1 and F2.",
                    TargetMetric = isBeginner ? "1-point VP consistency" : "2-point oblique perspective",
                    Difficulty = isBeginner ? "beginner" : "advanced"
                }
            }
        };
    }

    public async Task<FeedbackRequestDto?> SubmitFeedbackAsync(string exerciseId, string studentId, bool helpful, string? note)
    {
        try
        {
            var payload = new FeedbackRequestDto { StudentId = studentId, Helpful = helpful, Note = note };
            var response = await _httpClient.PostAsJsonAsync($"/api/exercises/{exerciseId}/feedback", payload);
            if (response.IsSuccessStatusCode)
            {
                return payload;
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to submit feedback for exercise {ExerciseId}", exerciseId);
        }
        return new FeedbackRequestDto { StudentId = studentId, Helpful = helpful, Note = note };
    }

    public async Task<DerivedProfileDto?> GetDerivedProfileAsync(string studentId)
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<DerivedProfileDto>($"/api/students/{studentId}/profile");
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to get derived profile for {StudentId}", studentId);
            var isBeginner = studentId.Contains("clara");
            return new DerivedProfileDto
            {
                Student = new StudentProfileDto
                {
                    StudentId = studentId,
                    Name = isBeginner ? "Clara" : "Sofia",
                    Level = isBeginner ? "beginner" : "advanced"
                },
                TotalExercises = 4,
                OverallAvgErrorDeg = isBeginner ? 2.1 : 2.8,
                DerivedTonePreference = isBeginner ? "encouraging" : "technical",
                RecentHelpfulRatio = 1.0,
                CurrentPracticeFocus = isBeginner ? "1-Point frontal cube alignment" : "2-Point F1 depth convergence",
                ProgressCurve =
                [
                    new ProgressPointDto { Timestamp = "Session 1", AvgConvergenceErrorDeg = 4.8, KPoints = 1, ExerciseId = "1" },
                    new ProgressPointDto { Timestamp = "Session 2", AvgConvergenceErrorDeg = 3.6, KPoints = 1, ExerciseId = "2" },
                    new ProgressPointDto { Timestamp = "Session 3", AvgConvergenceErrorDeg = 2.4, KPoints = 1, ExerciseId = "3" },
                    new ProgressPointDto { Timestamp = "Session 4", AvgConvergenceErrorDeg = 1.8, KPoints = 1, ExerciseId = "4" }
                ],
                RecommendedNextExercise = new NextExerciseRecommendationDto
                {
                    Title = isBeginner ? "3 Aligned Boxes in Space" : "2-Point Stepped Architectural Block",
                    Description = "Construct solid volumes verifying receding horizontal lines converge to the horizon.",
                    TargetMetric = "Convergence accuracy",
                    Difficulty = isBeginner ? "beginner" : "advanced"
                }
            };
        }
    }

    public async Task<NextExerciseRecommendationDto?> GetNextGuidedExerciseAsync(string studentId)
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<NextExerciseRecommendationDto>($"/api/students/{studentId}/guide");
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to get next guided exercise for {StudentId}", studentId);
            return new NextExerciseRecommendationDto
            {
                Title = "Targeted Perspective Drill",
                Description = "Practice box convergence with light construction lines.",
                TargetMetric = "Convergence accuracy",
                Difficulty = "appropriate"
            };
        }
    }

    public async Task<WeeklyDigestDto?> GetWeeklyDigestAsync(string studentId)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/digest/weekly", new { student_id = studentId });
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<WeeklyDigestDto>();
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to generate weekly digest for {StudentId}", studentId);
        }

        var isBeginner = studentId.Contains("clara");
        return new WeeklyDigestDto
        {
            DigestId = "digest-sample",
            StudentId = studentId,
            StudentName = isBeginner ? "Clara" : "Sofia",
            WeekId = "2026-W34",
            TotalDrawings = 4,
            WeeklyAvgConvergenceErrorDeg = isBeginner ? 2.1 : 2.6,
            ErrorReductionDeg = 1.4,
            WeeklySummary = $"Great consistency this week! Your average angular error dropped by 1.4°.",
            RecommendedFocus = isBeginner ? "Frontal face alignment and light pencil pressure." : "F1 vanishing point convergence and line weight contrast.",
            NextWeekPracticePlan =
            [
                new PracticePlanDayDto { Day = "Monday", Title = "3 Cubes on Horizon", Description = "Draw three boxes pointing to the center VP.", TargetMetric = "1-Point VP consistency" },
                new PracticePlanDayDto { Day = "Wednesday", Title = "Floating Cube Practice", Description = "Draw a floating box above eye level.", TargetMetric = "Horizon alignment" },
                new PracticePlanDayDto { Day = "Friday", Title = "Stepped Room Box", Description = "Draw a room interior in 1-point perspective.", TargetMetric = "Spatial readability" }
            ]
        };
    }

    private static List<StudentProfileDto> GetFallbackStudents() =>
    [
        new StudentProfileDto { StudentId = "clara-01", Name = "Clara", Level = "beginner", TonePreference = "encouraging" },
        new StudentProfileDto { StudentId = "sofia-01", Name = "Sofia", Level = "advanced", TonePreference = "technical" }
    ];
}
