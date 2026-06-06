using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace MobileCrm.Adapter.Gen;

public sealed record MyDaySlice(IReadOnlyList<GenActivityRow> Today, IReadOnlyList<GenActivityRow> Overdue);

public interface IMyDayService
{
    Task<MyDaySlice> GetMyDayAsync(GenCredentials credentials, string repUserId, DateOnly agendaDate, int take, CancellationToken ct = default);
    Task<IReadOnlyDictionary<string, string>> ResolveFirmNamesAsync(
        GenCredentials credentials,
        IEnumerable<string?> firmIds,
        CancellationToken ct = default);
}

public sealed class MyDayService : IMyDayService
{
    private readonly IGenApiClient _gen;
    private readonly GenOptions _options;
    private readonly ILogger<MyDayService> _logger;

    public MyDayService(IGenApiClient gen, IOptions<GenOptions> options, ILogger<MyDayService> logger)
    {
        _gen = gen;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<MyDaySlice> GetMyDayAsync(
        GenCredentials credentials,
        string repUserId,
        DateOnly agendaDate,
        int take,
        CancellationToken ct = default)
    {
        var query = ActivityMapper.BuildActivitiesQuery(repUserId, Math.Min(take * 4, 200));
        var root = await _gen.GetAsync(query, credentials, ct);
        var all = ActivityMapper.ParseList(root);

        var tz = TimeZoneInfo.FindSystemTimeZoneById(_options.TimeZoneId);
        var localMidnight = agendaDate.ToDateTime(TimeOnly.MinValue);
        var dayStart = new DateTimeOffset(localMidnight, tz.GetUtcOffset(localMidnight));
        var dayEnd = dayStart.AddDays(1);

        var today = new List<GenActivityRow>();
        var overdue = new List<GenActivityRow>();

        foreach (var row in all)
        {
            if (!ActivityMapper.IsOpenStatus(row.Status))
            {
                continue;
            }

            if (!row.ScheduledStart.HasValue)
            {
                continue;
            }

            var start = row.ScheduledStart.Value;
            if (start >= dayStart && start < dayEnd)
            {
                if (today.Count < take)
                {
                    today.Add(row);
                }
            }
            else if (start < dayStart)
            {
                if (overdue.Count < take)
                {
                    overdue.Add(row);
                }
            }
        }

        today.Sort((a, b) => CompareStart(a, b));
        overdue.Sort((a, b) => CompareStart(a, b));

        _logger.LogInformation(
            "MyDay for {RepId} on {Date}: {TodayCount} today, {OverdueCount} overdue (from {Total} fetched)",
            repUserId,
            agendaDate,
            today.Count,
            overdue.Count,
            all.Count);

        return new MyDaySlice(today, overdue);
    }

    public async Task<IReadOnlyDictionary<string, string>> ResolveFirmNamesAsync(
        GenCredentials credentials,
        IEnumerable<string?> firmIds,
        CancellationToken ct = default)
    {
        var map = new Dictionary<string, string>();
        foreach (var firmId in firmIds.Where(id => !string.IsNullOrWhiteSpace(id)).Distinct())
        {
            try
            {
                var root = await _gen.GetAsync(
                    $"firms/{firmId}?select=ID,Name",
                    credentials,
                    ct);
                var name = GenJsonHelper.GetString(root, "Name", "name");
                if (!string.IsNullOrEmpty(name))
                {
                    map[firmId!] = name;
                }
            }
            catch (GenApiException ex)
            {
                _logger.LogWarning(ex, "Failed to resolve firm name for {FirmId}", firmId);
            }
        }

        return map;
    }

    private static int CompareStart(GenActivityRow a, GenActivityRow b)
    {
        var sa = a.ScheduledStart ?? DateTimeOffset.MinValue;
        var sb = b.ScheduledStart ?? DateTimeOffset.MinValue;
        return sa.CompareTo(sb);
    }
}
