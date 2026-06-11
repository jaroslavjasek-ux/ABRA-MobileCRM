using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Middleware;

var builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<GenOptions>(builder.Configuration.GetSection(GenOptions.SectionName));
builder.Services.Configure<ActivityFeatureOptions>(
    builder.Configuration.GetSection(ActivityFeatureOptions.SectionName));
builder.Services.AddSingleton<ISessionStore, InMemorySessionStore>();
builder.Services.AddHttpClient<IGenApiClient, GenApiClient>((sp, client) =>
{
    var options = sp.GetRequiredService<Microsoft.Extensions.Options.IOptions<GenOptions>>().Value;
    client.Timeout = TimeSpan.FromSeconds(options.TimeoutSeconds);
});
builder.Services.AddGenIntegration();

builder.Services.AddControllers()
    .AddJsonOptions(o =>
    {
        o.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
    });

builder.Services.AddCors(options =>
{
    options.AddPolicy("DevCors", policy =>
    {
        policy.WithOrigins(
                "http://localhost:5173",
                "http://127.0.0.1:5173")
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});

var app = builder.Build();

app.UseMiddleware<CorrelationIdMiddleware>();
app.UseMiddleware<ExceptionEnvelopeMiddleware>();
app.UseCors("DevCors");
app.UseMiddleware<SessionAuthMiddleware>();

app.MapControllers();

app.Run();
