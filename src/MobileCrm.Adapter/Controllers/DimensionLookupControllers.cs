using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/business-cases")]
public sealed class BusinessCasesController : ControllerBase
{
    private readonly IDimensionLookupService _dimensions;

    public BusinessCasesController(IDimensionLookupService dimensions) => _dimensions = dimensions;

    [HttpGet]
    public async Task<ActionResult<PagedResultDto<DimensionSummaryDto>>> Search(
        [FromQuery] string? q,
        [FromQuery] string? firmId,
        [FromQuery] int take = 30,
        [FromQuery] int skip = 0,
        CancellationToken ct = default)
    {
        var session = GetSession();
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var result = await _dimensions.SearchAsync(
            session.Credentials,
            DimensionKind.BusinessCase,
            q,
            firmId,
            take,
            skip,
            ct);

        return Ok(new PagedResultDto<DimensionSummaryDto>
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
[Route("api/v1/work-orders")]
public sealed class WorkOrdersController : ControllerBase
{
    private readonly IDimensionLookupService _dimensions;

    public WorkOrdersController(IDimensionLookupService dimensions) => _dimensions = dimensions;

    [HttpGet]
    public async Task<ActionResult<PagedResultDto<DimensionSummaryDto>>> Search(
        [FromQuery] string? q,
        [FromQuery] string? firmId,
        [FromQuery] int take = 30,
        [FromQuery] int skip = 0,
        CancellationToken ct = default)
    {
        var session = GetSession();
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var result = await _dimensions.SearchAsync(
            session.Credentials,
            DimensionKind.WorkOrder,
            q,
            firmId,
            take,
            skip,
            ct);

        return Ok(new PagedResultDto<DimensionSummaryDto>
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
[Route("api/v1/projects")]
public sealed class ProjectsController : ControllerBase
{
    private readonly IDimensionLookupService _dimensions;

    public ProjectsController(IDimensionLookupService dimensions) => _dimensions = dimensions;

    [HttpGet]
    public async Task<ActionResult<PagedResultDto<DimensionSummaryDto>>> Search(
        [FromQuery] string? q,
        [FromQuery] string? firmId,
        [FromQuery] int take = 30,
        [FromQuery] int skip = 0,
        CancellationToken ct = default)
    {
        var session = GetSession();
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var result = await _dimensions.SearchAsync(
            session.Credentials,
            DimensionKind.Project,
            q,
            firmId,
            take,
            skip,
            ct);

        return Ok(new PagedResultDto<DimensionSummaryDto>
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
