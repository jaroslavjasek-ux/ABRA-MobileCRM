using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/session")]
public sealed class SessionController : ControllerBase
{
    private readonly ISessionStore _sessions;
    private readonly IRepresentativeService _representatives;
    private readonly IGenApiClient _gen;

    public SessionController(
        ISessionStore sessions,
        IRepresentativeService representatives,
        IGenApiClient gen)
    {
        _sessions = sessions;
        _representatives = representatives;
        _gen = gen;
    }

    [HttpPost]
    public async Task<ActionResult<SessionResponseDto>> Login([FromBody] LoginRequestDto request, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(request.LoginName) || string.IsNullOrWhiteSpace(request.Password))
        {
            return BadRequestError("VALIDATION_FAILED", "loginName and password are required.");
        }

        var credentials = new GenCredentials
        {
            LoginName = request.LoginName.Trim(),
            Password = request.Password,
        };

        try
        {
            var profile = await _representatives.GetCurrentUserAsync(credentials, ct);
            var session = _sessions.Create(credentials, profile.Id);
            return Ok(BuildResponse(profile, session.Token));
        }
        catch (GenApiException ex) when (ex.StatusCode is 401 or 403)
        {
            return UnauthorizedError();
        }
    }

    [HttpGet]
    public async Task<ActionResult<SessionResponseDto>> GetSession(CancellationToken ct)
    {
        var session = GetRequiredSession();
        try
        {
            var profile = await _representatives.GetCurrentUserAsync(session.Credentials, ct);
            return Ok(BuildResponse(profile, session.Token));
        }
        catch (GenApiException ex) when (ex.StatusCode is 401 or 403)
        {
            _sessions.Remove(session.Token);
            return UnauthorizedError();
        }
    }

    [HttpDelete]
    public IActionResult Logout()
    {
        var session = GetRequiredSession();
        _sessions.Remove(session.Token);
        return NoContent();
    }

    private UserSession GetRequiredSession() =>
        HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
        ?? throw new InvalidOperationException("Session missing");

    private static SessionResponseDto BuildResponse(RepresentativeProfile profile, string token) => new()
    {
        Representative = ApiMapping.ToDto(profile),
        SessionToken = token,
        ExpiresAt = null,
        Capabilities = new[] { "activities.read", "activities.write", "firms.read" },
        Provider = new BackendProviderDto { Name = "abra-gen", Version = "demo" },
    };

    private ActionResult UnauthorizedError() =>
        Unauthorized(new ApiErrorDto
        {
            Error = new ApiErrorBodyDto
            {
                Code = "UNAUTHORIZED",
                Message = "Invalid credentials or session.",
                TraceId = HttpContext.TraceIdentifier,
            },
        });

    private ActionResult BadRequestError(string code, string message) =>
        BadRequest(new ApiErrorDto
        {
            Error = new ApiErrorBodyDto
            {
                Code = code,
                Message = message,
                TraceId = HttpContext.TraceIdentifier,
            },
        });
}
