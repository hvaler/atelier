using Atelier.Web.Models;
using Atelier.Web.Services;
using Microsoft.Extensions.Logging.Abstractions;
using Moq;

namespace Atelier.Web.Tests;

public class AgentClientTests
{
    private readonly IAtelierAgentClient _client;

    public AgentClientTests()
    {
        var mockFactory = new Mock<IHttpClientFactory>();
        var httpClient = new HttpClient { BaseAddress = new Uri("http://localhost:8000") };
        mockFactory.Setup(f => f.CreateClient(It.IsAny<string>())).Returns(httpClient);

        _client = new AtelierAgentClient(mockFactory.Object, NullLogger<AtelierAgentClient>.Instance);
    }

    [Fact]
    public async Task GetStudentsAsync_ReturnsProfiles_WithFallback()
    {
        // Act
        var students = await _client.GetStudentsAsync();

        // Assert
        Assert.NotNull(students);
        Assert.NotEmpty(students);
        Assert.Contains(students, s => s.Name == "Clara" && s.Level == "beginner");
        Assert.Contains(students, s => s.Name == "Sofia" && s.Level == "advanced");
    }

    [Fact]
    public async Task GetAskPromptAsync_ReturnsTailoredQuestions()
    {
        // Act
        var askClara = await _client.GetAskPromptAsync("clara-01");

        // Assert
        Assert.NotNull(askClara);
        Assert.Equal("Clara", askClara.StudentName);
        Assert.NotEmpty(askClara.QuickIntentSuggestions);
    }

    [Fact]
    public async Task AnalyzeGeometryAsync_ReturnsValidGeometryPayload()
    {
        // Act
        var result = await _client.AnalyzeGeometryAsync(string.Empty, kPoints: 1);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(1, result.KRequested);
        Assert.True(result.AvgConvergenceErrorDeg >= 0);
        Assert.False(result.ConfidenceLow);
    }

    [Fact]
    public async Task GenerateCritiqueAsync_ProducesTwoPlaneCritique()
    {
        // Arrange
        var geom = new GeometryAnalysisResultDto
        {
            KRequested = 1,
            KDetected = 1,
            AvgConvergenceErrorDeg = 1.8,
            Confidence = 0.9
        };
        var student = new StudentProfileDto
        {
            StudentId = "clara-01",
            Name = "Clara",
            Level = "beginner"
        };
        var req = new CritiqueRequestDto
        {
            Geometry = geom,
            Student = student,
            StudentIntent = "1-Point box"
        };

        // Act
        var response = await _client.GenerateCritiqueAsync(req);

        // Assert
        Assert.NotNull(response);
        Assert.NotNull(response.Critique);
        Assert.Equal("Clara", response.Critique.StudentName);
        Assert.NotEmpty(response.Critique.MeasuredFindings);
        Assert.NotEmpty(response.Critique.QualitativeObservations);
        Assert.NotNull(response.Critique.NextExercise);
    }

    [Fact]
    public async Task GetDerivedProfileAsync_ReturnsProgressionCurve()
    {
        // Act
        var profile = await _client.GetDerivedProfileAsync("clara-01");

        // Assert
        Assert.NotNull(profile);
        Assert.NotNull(profile.Student);
        Assert.NotEmpty(profile.ProgressCurve);
        Assert.True(profile.TotalExercises > 0);
    }

    [Fact]
    public async Task GetWeeklyDigestAsync_ReturnsPracticePlan()
    {
        // Act
        var digest = await _client.GetWeeklyDigestAsync("sofia-01");

        // Assert
        Assert.NotNull(digest);
        Assert.Equal("Sofia", digest.StudentName);
        Assert.NotEmpty(digest.NextWeekPracticePlan);
        Assert.Contains(digest.NextWeekPracticePlan, p => p.Day == "Monday");
    }
}
