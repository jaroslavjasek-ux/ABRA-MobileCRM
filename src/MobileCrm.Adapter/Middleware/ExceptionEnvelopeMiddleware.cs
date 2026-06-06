using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;

namespace MobileCrm.Adapter.Middleware;

public sealed class ExceptionEnvelopeMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionEnvelopeMiddleware> _logger;

    public ExceptionEnvelopeMiddleware(RequestDelegate next, ILogger<ExceptionEnvelopeMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "Gen API error {Status}", ex.StatusCode);
            await WriteErrorAsync(context, MapGenError(ex));
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unhandled exception");
            await WriteErrorAsync(
                context,
                StatusCodes.Status500InternalServerError,
                "INTERNAL_ERROR",
                "An unexpected error occurred.");
        }
    }

    private static (int Status, string Code, string Message) MapGenError(GenApiException ex) =>
        ex.StatusCode switch
        {
            401 or 403 => (StatusCodes.Status401Unauthorized, "UNAUTHORIZED", "Authentication failed."),
            404 => (StatusCodes.Status404NotFound, "NOT_FOUND", "Resource not found."),
            >= 500 => (StatusCodes.Status503ServiceUnavailable, "SERVICE_UNAVAILABLE", "Backend service is unavailable."),
            _ => (StatusCodes.Status503ServiceUnavailable, "SERVICE_UNAVAILABLE", "Backend request failed."),
        };

    private static Task WriteErrorAsync(HttpContext context, (int Status, string Code, string Message) error) =>
        WriteErrorAsync(context, error.Status, error.Code, error.Message);

    private static Task WriteErrorAsync(HttpContext context, int status, string code, string message)
    {
        if (context.Response.HasStarted)
        {
            return Task.CompletedTask;
        }

        context.Response.StatusCode = status;
        context.Response.ContentType = "application/json";
        var body = new ApiErrorDto
        {
            Error = new ApiErrorBodyDto
            {
                Code = code,
                Message = message,
                TraceId = context.TraceIdentifier,
            },
        };
        return context.Response.WriteAsJsonAsync(body);
    }
}
