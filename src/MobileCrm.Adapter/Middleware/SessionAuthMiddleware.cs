using MobileCrm.Adapter.Auth;

namespace MobileCrm.Adapter.Middleware;

public sealed class SessionAuthMiddleware
{
    private readonly RequestDelegate _next;

    public SessionAuthMiddleware(RequestDelegate next) => _next = next;

    public async Task InvokeAsync(HttpContext context, ISessionStore sessions)
    {
        if (IsAnonymousPath(context))
        {
            await _next(context);
            return;
        }

        var token = ExtractBearerToken(context.Request.Headers.Authorization.ToString());
        if (string.IsNullOrEmpty(token))
        {
            await WriteUnauthorizedAsync(context);
            return;
        }

        var session = sessions.Get(token);
        if (session is null)
        {
            await WriteUnauthorizedAsync(context);
            return;
        }

        context.Items[SessionConstants.HttpContextItemKey] = session;
        await _next(context);
    }

    private static bool IsAnonymousPath(HttpContext context)
    {
        var value = context.Request.Path.Value ?? "";
        if (value.StartsWith("/health", StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        if (context.Request.Method.Equals("POST", StringComparison.OrdinalIgnoreCase)
            && (value.Equals("/api/v1/session", StringComparison.OrdinalIgnoreCase)
                || value.Equals("/session", StringComparison.OrdinalIgnoreCase)))
        {
            return true;
        }

        return false;
    }

    private static string? ExtractBearerToken(string? authorization)
    {
        if (string.IsNullOrWhiteSpace(authorization))
        {
            return null;
        }

        const string prefix = "Bearer ";
        if (!authorization.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        return authorization[prefix.Length..].Trim();
    }

    private static Task WriteUnauthorizedAsync(HttpContext context)
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        context.Response.ContentType = "application/json";
        return context.Response.WriteAsJsonAsync(new Models.ApiErrorDto
        {
            Error = new Models.ApiErrorBodyDto
            {
                Code = "UNAUTHORIZED",
                Message = "Session is invalid or expired.",
                TraceId = context.TraceIdentifier,
            },
        });
    }
}
