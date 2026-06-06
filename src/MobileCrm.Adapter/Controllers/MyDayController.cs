using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/my-day")]
public sealed class MyDayController : ControllerBase
{
    private readonly IMyDayService _myDay;
    private readonly IRepresentativeService _representatives;

    public MyDayController(IMyDayService myDay, IRepresentativeService representatives)
    {
        _myDay = myDay;
        _representatives = representatives;
    }

    [HttpGet]
    public async Task<ActionResult<MyDayResponseDto>> Get(
        [FromQuery] string? date,
        [FromQuery] int take = 50,
        CancellationToken ct = default)
    {
        var session = HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
            ?? throw new InvalidOperationException("Session missing");

        var agendaDate = ParseDate(date) ?? DateOnly.FromDateTime(DateTime.Today);
        take = Math.Clamp(take, 1, 50);

        var slice = await _myDay.GetMyDayAsync(session.Credentials, session.RepUserId, agendaDate, take, ct);
        var firmIds = slice.Today.Select(a => a.FirmId)
            .Concat(slice.Overdue.Select(a => a.FirmId));
        var firmNames = await _myDay.ResolveFirmNamesAsync(session.Credentials, firmIds, ct);

        var today = slice.Today
            .Select(a => ApiMapping.ToActivitySummary(a, firmNames, isOverdue: false))
            .ToList();
        var overdue = slice.Overdue
            .Select(a => ApiMapping.ToActivitySummary(a, firmNames, isOverdue: true))
            .ToList();

        var representative = await _representatives.GetCurrentUserAsync(session.Credentials, ct);

        return Ok(new MyDayResponseDto
        {
            Date = agendaDate.ToString("yyyy-MM-dd"),
            Representative = ApiMapping.ToDto(representative),
            Today = today,
            Overdue = overdue,
            TodayCount = today.Count,
            OverdueCount = overdue.Count,
            Meta = new { schemaVersion = "1.0" },
        });
    }

    private static DateOnly? ParseDate(string? value) =>
        string.IsNullOrWhiteSpace(value) ? null : DateOnly.TryParse(value, out var d) ? d : null;
}
