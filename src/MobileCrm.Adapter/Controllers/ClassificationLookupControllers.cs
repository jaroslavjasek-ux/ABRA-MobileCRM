using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/activity-areas")]
public sealed class ActivityAreasController : ControllerBase
{
    private readonly IClassificationLookupService _classification;

    public ActivityAreasController(IClassificationLookupService classification) => _classification = classification;

    [HttpGet]
    public async Task<ActionResult<PagedResultDto<ClassificationSummaryDto>>> Search(
        [FromQuery] string? q,
        [FromQuery] int take = 30,
        [FromQuery] int skip = 0,
        CancellationToken ct = default)
    {
        return await SearchAsync(ClassificationKind.Area, q, take, skip, ct);
    }

    private async Task<ActionResult<PagedResultDto<ClassificationSummaryDto>>> SearchAsync(
        ClassificationKind kind,
        string? q,
        int take,
        int skip,
        CancellationToken ct)
    {
        var session = GetSession();
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var result = await _classification.SearchAsync(session.Credentials, kind, q, take, skip, ct);

        return Ok(new PagedResultDto<ClassificationSummaryDto>
        {
            Items = result.Items.Select(ApiMapping.ToDto).ToList(),
            Total = result.Total,
            HasMore = result.HasMore,
        });
    }

    private UserSession GetSession() =>
        HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
        ?? throw new InvalidOperationException("Session missing");
}

[ApiController]
[Route("api/v1/activity-types")]
public sealed class ActivityTypesController : ControllerBase
{
    private readonly IClassificationLookupService _classification;

    public ActivityTypesController(IClassificationLookupService classification) => _classification = classification;

    [HttpGet]
    public async Task<ActionResult<PagedResultDto<ClassificationSummaryDto>>> Search(
        [FromQuery] string? q,
        [FromQuery] int take = 30,
        [FromQuery] int skip = 0,
        CancellationToken ct = default)
    {
        var session = GetSession();
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var result = await _classification.SearchAsync(
            session.Credentials,
            ClassificationKind.Type,
            q,
            take,
            skip,
            ct);

        return Ok(new PagedResultDto<ClassificationSummaryDto>
        {
            Items = result.Items.Select(ApiMapping.ToDto).ToList(),
            Total = result.Total,
            HasMore = result.HasMore,
        });
    }

    private UserSession GetSession() =>
        HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
        ?? throw new InvalidOperationException("Session missing");
}

[ApiController]
[Route("api/v1/activity-queues")]
public sealed class ActivityQueuesController : ControllerBase
{
    private readonly IClassificationLookupService _classification;

    public ActivityQueuesController(IClassificationLookupService classification) => _classification = classification;

    [HttpGet]
    public async Task<ActionResult<PagedResultDto<ClassificationSummaryDto>>> Search(
        [FromQuery] string? q,
        [FromQuery] int take = 30,
        [FromQuery] int skip = 0,
        CancellationToken ct = default)
    {
        var session = GetSession();
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var result = await _classification.SearchAsync(
            session.Credentials,
            ClassificationKind.Queue,
            q,
            take,
            skip,
            ct);

        return Ok(new PagedResultDto<ClassificationSummaryDto>
        {
            Items = result.Items.Select(ApiMapping.ToDto).ToList(),
            Total = result.Total,
            HasMore = result.HasMore,
        });
    }

    private UserSession GetSession() =>
        HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
        ?? throw new InvalidOperationException("Session missing");
}
