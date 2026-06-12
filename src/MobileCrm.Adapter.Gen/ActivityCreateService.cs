using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace MobileCrm.Adapter.Gen;

public sealed record CreateActivityCommand(
    string SourceActivityId,
    string Subject,
    DateTimeOffset ScheduledStart,
    string? Description,
    string? AssignedUserId = null,
    string? SourceDescription = null,
    string? SourceAnswer = null);

public sealed record StandaloneCreateActivityCommand(
    string Subject,
    DateTimeOffset ScheduledStart,
    string FirmId,
    string? ContactPersonId,
    string? Description,
    string AssignedUserId,
    string? BusinessCaseId = null,
    string? WorkOrderId = null,
    string? ProjectId = null,
    string? ActivityAreaId = null,
    string? ActivityTypeId = null,
    string? ActQueueId = null);

public interface IActivityCreateService
{
    Task<ActivityOperationResult<GenActivityDetail>> CreateAsync(
        GenCredentials credentials,
        string repUserId,
        CreateActivityCommand command,
        CancellationToken ct = default);

    Task<ActivityOperationResult<GenActivityDetail>> CreateStandaloneAsync(
        GenCredentials credentials,
        string repUserId,
        StandaloneCreateActivityCommand command,
        CancellationToken ct = default);
}

public sealed class ActivityCreateService : IActivityCreateService
{
    private const int MaxValidateRounds = 3;

    private readonly IGenApiClient _gen;
    private readonly IActivityService _activities;
    private readonly IReferenceDefaultsService _referenceDefaults;
    private readonly ILogger<ActivityCreateService> _logger;

    public ActivityCreateService(
        IGenApiClient gen,
        IActivityService activities,
        IReferenceDefaultsService referenceDefaults,
        ILogger<ActivityCreateService> logger)
    {
        _gen = gen;
        _activities = activities;
        _referenceDefaults = referenceDefaults;
        _logger = logger;
    }

    public async Task<ActivityOperationResult<GenActivityDetail>> CreateAsync(
        GenCredentials credentials,
        string repUserId,
        CreateActivityCommand command,
        CancellationToken ct = default)
    {
        var sourceKey = command.SourceActivityId.Trim();
        _logger.LogInformation(
            "CreateAsync sourceActivityId={SourceActivityId} repUserId={RepUserId}",
            sourceKey,
            repUserId);

        var lookup = await ActivityLookup.LoadAsync(_gen, credentials, sourceKey, _logger, ct);
        if (lookup is null)
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotFound,
                "Source activity not found.");
        }

        // Full GET — ActivityDetailSelect omits Gen reference fields required for create.
        JsonElement sourceRoot;
        try
        {
            sourceRoot = await _gen.GetAsync($"crmactivities/{lookup.CanonicalId}", credentials, ct);
        }
        catch (GenApiException ex) when (ex.StatusCode is 404)
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotFound,
                "Source activity not found.");
        }

        var sourceRow = ActivityMapper.ParseDetailRow(sourceRoot);

        if (string.IsNullOrWhiteSpace(sourceRow.FirmId))
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.MissingFirm,
                "Source activity has no linked customer.");
        }

        if (string.IsNullOrWhiteSpace(sourceRow.ActivityTypeId))
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.GenValidationFailed,
                "Source activity has no activity type.");
        }

        if (!ActivityMapper.TryGetReferenceFields(sourceRoot, out var refs))
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.MissingReferenceFields,
                "Source activity is missing required Gen reference fields (ActQueue, Period, Division, SolverRole, or ActivityArea).");
        }

        var body = BuildFollowUpGenPayload(command, sourceRoot, sourceRow, refs, repUserId);
        LogFollowUpContext(command, sourceRoot, body);

        var result = await CommitAndLoadDetailAsync(credentials, repUserId, body, mergeFromValidate: false, ct);
        if (result.Value is not null)
        {
            await LogChildContextAfterCreateAsync(credentials, result.Value.Id, ct);
        }

        return result;
    }

    public async Task<ActivityOperationResult<GenActivityDetail>> CreateStandaloneAsync(
        GenCredentials credentials,
        string repUserId,
        StandaloneCreateActivityCommand command,
        CancellationToken ct = default)
    {
        _logger.LogInformation(
            "CreateStandaloneAsync firmId={FirmId} repUserId={RepUserId}",
            command.FirmId,
            repUserId);

        if (!_referenceDefaults.TryGetStandaloneDefaults(out var defaults))
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.MissingReferenceFields,
                "Activity reference defaults are not configured for this tenant.");
        }

        var body = BuildStandaloneGenPayload(command, defaults);
        return await CommitAndLoadDetailAsync(credentials, repUserId, body, mergeFromValidate: true, ct);
    }

    private async Task<ActivityOperationResult<GenActivityDetail>> CommitAndLoadDetailAsync(
        GenCredentials credentials,
        string repUserId,
        Dictionary<string, object?> body,
        bool mergeFromValidate,
        CancellationToken ct)
    {
        var (createError, createdId) = await PostCreateAsync(credentials, body, mergeFromValidate, ct);
        if (createError is not null)
        {
            return MapPostError(createError.Value);
        }

        if (string.IsNullOrEmpty(createdId))
        {
            _logger.LogError("Create commit succeeded but no activity ID was returned from Gen");
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.GenValidationFailed,
                "Gen did not return a created activity ID.");
        }

        _logger.LogInformation("Create committed id={CreatedId}", createdId);

        var detail = await _activities.GetDetailAsync(credentials, createdId, repUserId, ct);
        if (detail is null)
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotFound,
                "Created activity could not be loaded.");
        }

        return ActivityOperationResult<GenActivityDetail>.Ok(detail);
    }

    private static Dictionary<string, object?> BuildStandaloneGenPayload(
        StandaloneCreateActivityCommand command,
        StandaloneActivityDefaults defaults)
    {
        // AssignedUserId is pre-resolved in ActivitiesController (explicit pick or session rep).
        var assigneeId = command.AssignedUserId.Trim();
        var actQueueId = FirstNonEmpty(command.ActQueueId, defaults.ActQueueId);
        var activityTypeId = FirstNonEmpty(command.ActivityTypeId, defaults.ActivityTypeId);
        var activityAreaId = FirstNonEmpty(command.ActivityAreaId, defaults.ActivityAreaId);

        if (string.IsNullOrWhiteSpace(actQueueId) || string.IsNullOrWhiteSpace(activityTypeId))
        {
            throw new InvalidOperationException(
                "Standalone create requires ActQueue_ID and ActivityType_ID from the request or tenant defaults.");
        }

        var body = new Dictionary<string, object?>
        {
            ["Subject"] = command.Subject.Trim(),
            ["Firm_ID"] = command.FirmId.Trim(),
            ["SheduledStart$DATE"] = command.ScheduledStart.ToString("o"),
            ["ResponsibleUser_ID"] = assigneeId,
            ["SolverUser_ID"] = assigneeId,
            ["ActQueue_ID"] = actQueueId,
            ["Division_ID"] = defaults.DivisionId,
            ["SolverRole_ID"] = defaults.SolverRoleId,
            ["ActivityType_ID"] = activityTypeId,
        };

        if (!string.IsNullOrWhiteSpace(activityAreaId))
        {
            body["ActivityArea_ID"] = activityAreaId;
        }

        if (!string.IsNullOrWhiteSpace(command.Description))
        {
            body["Description"] = command.Description.Trim();
        }

        if (ActivityMapper.IsValidPersonId(command.ContactPersonId))
        {
            body["Person_ID"] = command.ContactPersonId!.Trim();
        }

        if (!string.IsNullOrWhiteSpace(command.BusinessCaseId))
        {
            body["BusTransaction_ID"] = command.BusinessCaseId.Trim();
        }

        if (!string.IsNullOrWhiteSpace(command.WorkOrderId))
        {
            body["BusOrder_ID"] = command.WorkOrderId.Trim();
        }

        if (!string.IsNullOrWhiteSpace(command.ProjectId))
        {
            body["BusProject_ID"] = command.ProjectId.Trim();
        }

        return body;
    }

    private static string FirstNonEmpty(string? primary, string? fallback) =>
        !string.IsNullOrWhiteSpace(primary) ? primary.Trim()
        : !string.IsNullOrWhiteSpace(fallback) ? fallback.Trim()
        : "";

    private static Dictionary<string, object?> BuildFollowUpGenPayload(
        CreateActivityCommand command,
        JsonElement sourceRoot,
        GenActivityRow sourceRow,
        ActivityMapper.GenActivityReferenceFields refs,
        string repUserId)
    {
        // AssignedUserId is pre-resolved in ActivitiesController (explicit pick or session rep).
        var assigneeId = command.AssignedUserId!.Trim();
        var responsibleUserId = assigneeId;
        var solverUserId = assigneeId;

        var body = new Dictionary<string, object?>
        {
            ["Subject"] = command.Subject.Trim(),
            ["Firm_ID"] = sourceRow.FirmId!,
            ["ActivityType_ID"] = sourceRow.ActivityTypeId!,
            ["SheduledStart$DATE"] = command.ScheduledStart.ToString("o"),
            ["ResponsibleUser_ID"] = responsibleUserId,
            ["SolverUser_ID"] = solverUserId,
            ["Source_ID"] = command.SourceActivityId.Trim(),
            ["ActQueue_ID"] = refs.ActQueueId,
            ["Period_ID"] = refs.PeriodId,
            ["Division_ID"] = refs.DivisionId,
            ["SolverRole_ID"] = refs.SolverRoleId,
            ["ActivityArea_ID"] = refs.ActivityAreaId,
        };

        var (sourceDescription, sourceAnswer) = ResolveSourceText(command, sourceRoot);
        var (followUpDescription, followUpAnswer) = ActivityMapper.ResolveFollowUpTextFields(
            sourceDescription,
            sourceAnswer,
            command.Description);

        if (!string.IsNullOrWhiteSpace(followUpDescription))
        {
            body["Description"] = followUpDescription;
        }

        if (!string.IsNullOrWhiteSpace(followUpAnswer))
        {
            body["Answer"] = followUpAnswer;
        }

        var personId = ActivityMapper.GetPersonId(sourceRoot);
        if (ActivityMapper.IsValidPersonId(personId))
        {
            body["Person_ID"] = personId;
        }

        var busTransactionId = ActivityMapper.GetBusTransactionId(sourceRoot);
        if (!string.IsNullOrWhiteSpace(busTransactionId))
        {
            body["BusTransaction_ID"] = busTransactionId;
        }

        var busOrderId = ActivityMapper.GetBusOrderId(sourceRoot);
        if (!string.IsNullOrWhiteSpace(busOrderId))
        {
            body["BusOrder_ID"] = busOrderId;
        }

        var busProjectId = ActivityMapper.GetBusProjectId(sourceRoot);
        if (!string.IsNullOrWhiteSpace(busProjectId))
        {
            body["BusProject_ID"] = busProjectId;
        }

        return body;
    }

    private static (string? Description, string? Answer) ResolveSourceText(
        CreateActivityCommand command,
        JsonElement sourceRoot)
    {
        var description = !string.IsNullOrWhiteSpace(command.SourceDescription)
            ? command.SourceDescription.Trim()
            : ActivityMapper.GetDescription(sourceRoot);

        var answer = !string.IsNullOrWhiteSpace(command.SourceAnswer)
            ? command.SourceAnswer.Trim()
            : ActivityMapper.GetAnswer(sourceRoot);

        return (description, answer);
    }

    private void LogFollowUpContext(
        CreateActivityCommand command,
        JsonElement sourceRoot,
        Dictionary<string, object?> body)
    {
        var (sourceDescription, sourceAnswer) = ResolveSourceText(command, sourceRoot);
        var (followUpDescription, followUpAnswer) = ActivityMapper.ResolveFollowUpTextFields(
            sourceDescription,
            sourceAnswer,
            command.Description);

        _logger.LogInformation(
            "[FollowUpContext] sourceActivityId={SourceActivityId} commandSourceDescriptionLen={CommandSourceDescriptionLen} commandSourceAnswerLen={CommandSourceAnswerLen} genSourceDescriptionLen={GenSourceDescriptionLen} genSourceAnswerLen={GenSourceAnswerLen} resolvedDescriptionLen={ResolvedDescriptionLen} resolvedAnswerLen={ResolvedAnswerLen} payloadHasDescription={PayloadHasDescription} payloadHasAnswer={PayloadHasAnswer}",
            command.SourceActivityId,
            command.SourceDescription?.Length ?? 0,
            command.SourceAnswer?.Length ?? 0,
            ActivityMapper.GetDescription(sourceRoot)?.Length ?? 0,
            ActivityMapper.GetAnswer(sourceRoot)?.Length ?? 0,
            followUpDescription?.Length ?? 0,
            followUpAnswer?.Length ?? 0,
            body.ContainsKey("Description"),
            body.ContainsKey("Answer"));

        if (_logger.IsEnabled(LogLevel.Debug))
        {
            var payloadJson = JsonSerializer.Serialize(body, GenJsonHelper.Options);
            _logger.LogDebug("[FollowUpContext] outgoing Gen POST payload={Payload}", payloadJson);
        }
    }

    private async Task LogChildContextAfterCreateAsync(
        GenCredentials credentials,
        string createdId,
        CancellationToken ct)
    {
        try
        {
            var childRoot = await _gen.GetAsync($"crmactivities/{createdId}", credentials, ct);
            _logger.LogInformation(
                "[FollowUpContext] childAfterCreate id={CreatedId} descriptionLen={DescriptionLen} answerLen={AnswerLen}",
                createdId,
                ActivityMapper.GetDescription(childRoot)?.Length ?? 0,
                ActivityMapper.GetAnswer(childRoot)?.Length ?? 0);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "[FollowUpContext] childAfterCreate GET failed id={CreatedId}", createdId);
        }
    }

    private async Task<(ActivityOperationErrorCode? Error, string? CreatedId)> PostCreateAsync(
        GenCredentials credentials,
        Dictionary<string, object?> body,
        bool mergeFromValidate,
        CancellationToken ct)
    {
        JsonElement validateResponse = default;
        var validateErrorCount = 0;

        for (var round = 0; round < MaxValidateRounds; round++)
        {
            try
            {
                validateResponse = await _gen.PostAsync(
                    "crmactivities?validation=true",
                    credentials,
                    body,
                    ct);
            }
            catch (GenApiException ex)
            {
                _logger.LogWarning(
                    ex,
                    "PostCreateAsync Gen validate HTTP {Status}",
                    ex.StatusCode);
                return (ActivityOperationErrorCode.GenValidationFailed, null);
            }

            validateErrorCount = GenValidation.GetErrorCount(validateResponse);
            _logger.LogInformation(
                "PostCreateAsync validate round={Round} errorCount={ErrorCount}",
                round + 1,
                validateErrorCount);

            if (validateErrorCount == 0)
            {
                if (mergeFromValidate)
                {
                    _referenceDefaults.MergeFromValidateResponse(body, validateResponse);
                }

                break;
            }

            if (!mergeFromValidate || round >= MaxValidateRounds - 1)
            {
                return (ActivityOperationErrorCode.GenValidationFailed, null);
            }

            _referenceDefaults.MergeFromValidateResponse(body, validateResponse);
        }

        if (validateErrorCount > 0)
        {
            return (ActivityOperationErrorCode.GenValidationFailed, null);
        }

        JsonElement commitResponse;
        try
        {
            commitResponse = await _gen.PostAsync("crmactivities", credentials, body, ct);
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(
                ex,
                "PostCreateAsync Gen commit HTTP {Status}",
                ex.StatusCode);
            return (ActivityOperationErrorCode.GenValidationFailed, null);
        }

        var commitErrorCount = GenValidation.GetErrorCount(commitResponse);
        if (commitErrorCount > 0)
        {
            _logger.LogWarning(
                "PostCreateAsync Gen commit validation errorCount={ErrorCount}",
                commitErrorCount);
            return (ActivityOperationErrorCode.GenValidationFailed, null);
        }

        return (null, ActivityMapper.GetCanonicalId(commitResponse));
    }

    private static ActivityOperationResult<GenActivityDetail> MapPostError(ActivityOperationErrorCode code) =>
        ActivityOperationResult<GenActivityDetail>.Fail(
            code,
            code switch
            {
                ActivityOperationErrorCode.GenValidationFailed => "Gen rejected the activity create.",
                ActivityOperationErrorCode.MissingReferenceFields =>
                    "Activity reference defaults are not configured for this tenant.",
                _ => "Activity create failed.",
            });
}
