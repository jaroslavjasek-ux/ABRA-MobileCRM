using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/activities")]
public sealed class ActivitiesController : ControllerBase
{
    private const string FollowUpCreateFailedCode = "FOLLOW_UP_CREATE_FAILED";

    private readonly IActivityService _activities;
    private readonly IActivityCreateService _activityCreate;
    private readonly IFirmService _firms;
    private readonly IRepresentativeService _representatives;
    private readonly IUserLookupService _users;
    private readonly ActivityClassificationOptions _activityClassification;
    private readonly ILogger<ActivitiesController> _logger;

    public ActivitiesController(
        IActivityService activities,
        IActivityCreateService activityCreate,
        IFirmService firms,
        IRepresentativeService representatives,
        IUserLookupService users,
        IOptions<ActivityClassificationOptions> activityClassification,
        ILogger<ActivitiesController> logger)
    {
        _activities = activities;
        _activityCreate = activityCreate;
        _firms = firms;
        _representatives = representatives;
        _users = users;
        _activityClassification = activityClassification.Value;
        _logger = logger;
    }

    [HttpPost]
    public async Task<ActionResult<ActivityDetailResponseDto>> Create(
        [FromBody] CreateActivityRequestDto request,
        CancellationToken ct = default)
    {
        _logger.LogInformation(
            "POST /api/v1/activities sourceActivityId={SourceActivityId} traceId={TraceId}",
            request.SourceActivityId,
            HttpContext.TraceIdentifier);

        var validationError = ValidateCreateRequest(request);
        if (validationError is not null)
        {
            return validationError;
        }

        var session = GetSession();
        var assignedUserError = await ValidateAssignedUserAsync(session, request.AssignedUserId, "assignedUserId", ct);
        if (assignedUserError is not null)
        {
            return assignedUserError;
        }

        var resolvedAssignedUserId = ResolveAssignedUserId(request.AssignedUserId, session.RepUserId);

        var result = await _activityCreate.CreateAsync(
            session.Credentials,
            session.RepUserId,
            new CreateActivityCommand(
                request.SourceActivityId.Trim(),
                request.Subject.Trim(),
                DateTimeOffset.Parse(request.ScheduledStart),
                string.IsNullOrWhiteSpace(request.Description) ? null : request.Description.Trim(),
                resolvedAssignedUserId),
            ct);

        return MapOperationResult(result);
    }

    [HttpPost("create")]
    public async Task<ActionResult<ActivityDetailResponseDto>> CreateStandalone(
        [FromBody] StandaloneCreateActivityRequestDto request,
        CancellationToken ct = default)
    {
        _logger.LogInformation(
            "POST /api/v1/activities/create firmId={FirmId} traceId={TraceId}",
            request.FirmId,
            HttpContext.TraceIdentifier);

        var validationError = ValidateStandaloneCreateRequest(request);
        if (validationError is not null)
        {
            return validationError;
        }

        var session = GetSession();
        var assignedUserError = await ValidateAssignedUserAsync(
            session,
            request.AssignedUserId,
            "assignedUserId",
            ct);
        if (assignedUserError is not null)
        {
            return assignedUserError;
        }

        var resolvedAssignedUserId = ResolveAssignedUserId(request.AssignedUserId, session.RepUserId);

        var firm = await _firms.GetDetailAsync(session.Credentials, request.FirmId.Trim(), 0, ct);
        if (firm is null)
        {
            return UnprocessableEntity(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "VALIDATION_FAILED",
                    Message = "Request validation failed.",
                    Details =
                    [
                        new ApiErrorDetailDto
                        {
                            Field = "firmId",
                            Message = "Firm was not found.",
                        },
                    ],
                    TraceId = HttpContext.TraceIdentifier,
                },
            });
        }

        if (!string.IsNullOrWhiteSpace(request.ContactPersonId))
        {
            var contactId = request.ContactPersonId.Trim();
            var contactFound = firm.Contacts.Any(c =>
                string.Equals(c.Id, contactId, StringComparison.Ordinal));
            if (!contactFound)
            {
                return UnprocessableEntity(new ApiErrorDto
                {
                    Error = new ApiErrorBodyDto
                    {
                        Code = "VALIDATION_FAILED",
                        Message = "Request validation failed.",
                        Details =
                        [
                            new ApiErrorDetailDto
                            {
                                Field = "contactPersonId",
                                Message = "Contact person does not belong to the selected firm.",
                            },
                        ],
                        TraceId = HttpContext.TraceIdentifier,
                    },
                });
            }
        }

        var result = await _activityCreate.CreateStandaloneAsync(
            session.Credentials,
            session.RepUserId,
            new StandaloneCreateActivityCommand(
                request.Subject.Trim(),
                DateTimeOffset.Parse(request.ScheduledStart),
                request.FirmId.Trim(),
                string.IsNullOrWhiteSpace(request.ContactPersonId) ? null : request.ContactPersonId.Trim(),
                string.IsNullOrWhiteSpace(request.Description) ? null : request.Description.Trim(),
                resolvedAssignedUserId,
                string.IsNullOrWhiteSpace(request.BusinessCaseId) ? null : request.BusinessCaseId.Trim(),
                string.IsNullOrWhiteSpace(request.WorkOrderId) ? null : request.WorkOrderId.Trim(),
                string.IsNullOrWhiteSpace(request.ProjectId) ? null : request.ProjectId.Trim(),
                string.IsNullOrWhiteSpace(request.ActivityAreaId) ? null : request.ActivityAreaId.Trim(),
                string.IsNullOrWhiteSpace(request.ActivityTypeId) ? null : request.ActivityTypeId.Trim(),
                string.IsNullOrWhiteSpace(request.ActQueueId) ? null : request.ActQueueId.Trim()),
            ct);

        return MapOperationResult(result);
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

        var followUpValidation = ValidateFollowUpRequest(request.FollowUp);
        if (followUpValidation is not null)
        {
            return followUpValidation;
        }

        var session = GetSession();
        if (request.FollowUp?.Enabled == true)
        {
            var assignedUserError = await ValidateAssignedUserAsync(
                session,
                request.FollowUp.AssignedUserId,
                "followUp.assignedUserId",
                ct);
            if (assignedUserError is not null)
            {
                return assignedUserError;
            }
        }

        var authorDisplayName = await ResolveAuthorDisplayNameAsync(session, ct);
        var result = await _activities.CompleteAsync(
            session.Credentials,
            activityId,
            session.RepUserId,
            request.Answer,
            request.Description,
            authorDisplayName,
            ct);

        if (result.Value is null)
        {
            return MapOperationResult(result);
        }

        GenActivityDetail completedDetail = result.Value;
        GenActivityDetail? followUpDetail = null;
        List<ApiWarningDto>? warnings = null;

        if (request.FollowUp?.Enabled == true)
        {
            var resolvedAssignedUserId = ResolveAssignedUserId(request.FollowUp.AssignedUserId, session.RepUserId);

            var followUpResult = await _activityCreate.CreateAsync(
                session.Credentials,
                session.RepUserId,
                new CreateActivityCommand(
                    activityId,
                    request.FollowUp.Subject!.Trim(),
                    DateTimeOffset.Parse(request.FollowUp.ScheduledStart!),
                    string.IsNullOrWhiteSpace(request.FollowUp.Description)
                        ? null
                        : request.FollowUp.Description.Trim(),
                    resolvedAssignedUserId,
                    string.IsNullOrWhiteSpace(completedDetail.Description)
                        ? null
                        : completedDetail.Description.Trim(),
                    string.IsNullOrWhiteSpace(completedDetail.Answer)
                        ? null
                        : completedDetail.Answer.Trim()),
                ct);

            if (followUpResult.Value is not null)
            {
                followUpDetail = followUpResult.Value;
                var refetched = await _activities.GetDetailAsync(
                    session.Credentials,
                    activityId,
                    session.RepUserId,
                    ct);
                if (refetched is not null)
                {
                    completedDetail = refetched;
                }
            }
            else
            {
                _logger.LogWarning(
                    "Follow-up create failed after complete activityId={ActivityId} error={Error} message={Message}",
                    activityId,
                    followUpResult.Error,
                    followUpResult.Message);
                warnings =
                [
                    new ApiWarningDto
                    {
                        Code = FollowUpCreateFailedCode,
                        Message = followUpResult.Message ?? "Follow-up activity could not be created.",
                    },
                ];
            }
        }

        return Ok(ApiMapping.ToDto(completedDetail, followUpDetail, warnings));
    }

    [HttpPut("{activityId}/note")]
    public async Task<ActionResult<ActivityDetailResponseDto>> AddNote(
        string activityId,
        [FromBody] AddActivityNoteRequestDto request,
        CancellationToken ct = default)
    {
        _logger.LogInformation(
            "PUT /api/v1/activities/{ActivityId}/note traceId={TraceId}",
            activityId,
            HttpContext.TraceIdentifier);

        if (string.IsNullOrWhiteSpace(request.Note))
        {
            return UnprocessableEntity(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "VALIDATION_FAILED",
                    Message = "Note is required.",
                    Details =
                    [
                        new ApiErrorDetailDto { Field = "note", Message = "Note is required." },
                    ],
                    TraceId = HttpContext.TraceIdentifier,
                },
            });
        }

        var session = GetSession();
        var authorDisplayName = await ResolveAuthorDisplayNameAsync(session, ct);
        var result = await _activities.AddNoteAsync(
            session.Credentials,
            activityId,
            session.RepUserId,
            request.Note,
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
            ActivityOperationErrorCode.MissingReferenceFields => UnprocessableEntity(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "VALIDATION_FAILED",
                    Message = result.Message ?? "Source activity is missing required reference fields.",
                    TraceId = HttpContext.TraceIdentifier,
                },
            }),
            ActivityOperationErrorCode.ClassificationValidationFailed => UnprocessableEntity(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "CLASSIFICATION_INVALID",
                    Message = result.Message ?? "Selected activity classification is not valid.",
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

    private UnprocessableEntityObjectResult? ValidateFollowUpRequest(ScheduleFollowUpRequestDto? followUp)
    {
        if (followUp is null || !followUp.Enabled)
        {
            return null;
        }

        var details = new List<ApiErrorDetailDto>();

        if (string.IsNullOrWhiteSpace(followUp.Subject))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "followUp.subject",
                Message = "Follow-up subject is required.",
            });
        }

        if (string.IsNullOrWhiteSpace(followUp.ScheduledStart))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "followUp.scheduledStart",
                Message = "Follow-up scheduled start is required.",
            });
        }
        else if (!DateTimeOffset.TryParse(followUp.ScheduledStart, out _))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "followUp.scheduledStart",
                Message = "Follow-up scheduled start must be a valid ISO-8601 date/time.",
            });
        }

        if (string.IsNullOrWhiteSpace(followUp.AssignedUserId))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "followUp.assignedUserId",
                Message = "Follow-up assigned user is required.",
            });
        }

        if (details.Count == 0)
        {
            return null;
        }

        return UnprocessableEntity(new ApiErrorDto
        {
            Error = new ApiErrorBodyDto
            {
                Code = "VALIDATION_FAILED",
                Message = "Follow-up validation failed.",
                Details = details,
                TraceId = HttpContext.TraceIdentifier,
            },
        });
    }

    private UnprocessableEntityObjectResult? ValidateStandaloneCreateRequest(
        StandaloneCreateActivityRequestDto request)
    {
        var details = new List<ApiErrorDetailDto>();

        if (string.IsNullOrWhiteSpace(request.Subject))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "subject",
                Message = "Subject is required.",
            });
        }

        if (string.IsNullOrWhiteSpace(request.FirmId))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "firmId",
                Message = "Firm is required.",
            });
        }

        if (string.IsNullOrWhiteSpace(request.ScheduledStart))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "scheduledStart",
                Message = "Scheduled start is required.",
            });
        }
        else if (!DateTimeOffset.TryParse(request.ScheduledStart, out _))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "scheduledStart",
                Message = "Scheduled start must be a valid ISO-8601 date/time.",
            });
        }

        if (_activityClassification.Type && string.IsNullOrWhiteSpace(request.ActivityTypeId))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "activityTypeId",
                Message = "Activity type is required.",
            });
        }

        if (_activityClassification.Queue && string.IsNullOrWhiteSpace(request.ActQueueId))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "actQueueId",
                Message = "Activity queue is required.",
            });
        }

        if (details.Count == 0)
        {
            return null;
        }

        return UnprocessableEntity(new ApiErrorDto
        {
            Error = new ApiErrorBodyDto
            {
                Code = "VALIDATION_FAILED",
                Message = "Request validation failed.",
                Details = details,
                TraceId = HttpContext.TraceIdentifier,
            },
        });
    }

    private UnprocessableEntityObjectResult? ValidateCreateRequest(CreateActivityRequestDto request)
    {
        var details = new List<ApiErrorDetailDto>();

        if (string.IsNullOrWhiteSpace(request.SourceActivityId))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "sourceActivityId",
                Message = "Source activity ID is required.",
            });
        }

        if (string.IsNullOrWhiteSpace(request.Subject))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "subject",
                Message = "Subject is required.",
            });
        }

        if (string.IsNullOrWhiteSpace(request.ScheduledStart))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "scheduledStart",
                Message = "Scheduled start is required.",
            });
        }
        else if (!DateTimeOffset.TryParse(request.ScheduledStart, out _))
        {
            details.Add(new ApiErrorDetailDto
            {
                Field = "scheduledStart",
                Message = "Scheduled start must be a valid ISO-8601 date/time.",
            });
        }

        if (details.Count == 0)
        {
            return null;
        }

        return UnprocessableEntity(new ApiErrorDto
        {
            Error = new ApiErrorBodyDto
            {
                Code = "VALIDATION_FAILED",
                Message = "Request validation failed.",
                Details = details,
                TraceId = HttpContext.TraceIdentifier,
            },
        });
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

    private static string ResolveAssignedUserId(string? assignedUserId, string sessionRepUserId) =>
        string.IsNullOrWhiteSpace(assignedUserId) ? sessionRepUserId : assignedUserId.Trim();

    private async Task<UnprocessableEntityObjectResult?> ValidateAssignedUserAsync(
        UserSession session,
        string? assignedUserId,
        string fieldName,
        CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(assignedUserId))
        {
            return null;
        }

        var user = await _users.GetByIdAsync(session.Credentials, assignedUserId.Trim(), ct);
        if (user is null || !user.IsActive)
        {
            return UnprocessableEntity(new ApiErrorDto
            {
                Error = new ApiErrorBodyDto
                {
                    Code = "VALIDATION_FAILED",
                    Message = "Assigned user is not valid.",
                    Details =
                    [
                        new ApiErrorDetailDto
                        {
                            Field = fieldName,
                            Message = "Assigned user was not found or is inactive.",
                        },
                    ],
                    TraceId = HttpContext.TraceIdentifier,
                },
            });
        }

        return null;
    }

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
                "Could not resolve display name for rep {RepUserId}; prepending answer without author",
                session.RepUserId);
            return null;
        }
    }
}
