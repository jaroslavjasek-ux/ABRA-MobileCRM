using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/firms")]
public sealed class FirmsController : ControllerBase
{
    private readonly IFirmService _firms;

    public FirmsController(IFirmService firms) => _firms = firms;

    [HttpGet]
    public async Task<ActionResult<PagedResultDto<FirmSummaryDto>>> Search(
        [FromQuery] string? q,
        [FromQuery] int take = 20,
        [FromQuery] int skip = 0,
        CancellationToken ct = default)
    {
        var session = GetSession();
        var term = (q ?? "").Trim();
        if (term.Length < 2)
        {
            return Ok(new PagedResultDto<FirmSummaryDto>
            {
                Items = [],
                Total = 0,
                HasMore = false,
            });
        }

        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var result = await _firms.SearchAsync(session.Credentials, term, take, skip, ct);
        return Ok(new PagedResultDto<FirmSummaryDto>
        {
            Items = result.Items.Select(ApiMapping.ToDto).ToList(),
            Total = result.Total,
            HasMore = result.HasMore,
        });
    }

    [HttpGet("{firmId}")]
    public async Task<ActionResult<FirmDetailResponseDto>> GetDetail(
        string firmId,
        [FromQuery] int recentTake = 10,
        CancellationToken ct = default)
    {
        var session = GetSession();
        recentTake = Math.Clamp(recentTake, 1, 20);

        var detail = await _firms.GetDetailAsync(session.Credentials, firmId, recentTake, ct);
        if (detail is null)
        {
            return NotFound();
        }

        return Ok(ApiMapping.ToDto(detail));
    }

    private UserSession GetSession() =>
        HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
        ?? throw new InvalidOperationException("Session missing");
}
