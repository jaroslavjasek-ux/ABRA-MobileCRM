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

public interface IActivityCreateService
{
    Task<ActivityOperationResult<GenActivityDetail>> CreateAsync(
        GenCredentials credentials,
        string repUserId,
        CreateActivityCommand command,
        CancellationToken ct = default);
}

public sealed class ActivityCreateService : IActivityCreateService
{
    private readonly IGenApiClient _gen;
    private readonly IActivityService _activities;
    private readonly ILogger<ActivityCreateService> _logger;

    public ActivityCreateService(
        IGenApiClient gen,
        IActivityService activities,
        ILogger<ActivityCreateService> logger)
    {
        _gen = gen;
        _activities = activities;
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

        var body = BuildGenPayload(command, sourceRoot, sourceRow, refs, repUserId);
        LogFollowUpContext(command, sourceRoot, body);

        var (createError, createdId) = await PostCreateAsync(credentials, body, ct);
        if (createError is not null)
        {
            return MapPostError(createError.Value);
        }

        if (string.IsNullOrEmpty(createdId))
        {
            _logger.LogError("CreateAsync commit succeeded but no activity ID was returned from Gen");
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.GenValidationFailed,
                "Gen did not return a created activity ID.");
        }

        _logger.LogInformation("CreateAsync committed id={CreatedId}", createdId);

        await LogChildContextAfterCreateAsync(credentials, createdId, ct);

        var detail = await _activities.GetDetailAsync(credentials, createdId, repUserId, ct);
        if (detail is null)
        {
            return ActivityOperationResult<GenActivityDetail>.Fail(
                ActivityOperationErrorCode.NotFound,
                "Created activity could not be loaded.");
        }

        return ActivityOperationResult<GenActivityDetail>.Ok(detail);
    }

    private static Dictionary<string, object?> BuildGenPayload(
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
        CancellationToken ct)
    {
        JsonElement validateResponse;
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

        var validateErrorCount = GenValidation.GetErrorCount(validateResponse);
        _logger.LogInformation(
            "PostCreateAsync validate errorCount={ErrorCount}",
            validateErrorCount);

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
                _ => "Activity create failed.",
            });
}
