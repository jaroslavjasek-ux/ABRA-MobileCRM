using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/activities")]
public sealed class ActivitiesController : ControllerBase
{
    private readonly IActivityService _activities;
    private readonly IRepresentativeService _representatives;
    private readonly ILogger<ActivitiesController> _logger;

    public ActivitiesController(
        IActivityService activities,
        IRepresentativeService representatives,
        ILogger<ActivitiesController> logger)
    {
        _activities = activities;
        _representatives = representatives;
        _logger = logger;
    }

    [HttpGet("{activityId}")]
    public async Task<ActionResult<ActivityDetailResponseDto>> GetDetail(
        string activityId,
        CancellationToken ct = default)
    {
        _logger.LogInformation(
            "GET /api/v1/activities/{ActivityId} traceId={TraceId}",
            activityId,
            HttpContext.TraceIdentifier);

        var session = GetSession();
        var detail = await _activities.GetDetailAsync(
            session.Credentials,
            activityId,
            session.RepUserId,
            ct);

        if (detail is null)
        {
            return ActivityNotFound();
        }

        return Ok(ApiMapping.ToDto(detail));
    }

    [HttpPut("{activityId}/start")]
    public async Task<ActionResult<ActivityDetailResponseDto>> Start(
        string activityId,
        CancellationToken ct = default)
    {
        _logger.LogInformation(
            "PUT /api/v1/activities/{ActivityId}/start traceId={TraceId}",
            activityId,
            HttpContext.TraceIdentifier);

        var session = GetSession();
        var result = await _activities.StartAsync(
            session.Credentials,
            activityId,
            session.RepUserId,
            ct);

        return MapOperationResult(result);
    }

    [HttpPut("{activityId}/complete")]
    public async Task<ActionResult<ActivityDetailResponseDto>> Complete(
        string activityId,
        [FromBody] CompleteActivityRequestDto request,
        CancellationToken ct = default)
    {
        _logger.LogInformation(
            "PUT /api/v1/activities/{ActivityId}/complete traceId={TraceId}",
            activityId,
            HttpContext.TraceIdentifier);

        if (string.IsNullOrWhiteSpace(request.Answer))
        {
            return UnprocessableEntity(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "VALIDATION_FAILED",
                    Message = "Answer is required.",
                    Details =
                    [
                        new ApiErrorDetailDto { Field = "answer", Message = "Answer is required." },
                    ],
                    TraceId = HttpContext.TraceIdentifier,
                },
            });
        }

        var session = GetSession();
        var authorDisplayName = await ResolveAuthorDisplayNameAsync(session, ct);
        var result = await _activities.CompleteAsync(
            session.Credentials,
            activityId,
            session.RepUserId,
            request.Answer,
            request.Description,
            authorDisplayName,
            ct);

        return MapOperationResult(result);
    }

    private ActionResult<ActivityDetailResponseDto> MapOperationResult(
        ActivityOperationResult<GenActivityDetail> result)
    {
        if (result.Value is not null)
        {
            return Ok(ApiMapping.ToDto(result.Value));
        }

        return result.Error switch
        {
            ActivityOperationErrorCode.NotFound => ActivityNotFound(),
            ActivityOperationErrorCode.NotEditable => Conflict(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "NOT_EDITABLE",
                    Message = result.Message ?? "Activity cannot be changed.",
                    TraceId = HttpContext.TraceIdentifier,
                },
            }),
            ActivityOperationErrorCode.MissingFirm => UnprocessableEntity(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "VALIDATION_FAILED",
                    Message = result.Message ?? "Activity has no linked customer.",
                    TraceId = HttpContext.TraceIdentifier,
                },
            }),
            ActivityOperationErrorCode.GenValidationFailed => UnprocessableEntity(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "VALIDATION_FAILED",
                    Message = result.Message ?? "Gen rejected the activity update.",
                    TraceId = HttpContext.TraceIdentifier,
                },
            }),
            _ => StatusCode(
                StatusCodes.Status500InternalServerError,
                new ApiErrorDto
                {
                    Error = new ApiErrorBodyDto
                    {
                        Code = "INTERNAL_ERROR",
                        Message = "Activity update failed.",
                        TraceId = HttpContext.TraceIdentifier,
                    },
                }),
        };
    }

    private NotFoundObjectResult ActivityNotFound() =>
        NotFound(new ApiErrorDto
        {
            Error = new ApiErrorBodyDto
            {
                Code = "NOT_FOUND",
                Message = "Activity not found.",
                TraceId = HttpContext.TraceIdentifier,
            },
        });

    private UserSession GetSession() =>
        HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
        ?? throw new InvalidOperationException("Session missing");

    private async Task<string?> ResolveAuthorDisplayNameAsync(UserSession session, CancellationToken ct)
    {
        try
        {
            var profile = await _representatives.GetCurrentUserAsync(session.Credentials, ct);
            return string.IsNullOrWhiteSpace(profile.DisplayName) ? null : profile.DisplayName.Trim();
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(
                ex,
                "Could not resolve display name for rep {RepUserId}; appending answer without author",
                session.RepUserId);
            return null;
        }
    }
}
