using System.Net;
using System.Text;
using Atelier.Web.Models;
using Atelier.Web.Services;
using Microsoft.Extensions.Logging.Abstractions;
using Moq;

namespace Atelier.Web.Tests;

/// <summary>
/// Contract tests for the typed agent client.
///
/// <para>These replace six tests that pointed an <see cref="HttpClient"/> at
/// <c>http://localhost:8000</c> with nothing listening, so every call threw, fell into a
/// hardcoded fallback, and the assertions checked those constants. They passed only while the
/// system was broken: <c>Assert.True(profile.TotalExercises &gt; 0)</c> succeeded because the
/// fallback hardcoded four, and would have failed against a live backend where a fresh student
/// has none. A suite that goes green when the service is down is worse than no suite.</para>
///
/// <para>What is tested here instead is the thing this client is actually responsible for: the
/// snake_case wire format the Python agent speaks, mapped onto PascalCase C#. A stub handler
/// returns real agent payloads, and a failure case asserts that a refused request produces
/// <c>null</c> rather than an invention.</para>
/// </summary>
public class AgentClientTests
{
    /// <summary>Answers every request with a canned status and body.</summary>
    private sealed class StubHandler : HttpMessageHandler
    {
        private readonly HttpStatusCode _status;
        private readonly string _body;

        public StubHandler(HttpStatusCode status, string body = "")
        {
            _status = status;
            _body = body;
        }

        public string? LastRequestUri { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request, CancellationToken cancellationToken)
        {
            LastRequestUri = request.RequestUri?.PathAndQuery;
            return Task.FromResult(new HttpResponseMessage(_status)
            {
                Content = new StringContent(_body, Encoding.UTF8, "application/json")
            });
        }
    }

    private static (AtelierAgentClient Client, StubHandler Handler) Build(
        HttpStatusCode status, string body = "")
    {
        var handler = new StubHandler(status, body);
        var httpClient = new HttpClient(handler) { BaseAddress = new Uri("http://agent.test") };
        var factory = new Mock<IHttpClientFactory>();
        factory.Setup(f => f.CreateClient(It.IsAny<string>())).Returns(httpClient);
        return (new AtelierAgentClient(factory.Object, NullLogger<AtelierAgentClient>.Instance), handler);
    }

    [Fact]
    public async Task AnalyzeGeometryAsync_MapsTheAgentsSnakeCasePayload()
    {
        const string body = """
        {
          "k_requested": 1, "k_detected": 1,
          "avg_convergence_error_deg": 0.82, "max_convergence_error_deg": 2.53,
          "confidence": 0.97, "confidence_low": false, "line_count": 16,
          "image_width": 800, "image_height": 600,
          "vanishing_points": [
            {"index": 1, "label": "F1",
             "point": {"x": 401.0, "y": 250.0, "norm_x": 0.5, "norm_y": 0.42},
             "avg_error_deg": 0.82, "supporting_lines": 16}
          ],
          "lines": []
        }
        """;
        var (client, handler) = Build(HttpStatusCode.OK, body);

        var result = await client.AnalyzeGeometryAsync("aGVsbG8=", 1, generateOverlay: true);

        Assert.NotNull(result);
        Assert.Equal("/api/analyze", handler.LastRequestUri);
        // The real measurement of 01_1point_perfect.png, not a constant this file chose.
        Assert.Equal(0.82, result!.AvgConvergenceErrorDeg, precision: 2);
        Assert.Equal(1, result.KDetected);
        Assert.Single(result.VanishingPoints);
        Assert.Equal("F1", result.VanishingPoints[0].Label);
        Assert.Equal(401.0, result.VanishingPoints[0].Point.X, precision: 1);
    }

    [Fact]
    public async Task AnalyzeGeometryAsync_ReturnsNullWhenTheAgentRefuses()
    {
        var (client, _) = Build(HttpStatusCode.InternalServerError);

        var result = await client.AnalyzeGeometryAsync("aGVsbG8=", 1, generateOverlay: true);

        // Null, not a plausible-looking drawing. The page renders "the analysis service did not
        // answer"; it used to render 1.8 degrees and a confidence of 0.88.
        Assert.Null(result);
    }

    [Fact]
    public async Task GenerateCritiqueAsync_CarriesProvenanceThrough()
    {
        const string body = """
        {
          "critique": {
            "student_name": "Clara", "level": "beginner",
            "headline": "Fantastic 3D Box Magic!",
            "measured_findings": [], "qualitative_observations": [],
            "pedagogical_summary": {"strengths": [], "focus_area": "", "encouragement": ""},
            "next_exercise": {"title": "", "description": "", "target_metric": "", "difficulty": "beginner"},
            "source": "vertex", "model_version": "gemini-3.5-flash", "validated": true
          },
          "cached": false, "validation_retries": 0
        }
        """;
        var (client, _) = Build(HttpStatusCode.OK, body);

        var response = await client.GenerateCritiqueAsync(new CritiqueRequestDto());

        Assert.NotNull(response);
        // The badge on screen is gated on these two, so the mapping has to survive the wire.
        Assert.Equal("vertex", response!.Critique.Source);
        Assert.True(response.Critique.Validated);
        Assert.Equal("gemini-3.5-flash", response.Critique.ModelVersion);
    }

    [Fact]
    public async Task CritiqueDefaultsToFallbackWhenTheAgentOmitsProvenance()
    {
        const string body = """
        {
          "critique": {
            "student_name": "Clara", "level": "beginner", "headline": "x",
            "measured_findings": [], "qualitative_observations": [],
            "pedagogical_summary": {"strengths": [], "focus_area": "", "encouragement": ""},
            "next_exercise": {"title": "", "description": "", "target_metric": "", "difficulty": "beginner"}
          },
          "cached": false, "validation_retries": 0
        }
        """;
        var (client, _) = Build(HttpStatusCode.OK, body);

        var response = await client.GenerateCritiqueAsync(new CritiqueRequestDto());

        // Absent provenance must read as "no model answered", never as a validated one. This is
        // the direction the default has to fail in.
        Assert.Equal("fallback", response!.Critique.Source);
        Assert.False(response.Critique.Validated);
    }

    [Fact]
    public async Task SaveExerciseAsync_ReturnsTheIdTheAgentAssigned()
    {
        const string body = """
        {"exercise_id": "ex-ui-9f3a1c2b", "student_id": "young-tester-01", "source": "upload"}
        """;
        var (client, handler) = Build(HttpStatusCode.Created, body);

        var saved = await client.SaveExerciseAsync(new ExerciseRecordDto
        {
            ExerciseId = "ex-ui-9f3a1c2b",
            StudentId = "young-tester-01"
        });

        Assert.NotNull(saved);
        Assert.Equal("/api/exercises", handler.LastRequestUri);
        Assert.Equal("ex-ui-9f3a1c2b", saved!.ExerciseId);
    }

    [Fact]
    public async Task SubmitFeedbackAsync_ReportsWhetherItWasRecorded()
    {
        var (recorded, _) = Build(HttpStatusCode.Created, "{}");
        var (refused, _) = Build(HttpStatusCode.NotFound);

        Assert.True(await recorded.SubmitFeedbackAsync("ex-1", "young-tester-01", true, null));
        // A 404 means the exercise does not exist, so nothing was appended. The old client
        // returned its own request payload here and the UI showed "Profile Adapted".
        Assert.False(await refused.SubmitFeedbackAsync("ex-1", "young-tester-01", true, null));
    }

    [Fact]
    public async Task GetDerivedProfileAsync_MapsTheProgressionCurve()
    {
        const string body = """
        {
          "student_id": "young-tester-01", "student_name": "Young Tester (Age 9)",
          "derived_tone_preference": "encouraging", "total_exercises": 0,
          "recurring_issues": [], "progress_curve": []
        }
        """;
        var (client, _) = Build(HttpStatusCode.OK, body);

        var profile = await client.GetDerivedProfileAsync("young-tester-01");

        Assert.NotNull(profile);
        Assert.Equal("encouraging", profile!.DerivedTonePreference);
        // Zero is the correct answer for a student who has done nothing. The previous suite
        // asserted TotalExercises > 0 and passed only because the fallback hardcoded four.
        Assert.Equal(0, profile.TotalExercises);
    }
}
