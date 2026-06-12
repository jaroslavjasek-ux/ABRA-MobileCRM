using System.Text.Json;
using Microsoft.Extensions.Options;

namespace MobileCrm.Adapter.Gen;

public sealed record ActivityReferenceDefaults(
    string ActQueueId,
    string PeriodId,
    string DivisionId,
    string SolverRoleId,
    string ActivityAreaId,
    string ActivityTypeId);

public sealed record StandaloneActivityDefaults(
    string DivisionId,
    string SolverRoleId,
    string? ActQueueId,
    string? ActivityAreaId,
    string? ActivityTypeId);

public interface IReferenceDefaultsService
{
    bool TryGetConfiguredDefaults(out ActivityReferenceDefaults defaults);

    bool TryGetStandaloneDefaults(out StandaloneActivityDefaults defaults);

    void ApplyConfiguredDefaults(Dictionary<string, object?> body, ActivityReferenceDefaults defaults);

    void MergeFromValidateResponse(Dictionary<string, object?> body, JsonElement validateResponse);
}

public sealed class ReferenceDefaultsService : IReferenceDefaultsService
{
    private static readonly IReadOnlyDictionary<string, string> MergeFieldMap =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["activityarea_id"] = "ActivityArea_ID",
            ["actqueue_id"] = "ActQueue_ID",
            ["period_id"] = "Period_ID",
            ["division_id"] = "Division_ID",
            ["solverrole_id"] = "SolverRole_ID",
            ["activitytype_id"] = "ActivityType_ID",
        };

    private readonly GenOptions _options;

    public ReferenceDefaultsService(IOptions<GenOptions> options)
    {
        _options = options.Value;
    }

    public bool TryGetConfiguredDefaults(out ActivityReferenceDefaults defaults)
    {
        var configured = _options.ReferenceDefaults;
        if (string.IsNullOrWhiteSpace(configured.ActQueueId)
            || string.IsNullOrWhiteSpace(configured.PeriodId)
            || string.IsNullOrWhiteSpace(configured.DivisionId)
            || string.IsNullOrWhiteSpace(configured.SolverRoleId)
            || string.IsNullOrWhiteSpace(configured.ActivityAreaId)
            || string.IsNullOrWhiteSpace(configured.ActivityTypeId))
        {
            defaults = default!;
            return false;
        }

        defaults = new ActivityReferenceDefaults(
            configured.ActQueueId.Trim(),
            configured.PeriodId.Trim(),
            configured.DivisionId.Trim(),
            configured.SolverRoleId.Trim(),
            configured.ActivityAreaId.Trim(),
            configured.ActivityTypeId.Trim());
        return true;
    }

    public bool TryGetStandaloneDefaults(out StandaloneActivityDefaults defaults)
    {
        var configured = _options.ReferenceDefaults;
        if (string.IsNullOrWhiteSpace(configured.DivisionId)
            || string.IsNullOrWhiteSpace(configured.SolverRoleId))
        {
            defaults = default!;
            return false;
        }

        defaults = new StandaloneActivityDefaults(
            configured.DivisionId.Trim(),
            configured.SolverRoleId.Trim(),
            NullIfWhiteSpace(configured.ActQueueId),
            NullIfWhiteSpace(configured.ActivityAreaId),
            NullIfWhiteSpace(configured.ActivityTypeId));
        return true;
    }

    public void ApplyConfiguredDefaults(Dictionary<string, object?> body, ActivityReferenceDefaults defaults)
    {
        body["ActQueue_ID"] = defaults.ActQueueId;
        body["Period_ID"] = defaults.PeriodId;
        body["Division_ID"] = defaults.DivisionId;
        body["SolverRole_ID"] = defaults.SolverRoleId;
        body["ActivityArea_ID"] = defaults.ActivityAreaId;
        body["ActivityType_ID"] = defaults.ActivityTypeId;
    }

    public void MergeFromValidateResponse(Dictionary<string, object?> body, JsonElement validateResponse)
    {
        foreach (var (sourceKey, destinationKey) in MergeFieldMap)
        {
            var value = GenJsonHelper.GetString(validateResponse, destinationKey, sourceKey);
            if (!string.IsNullOrWhiteSpace(value))
            {
                body[destinationKey] = value;
            }
        }
    }

    private static string? NullIfWhiteSpace(string? value) =>
        string.IsNullOrWhiteSpace(value) ? null : value.Trim();
}
