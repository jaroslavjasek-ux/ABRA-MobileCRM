using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace MobileCrm.Adapter.Gen;

public interface IClassificationValidateProbeService
{
    Task<GenClassificationSearchResult> FilterTypesForAreaAsync(
        GenCredentials credentials,
        string repUserId,
        string areaId,
        string? query,
        int take,
        int skip,
        CancellationToken ct = default);

    Task<GenClassificationSearchResult> FilterQueuesForAreaAndTypeAsync(
        GenCredentials credentials,
        string repUserId,
        string areaId,
        string activityTypeId,
        string? query,
        int take,
        int skip,
        CancellationToken ct = default);
}

public sealed class ClassificationValidateProbeService : IClassificationValidateProbeService
{
    private readonly IGenApiClient _gen;
    private readonly IClassificationLookupService _catalog;
    private readonly GenOptions _options;
    private readonly ILogger<ClassificationValidateProbeService> _logger;

    public ClassificationValidateProbeService(
        IGenApiClient gen,
        IClassificationLookupService catalog,
        IOptions<GenOptions> options,
        ILogger<ClassificationValidateProbeService> logger)
    {
        _gen = gen;
        _catalog = catalog;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<GenClassificationSearchResult> FilterTypesForAreaAsync(
        GenCredentials credentials,
        string repUserId,
        string areaId,
        string? query,
        int take,
        int skip,
        CancellationToken ct = default)
    {
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var catalog = await _catalog.SearchAsync(credentials, ClassificationKind.Type, query, take: 50, skip: 0, ct);
        var probeQueueId = await ResolveProbeQueueIdAsync(credentials, ct);
        if (probeQueueId is null)
        {
            _logger.LogWarning("Classification type probe skipped — no queues in catalog");
            return EmptyResult();
        }

        var allowed = new List<GenClassificationRow>();
        foreach (var candidate in catalog.Items)
        {
            if (await IsTypeAllowedForAreaAsync(credentials, repUserId, areaId, candidate.Id, probeQueueId, ct))
            {
                allowed.Add(candidate);
            }
        }

        return PageResult(allowed, take, skip);
    }

    public async Task<GenClassificationSearchResult> FilterQueuesForAreaAndTypeAsync(
        GenCredentials credentials,
        string repUserId,
        string areaId,
        string activityTypeId,
        string? query,
        int take,
        int skip,
        CancellationToken ct = default)
    {
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var catalog = await _catalog.SearchAsync(credentials, ClassificationKind.Queue, query, take: 50, skip: 0, ct);
        var includeObchDates = await TypeRequiresObchDatesAsync(credentials, activityTypeId, ct);

        var allowed = new List<GenClassificationRow>();
        foreach (var candidate in catalog.Items)
        {
            if (await IsQueueAllowedAsync(
                    credentials,
                    repUserId,
                    areaId,
                    activityTypeId,
                    candidate.Id,
                    includeObchDates,
                    ct))
            {
                allowed.Add(candidate);
            }
        }

        return PageResult(allowed, take, skip);
    }

    private async Task<bool> IsTypeAllowedForAreaAsync(
        GenCredentials credentials,
        string repUserId,
        string areaId,
        string typeId,
        string probeQueueId,
        CancellationToken ct)
    {
        var body = BuildProbeBody(repUserId, areaId, typeId, probeQueueId, includeObchDates: false);
        var response = await ValidateAsync(credentials, body, ct);
        if (response is null)
        {
            return false;
        }

        if (GenValidation.HasFieldError(response.Value, "activitytype_id"))
        {
            return false;
        }

        var resolvedTypeId = GenJsonHelper.GetString(response.Value, "ActivityType_ID", "activitytype_id");
        return string.IsNullOrWhiteSpace(resolvedTypeId)
            || string.Equals(resolvedTypeId, typeId, StringComparison.OrdinalIgnoreCase);
    }

    private async Task<bool> IsQueueAllowedAsync(
        GenCredentials credentials,
        string repUserId,
        string areaId,
        string typeId,
        string queueId,
        bool includeObchDates,
        CancellationToken ct)
    {
        var body = BuildProbeBody(repUserId, areaId, typeId, queueId, includeObchDates);
        var response = await ValidateAsync(credentials, body, ct);
        if (response is null)
        {
            return false;
        }

        if (GenValidation.HasFieldError(response.Value, "actqueue_id"))
        {
            return false;
        }

        var resolvedQueueId = GenJsonHelper.GetString(response.Value, "ActQueue_ID", "actqueue_id");
        return string.IsNullOrWhiteSpace(resolvedQueueId)
            || string.Equals(resolvedQueueId, queueId, StringComparison.OrdinalIgnoreCase);
    }

    private async Task<JsonElement?> ValidateAsync(
        GenCredentials credentials,
        Dictionary<string, object?> body,
        CancellationToken ct)
    {
        try
        {
            return await _gen.PostAsync("crmactivities?validation=true", credentials, body, ct);
        }
        catch (GenApiException ex)
        {
            _logger.LogDebug(ex, "Classification validate probe HTTP {Status}", ex.StatusCode);
            if (GenValidation.TryParseResponseBody(ex.Body, out var root))
            {
                return root;
            }

            return null;
        }
    }

    private Dictionary<string, object?> BuildProbeBody(
        string repUserId,
        string areaId,
        string typeId,
        string queueId,
        bool includeObchDates)
    {
        var divisionId = _options.ReferenceDefaults.DivisionId;
        var solverRoleId = _options.ReferenceDefaults.SolverRoleId;
        if (string.IsNullOrWhiteSpace(divisionId)
            || string.IsNullOrWhiteSpace(solverRoleId)
            || string.IsNullOrWhiteSpace(_options.ClassificationProbeFirmId))
        {
            throw new InvalidOperationException(
                "Gen classification probe requires ReferenceDefaults.DivisionId, SolverRoleId, and ClassificationProbeFirmId.");
        }

        var scheduled = DateTimeOffset.UtcNow.AddDays(2);
        var body = new Dictionary<string, object?>
        {
            ["Subject"] = "Classification validate probe",
            ["Firm_ID"] = _options.ClassificationProbeFirmId.Trim(),
            ["SheduledStart$DATE"] = scheduled.ToString("o"),
            ["ResponsibleUser_ID"] = repUserId.Trim(),
            ["SolverUser_ID"] = repUserId.Trim(),
            ["Division_ID"] = divisionId!.Trim(),
            ["SolverRole_ID"] = solverRoleId!.Trim(),
            ["ActivityArea_ID"] = areaId.Trim(),
            ["ActivityType_ID"] = typeId.Trim(),
            ["ActQueue_ID"] = queueId.Trim(),
        };

        if (includeObchDates)
        {
            var nextContact = scheduled.AddDays(30);
            var tradeDate = scheduled.AddDays(60);
            body["NextContact$DATE"] = nextContact.ToString("o");
            body["TradeDate$DATE"] = tradeDate.ToString("o");
        }

        return body;
    }

    private async Task<string?> ResolveProbeQueueIdAsync(GenCredentials credentials, CancellationToken ct)
    {
        var queues = await _catalog.SearchAsync(credentials, ClassificationKind.Queue, query: null, take: 1, skip: 0, ct);
        return queues.Items.FirstOrDefault()?.Id;
    }

    private async Task<bool> TypeRequiresObchDatesAsync(
        GenCredentials credentials,
        string activityTypeId,
        CancellationToken ct)
    {
        try
        {
            var detail = await _gen.GetAsync($"crmactivitytypes/{activityTypeId.Trim()}", credentials, ct);
            var issheduled = GenJsonHelper.GetBool(detail, "issheduled", "IsSheduled");
            return issheduled == true;
        }
        catch (GenApiException ex)
        {
            _logger.LogDebug(ex, "Type detail probe failed for {TypeId}", activityTypeId);
            return false;
        }
    }

    private static GenClassificationSearchResult PageResult(
        IReadOnlyList<GenClassificationRow> allowed,
        int take,
        int skip)
    {
        var page = allowed.Skip(skip).Take(take).ToList();
        return new GenClassificationSearchResult(page, allowed.Count, skip + page.Count < allowed.Count);
    }

    private static GenClassificationSearchResult EmptyResult() =>
        new([], 0, false);
}
