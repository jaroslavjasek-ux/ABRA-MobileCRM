using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/users")]
public sealed class UsersController : ControllerBase
{
    private readonly IUserLookupService _users;

    public UsersController(IUserLookupService users) => _users = users;

    [HttpGet]
    public async Task<ActionResult<PagedResultDto<SalesRepresentativeDto>>> Search(
        [FromQuery] string? q,
        [FromQuery] int take = 30,
        CancellationToken ct = default)
    {
        var session = GetSession();
        take = Math.Clamp(take, 1, 50);

        var items = await _users.SearchAsync(session.Credentials, q, take, ct);
        return Ok(new PagedResultDto<SalesRepresentativeDto>
        {
            Items = items.Select(ToDto).ToList(),
            Total = items.Count,
            HasMore = false,
        });
    }

    private static SalesRepresentativeDto ToDto(GenUserSummary user) => new()
    {
        Id = user.Id,
        LoginName = user.LoginName,
        DisplayName = user.DisplayName,
    };

    private UserSession GetSession() =>
        HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
        ?? throw new InvalidOperationException("Session missing");
}
