using System.Net.Http.Json;
using Atelier.Web.Models;

namespace Atelier.Web.Services;

public interface IAtelierAgentClient
{
    Task<List<StudentProfileDto>> GetStudentsAsync();
    Task<AskPromptDataDto?> GetAskPromptAsync(string studentId);
    Task<GeometryAnalysisResultDto?> AnalyzeGeometryAsync(string imageBase64, int kPoints, bool generateOverlay = true);
    Task<CritiqueResponseDto?> GenerateCritiqueAsync(CritiqueRequestDto request);
    Task<DrawingGateResultDto?> ClassifyDrawingAsync(string imageBase64);
    Task<RoutingResultDto?> RouteIntentAsync(string? studentIntent, string studentLevel);
    Task<ExerciseRecordDto?> SaveExerciseAsync(ExerciseRecordDto exercise);
    Task<bool> SubmitFeedbackAsync(string exerciseId, string studentId, bool helpful, string? note);
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
                StudentName = studentId.Contains("sofia") ? "Sofia" : "Young Tester (Age 9)",
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
            _logger.LogError(ex, "Failed to analyze geometry on atelier-agent.");
            return null;
        }

        _logger.LogError("atelier-agent refused the analysis request.");
        return null;
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
            _logger.LogError(ex, "Failed to generate critique on atelier-agent.");
            return null;
        }

        // No fallback critique. This method used to hand back a hand-written one, so a dead
        // agent looked identical to a working one: the page showed a confident two-plane
        // critique with the green validated badge, composed entirely in this file. The screen
        // now says the agent is unreachable, which is the only true thing available.
        _logger.LogError("atelier-agent refused the critique request.");
        return null;
    }

    /// <summary>
    /// Ask whether this photograph is a perspective exercise at all, before measuring it.
    ///
    /// Runs on Gemini 3.5 Flash vision. Failing to reach it lets the drawing through — refusing
    /// a student's work because a model is down would be worse than measuring one that should
    /// not have been measured — but the caller can tell the two apart from `Source`.
    /// </summary>
    public async Task<DrawingGateResultDto?> ClassifyDrawingAsync(string imageBase64)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/router/gate", new
            {
                image_base64 = imageBase64,
                k_points = 1,
                generate_overlay = false
            });
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<DrawingGateResultDto>();
            }

            _logger.LogError("Drawing gate refused the request: HTTP {Status}", (int)response.StatusCode);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to reach the drawing gate.");
        }
        return null;
    }

    /// <summary>
    /// Choose the perspective model from what the student wrote, on Gemma 4.
    /// </summary>
    public async Task<RoutingResultDto?> RouteIntentAsync(string? studentIntent, string studentLevel)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/router/classify", new
            {
                student_intent = studentIntent,
                student_level_hint = studentLevel
            });
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<RoutingResultDto>();
            }

            _logger.LogError("Intent router refused the request: HTTP {Status}", (int)response.StatusCode);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to reach the intent router.");
        }
        return null;
    }

    /// <summary>
    /// Persist the exercise so that feedback has something to attach to.
    ///
    /// The UI never called this. It minted an id locally, so every feedback submission hit a
    /// 404 that the client swallowed, and the screen reported the profile as adapted.
    /// </summary>
    public async Task<ExerciseRecordDto?> SaveExerciseAsync(ExerciseRecordDto exercise)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync("/api/exercises", exercise);
            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<ExerciseRecordDto>();
            }

            _logger.LogError(
                "Agent refused to save exercise {ExerciseId}: HTTP {Status}",
                exercise.ExerciseId, (int)response.StatusCode);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to save exercise {ExerciseId}", exercise.ExerciseId);
        }
        return null;
    }

    /// <summary>
    /// Record a thumbs up or down. Returns whether it was actually recorded.
    ///
    /// This used to return the request payload on both paths, so a caller could not tell a
    /// stored event from a dropped one — and the UI, reasonably, assumed success.
    /// </summary>
    public async Task<bool> SubmitFeedbackAsync(string exerciseId, string studentId, bool helpful, string? note)
    {
        try
        {
            var payload = new FeedbackRequestDto { StudentId = studentId, Helpful = helpful, Note = note };
            var response = await _httpClient.PostAsJsonAsync($"/api/exercises/{exerciseId}/feedback", payload);
            if (response.IsSuccessStatusCode)
            {
                return true;
            }

            _logger.LogError(
                "Agent refused feedback for exercise {ExerciseId}: HTTP {Status}",
                exerciseId, (int)response.StatusCode);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to submit feedback for exercise {ExerciseId}", exerciseId);
        }
        return false;
    }

    public async Task<DerivedProfileDto?> GetDerivedProfileAsync(string studentId)
    {
        try
        {
            return await _httpClient.GetFromJsonAsync<DerivedProfileDto>($"/api/students/{studentId}/profile");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "GetDerivedProfileAsync failed for {StudentId}", studentId);
        }

        // No invented data. This returned a hand-written figure, so an empty history and a
        // broken agent both looked like a student making progress.
        return null;
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
            _logger.LogError(ex, "GetWeeklyDigestAsync failed for {StudentId}", studentId);
        }

        // No invented data. This returned a hand-written figure, so an empty history and a
        // broken agent both looked like a student making progress.
        return null;

    }

    private static List<StudentProfileDto> GetFallbackStudents() =>
    [
        new StudentProfileDto { StudentId = "young-tester-01", Name = "Young Tester (Age 9)", Level = "beginner", TonePreference = "encouraging" },
        new StudentProfileDto { StudentId = "sofia-01", Name = "Sofia", Level = "advanced", TonePreference = "technical" }
    ];
}
