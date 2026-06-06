using Microsoft.AspNetCore.Mvc;
using MobileCrm.Adapter.Auth;
using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;
using MobileCrm.Adapter.Services;

namespace MobileCrm.Adapter.Controllers;

[ApiController]
[Route("api/v1/contacts")]
public sealed class ContactsController : ControllerBase
{
    private readonly IContactService _contacts;

    public ContactsController(IContactService contacts) => _contacts = contacts;

    [HttpGet("{contactId}")]
    public async Task<ActionResult<ContactDetailResponseDto>> GetDetail(
        string contactId,
        [FromQuery] string? firmId,
        CancellationToken ct = default)
    {
        var session = GetSession();
        var detail = await _contacts.GetDetailAsync(session.Credentials, contactId, firmId, ct);
        if (detail is null)
        {
            return NotFound();
        }

        return Ok(ApiMapping.ToDto(detail));
    }

    private UserSession GetSession() =>
        HttpContext.Items[SessionConstants.HttpContextItemKey] as UserSession
        ?? throw new InvalidOperationException("Session missing");
}
