using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace MobileCrm.Adapter.Gen;

public interface IActivityService
{
    Task<GenActivityDetail?> GetDetailAsync(
        GenCredentials credentials,
        string activityId,
        string repUserId,
        CancellationToken ct = default);

    Task<ActivityOperationResult<GenActivityDetail>> StartAsync(
        GenCredentials credentials,
        string activityId,
        string repUserId,
        CancellationToken ct = default);

    Task<ActivityOperationResult<GenActivityDetail>> CompleteAsync(
        GenCredentials credentials,
        string activityId,
        string repUserId,
        string answer,
        string? description,
        string? authorDisplayName = null,
        CancellationToken ct = default);
}

public sealed class ActivityService : IActivityService
{
    private readonly IGenApiClient _gen;
    private readonly GenOptions _options;
    private readonly ILogger<ActivityService> _logger;

    public ActivityService(IGenApiClient gen, IOptions<GenOptions> options, ILogger<ActivityService> logger)
    {
        _gen = gen;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<GenActivityDetail?> GetDetailAsync(
        GenCredentials credentials,
        string activityId,
        string repUserId,
        CancellationToken ct = default)
    {
        _logger.LogInformation(
            "GetDetailAsync activityId={ActivityId} repUserId={RepUserId}",
            activityId,
            repUserId);

        var lookup = await ActivityLookup.LoadAsync(_gen, credentials, activityId, _logger, ct);
        if (lookup is null)
        {
            _logger.LogWarning(
                "GetDetailAsync NotFound: activityId={ActivityId} (no Gen match)",
                activityId);
            return null;
        }

        return await BuildDetailAsync(credentials, lookup, repUserId, ct);
    }

    public async Task<ActivityOperationResult<GenActivityDetail>> StartAsync(
        GenCredentials credentials,
        string activityId,
        string repUserId,
        CancellationToken ct = default)
    {
        var lookup = await ActivityLookup.LoadAsync(_gen, credentials, activityId, _logger, ct);
        if (lookup is null)
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotFound,
                "Activity not found.");
        }

        var preflight = EvaluateTransition(lookup.Root, repUserId, ActivityMapper.CanStart);
        if (preflight is not null)
        {
            return preflight;
        }

        var row = ActivityMapper.ParseDetailRow(lookup.Root);
        var id = string.IsNullOrEmpty(row.Id) ? lookup.CanonicalId : row.Id;
        _logger.LogWarning(
            "[StartDebug] StartAsync preflight id={Id} genStatusRaw={GenStatusRaw} mappedStatus={MappedStatus} firmId={FirmId}",
            id,
            GenJsonHelper.GetInt(lookup.Root, "Status", "status"),
            row.Status,
            row.FirmId);

        var putError = await PutStatusAsync(
            credentials,
            id,
            row.FirmId,
            status: 1,
            answer: null,
            description: null,
            ct);
        if (putError is not null)
        {
            return MapPutError(putError.Value);
        }

        return await RefetchAfterWriteAsync(credentials, id, repUserId, "start", ct);
    }

    public async Task<ActivityOperationResult<GenActivityDetail>> CompleteAsync(
        GenCredentials credentials,
        string activityId,
        string repUserId,
        string answer,
        string? description,
        string? authorDisplayName = null,
        CancellationToken ct = default)
    {
        var lookup = await ActivityLookup.LoadAsync(_gen, credentials, activityId, _logger, ct);
        if (lookup is null)
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotFound,
                "Activity not found.");
        }

        var preflight = EvaluateTransition(lookup.Root, repUserId, ActivityMapper.CanComplete);
        if (preflight is not null)
        {
            return preflight;
        }

        var row = ActivityMapper.ParseDetailRow(lookup.Root);
        var id = string.IsNullOrEmpty(row.Id) ? lookup.CanonicalId : row.Id;
        var mergedAnswer = ActivityMapper.AppendAnswer(
            ActivityMapper.GetAnswer(lookup.Root),
            answer,
            DateTimeOffset.Now,
            authorDisplayName);
        var putError = await PutStatusAsync(
            credentials,
            id,
            row.FirmId,
            status: 2,
            answer: mergedAnswer,
            description: string.IsNullOrWhiteSpace(description) ? null : description.Trim(),
            ct);
        if (putError is not null)
        {
            return MapPutError(putError.Value);
        }

        return await RefetchAfterWriteAsync(credentials, id, repUserId, "complete", ct);
    }

    private async Task<ActivityOperationResult<GenActivityDetail>> RefetchAfterWriteAsync(
        GenCredentials credentials,
        string activityId,
        string repUserId,
        string operation,
        CancellationToken ct)
    {
        var lookup = await ActivityLookup.LoadAsync(_gen, credentials, activityId, _logger, ct);
        if (lookup is not null)
        {
            var genStatusRaw = GenJsonHelper.GetInt(lookup.Root, "Status", "status");
            var mappedStatus = ActivityMapper.MapStatus(genStatusRaw);
            _logger.LogWarning(
                "[StartDebug] Refetch after {Operation} id={Id} strategy={Strategy} genStatusRaw={GenStatusRaw} mappedStatus={MappedStatus} rawPayload={RawPayload}",
                operation,
                activityId,
                lookup.Strategy,
                genStatusRaw,
                mappedStatus,
                FormatJsonElement(lookup.Root));
        }
        else
        {
            _logger.LogWarning(
                "[StartDebug] Refetch after {Operation} id={Id} lookup returned null",
                operation,
                activityId);
        }

        var detail = await GetDetailAsync(credentials, activityId, repUserId, ct);
        if (detail is null)
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotFound,
                "Activity not found after update.");
        }

        _logger.LogWarning(
            "[StartDebug] Mapped detail after {Operation} id={Id} status={Status} canStart={CanStart} canComplete={CanComplete}",
            operation,
            detail.Id,
            detail.Status,
            detail.CanEdit,
            detail.CanComplete);

        return ActivityOperationResult<GenActivityDetail>.Ok(detail);
    }

    private static ActivityOperationResult<GenActivityDetail> MapPutError(ActivityOperationErrorCode code) =>
        ActivityOperationResult<GenActivityDetail>.Fail(
            code,
            code switch
            {
                ActivityOperationErrorCode.GenValidationFailed => "Gen rejected the activity update.",
                _ => "Activity update failed.",
            });

    private async Task<ActivityOperationErrorCode?> PutStatusAsync(
        GenCredentials credentials,
        string id,
        string? firmId,
        int status,
        string? answer,
        string? description,
        CancellationToken ct)
    {
        var body = new Dictionary<string, object?>
        {
            ["ID"] = id,
            ["Status"] = status,
        };

        if (!string.IsNullOrWhiteSpace(firmId))
        {
            body["Firm_ID"] = firmId;
        }

        if (answer is not null)
        {
            body["Answer"] = answer;
        }

        if (description is not null)
        {
            body["Description"] = description;
        }

        var payloadJson = JsonSerializer.Serialize(body, GenJsonHelper.Options);
        _logger.LogWarning(
            "[StartDebug] PutStatusAsync outgoing payload id={Id} path=crmactivities/{ActivityId} body={Payload}",
            id,
            id,
            payloadJson);

        var validateResponse = await _gen.PutAsync(
            $"crmactivities/{id}?validation=true",
            credentials,
            body,
            ct);
        var validateErrorCount = GenValidation.GetErrorCount(validateResponse);
        _logger.LogWarning(
            "[StartDebug] Gen PUT validate response id={Id} errorCount={ErrorCount} genStatusRaw={GenStatusRaw} raw={RawResponse}",
            id,
            validateErrorCount,
            GenJsonHelper.GetInt(validateResponse, "Status", "status"),
            FormatJsonElement(validateResponse));

        if (validateErrorCount > 0)
        {
            _logger.LogWarning(
                "PutStatusAsync Gen validation failed id={Id} status={Status} errorCount={ErrorCount}",
                id,
                status,
                validateErrorCount);
            return ActivityOperationErrorCode.GenValidationFailed;
        }

        // Gen ?validation=true is preview-only; commit requires a second PUT without the flag.
        var commitResponse = await _gen.PutAsync($"crmactivities/{id}", credentials, body, ct);
        var commitErrorCount = GenValidation.GetErrorCount(commitResponse);
        _logger.LogWarning(
            "[StartDebug] Gen PUT commit response id={Id} errorCount={ErrorCount} genStatusRaw={GenStatusRaw} raw={RawResponse}",
            id,
            commitErrorCount,
            GenJsonHelper.GetInt(commitResponse, "Status", "status"),
            FormatJsonElement(commitResponse));

        if (commitErrorCount > 0)
        {
            _logger.LogWarning(
                "PutStatusAsync Gen commit validation failed id={Id} status={Status} errorCount={ErrorCount}",
                id,
                status,
                commitErrorCount);
            return ActivityOperationErrorCode.GenValidationFailed;
        }

        return null;
    }

    private static string FormatJsonElement(JsonElement el, int maxLength = 4000) =>
        el.ValueKind == JsonValueKind.Undefined
            ? "(empty)"
            : TruncateJson(el.GetRawText(), maxLength);

    private static string TruncateJson(string json, int maxLength) =>
        json.Length <= maxLength ? json : json[..maxLength] + "…";

    private static ActivityOperationResult<GenActivityDetail>? EvaluateTransition(
        System.Text.Json.JsonElement root,
        string repUserId,
        Func<string, bool> allowedStatus)
    {
        var row = ActivityMapper.ParseDetailRow(root);
        if (ActivityMapper.IsTerminalStatus(row.Status))
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotEditable,
                "Activity is already completed.");
        }

        if (!ActivityMapper.IsOwnedByRepresentative(root, repUserId))
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotEditable,
                "Activity is not assigned to you.");
        }

        if (!allowedStatus(row.Status))
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotEditable,
                "Activity is not in a valid state for this action.");
        }

        return null;
    }

    private async Task<GenActivityDetail?> BuildDetailAsync(
        GenCredentials credentials,
        ActivityLookupResult lookup,
        string repUserId,
        CancellationToken ct)
    {
        var root = lookup.Root;
        var row = ActivityMapper.ParseDetailRow(root);
        if (string.IsNullOrEmpty(row.Id))
        {
            row = row with { Id = lookup.CanonicalId };
        }

        var status = row.Status;
        var owned = ActivityMapper.IsOwnedByRepresentative(root, repUserId);
        var terminal = ActivityMapper.IsTerminalStatus(status);
        var canStart = !terminal && owned && ActivityMapper.CanStart(status);
        var canComplete = !terminal && owned && ActivityMapper.CanComplete(status);

        _logger.LogInformation(
            "BuildDetailAsync id={Id} status={Status} owned={Owned} canStart={CanStart} canComplete={CanComplete}",
            row.Id,
            status,
            owned,
            canStart,
            canComplete);

        var firm = await ResolveFirmAsync(credentials, row.FirmId, ct)
            ?? new GenFirmSummary("", "Unknown customer", "", null, null, "unknown");

        GenContactSummary? contact = null;
        var personId = ActivityMapper.GetPersonId(root);
        if (!string.IsNullOrWhiteSpace(personId) && personId is not "0000000000" and not "__________")
        {
            contact = await ResolveContactAsync(credentials, personId, ct);
        }

        var typeName = await ResolveActivityTypeNameAsync(credentials, row.ActivityTypeId, ct);

        return new GenActivityDetail(
            row.Id,
            row.DocumentNumber,
            row.Subject,
            ActivityMapper.GetDescription(root) ?? "",
            ActivityMapper.GetAnswer(root) ?? "",
            status,
            row.ActivityTypeId,
            typeName,
            row.ScheduledStart,
            row.ScheduledEnd,
            firm,
            contact,
            ActivityMapper.GetOwnerId(root),
            canStart,
            canComplete);
    }

    private async Task<GenFirmSummary?> ResolveFirmAsync(
        GenCredentials credentials,
        string? firmId,
        CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(firmId))
        {
            return null;
        }

        try
        {
            var select = Uri.EscapeDataString(_options.FirmListSelect);
            var root = await _gen.GetAsync($"firms/{firmId}?select={select}", credentials, ct);
            return FirmMapper.ToSummary(root);
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "Failed to resolve firm {FirmId} for activity", firmId);
            return new GenFirmSummary(firmId, "Customer", "", null, null, "unknown");
        }
    }

    private async Task<GenContactSummary?> ResolveContactAsync(
        GenCredentials credentials,
        string personId,
        CancellationToken ct)
    {
        try
        {
            var select = Uri.EscapeDataString(_options.PersonContactSelect);
            var root = await _gen.GetAsync($"persons/{personId}?select={select}", credentials, ct);
            var person = FirmService.ParsePersonContact(root);
            if (person is null || person.Hidden || person.IsEmployee)
            {
                return null;
            }

            return new GenContactSummary(
                person.Id,
                person.DisplayName ?? $"{person.FirstName} {person.LastName}".Trim(),
                person.FirstName,
                person.LastName,
                person.JobTitle,
                false,
                person.Address?.Phone1,
                person.Address?.Email);
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "Failed to resolve person {PersonId} for activity", personId);
            return null;
        }
    }

    private async Task<string?> ResolveActivityTypeNameAsync(
        GenCredentials credentials,
        string? typeId,
        CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(typeId))
        {
            return null;
        }

        try
        {
            var root = await _gen.GetAsync(
                $"crmactivitytypes/{typeId}?select=ID,Name,Code",
                credentials,
                ct);
            return GenJsonHelper.GetString(root, "Name", "name")
                ?? GenJsonHelper.GetString(root, "Code", "code");
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "Failed to resolve activity type {TypeId}", typeId);
            return null;
        }
    }
}
