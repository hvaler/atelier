using Microsoft.AspNetCore.Localization;
using Microsoft.Extensions.Options;
using Microsoft.AspNetCore.HttpOverrides;
using Atelier.Web.Components;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

builder.Services.AddHttpClient("AgentClient", client =>
{
    var agentUrl = builder.Configuration["Agent:BaseUrl"] ?? "http://localhost:8000";
    client.BaseAddress = new Uri(agentUrl);
});
builder.Services.AddScoped<Atelier.Web.Services.IAtelierAgentClient, Atelier.Web.Services.AtelierAgentClient>();

// Localisation. English is the default because the submission, the repository and the judging
// are in English; Spanish exists because the student this was built for reads Spanish, and a
// nine-year-old should not have to read her own drawing critique in a second language.
builder.Services.AddLocalization(options => options.ResourcesPath = "Resources");
builder.Services.AddControllers();   // for the culture-setting endpoint below

var supportedCultures = new[] { "en", "es" };
builder.Services.Configure<RequestLocalizationOptions>(options =>
{
    options.SetDefaultCulture(supportedCultures[0])
           .AddSupportedCultures(supportedCultures)
           .AddSupportedUICultures(supportedCultures);
});

var app = builder.Build();

// Forwarded Headers for Cloud Run reverse proxy termination (TEC-007)
var forwardedHeadersOptions = new ForwardedHeadersOptions
{
    ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto
};
forwardedHeadersOptions.KnownIPNetworks.Clear();
forwardedHeadersOptions.KnownProxies.Clear();
app.UseForwardedHeaders(forwardedHeadersOptions);

// Health check endpoint for Cloud Run and monitoring (avoids /healthz)
app.MapGet("/api/health", () => Results.Ok(new
{
    status = "healthy",
    service = "Atelier.Web",
    version = "0.1.0",
    environment = app.Environment.EnvironmentName,
    timestamp = DateTime.UtcNow
}));

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    app.UseHsts();
}
app.UseStatusCodePagesWithReExecute("/not-found", createScopeForStatusCodePages: true);
app.UseHttpsRedirection();

app.UseRequestLocalization(app.Services.GetRequiredService<IOptions<RequestLocalizationOptions>>().Value);
app.UseAntiforgery();

// Switching culture in Blazor Server means writing the cookie the request-localisation
// middleware reads, then reloading — the circuit's culture is fixed when it opens.
app.MapGet("/culture/set", (string culture, string redirectUri, HttpContext http) =>
{
    http.Response.Cookies.Append(
        CookieRequestCultureProvider.DefaultCookieName,
        CookieRequestCultureProvider.MakeCookieValue(new RequestCulture(culture, culture)),
        new CookieOptions { Path = "/", IsEssential = true, MaxAge = TimeSpan.FromDays(365) });
    return Results.LocalRedirect(string.IsNullOrWhiteSpace(redirectUri) ? "/" : redirectUri);
});

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
