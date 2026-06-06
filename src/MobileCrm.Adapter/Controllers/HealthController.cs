using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Gen;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("health")]
public sealed class HealthController : ControllerBase
{
    [HttpGet]
    public IActionResult Get() => Ok(new { status = "healthy" });

    [HttpGet("ready")]
    public async Task<IActionResult> Ready(
        [FromServices] IGenApiClient gen,
        [FromServices] IConfiguration config,
        CancellationToken ct)
    {
        var user = config["Gen:SmokeTest:LoginName"];
        var password = config["Gen:SmokeTest:Password"];
        if (string.IsNullOrWhiteSpace(user) || string.IsNullOrWhiteSpace(password))
        {
            return Ok(new { status = "ready", gen = "skipped" });
        }

        var ok = await gen.PingAsync(new GenCredentials { LoginName = user, Password = password }, ct);
        return ok
            ? Ok(new { status = "ready", gen = "ok" })
            : StatusCode(503, new { status = "degraded", gen = "failed" });
    }
}
