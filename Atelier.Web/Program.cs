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

app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
