using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace MobileCrm.Adapter.Gen;

public sealed record RepresentativeProfile(
    string Id,
    string LoginName,
    string DisplayName,
    string? Email,
    string? EmployeeNumber);

public interface IRepresentativeService
{
    Task<RepresentativeProfile> GetCurrentUserAsync(GenCredentials credentials, CancellationToken ct = default);
}

public sealed class RepresentativeService : IRepresentativeService
{
    private readonly IGenApiClient _gen;
    private readonly ILogger<RepresentativeService> _logger;

    public RepresentativeService(IGenApiClient gen, ILogger<RepresentativeService> logger)
    {
        _gen = gen;
        _logger = logger;
    }

    public async Task<RepresentativeProfile> GetCurrentUserAsync(GenCredentials credentials, CancellationToken ct = default)
    {
        var root = await _gen.GetAsync("currentuser", credentials, ct);
        var id = GenJsonHelper.GetString(root, "id", "ID") ?? throw new InvalidOperationException("currentuser missing id");
        var login = GenJsonHelper.GetString(root, "loginname", "LoginName", "loginName") ?? credentials.LoginName;
        var display = GenJsonHelper.GetString(root, "name", "Name", "displayName") ?? login;
        var email = GenJsonHelper.GetString(root, "email", "Email") ?? "";

        string? employeeNumber = null;
        try
        {
            var su = await _gen.GetAsync(
                $"securityusers/{id}?select=ID,LoginName,Name,Person_ID",
                credentials,
                ct);
            var personId = GenJsonHelper.GetString(su, "Person_ID", "person_ID", "personId");
            if (!string.IsNullOrEmpty(personId))
            {
                var where = Uri.EscapeDataString($"Person_ID eq '{personId}'");
                var employees = await _gen.GetAsync(
                    $"employees?select=ID,PersonalNumber&where={where}&take=1",
                    credentials,
                    ct);
                employeeNumber = ExtractPersonalNumber(employees);
            }
        }
        catch (GenApiException ex)
        {
            _logger.LogDebug(ex, "Optional employees lookup failed for user {UserId}", id);
        }

        return new RepresentativeProfile(id, login, display, email, employeeNumber);
    }

    private static string? ExtractPersonalNumber(JsonElement root)
    {
        if (root.ValueKind == JsonValueKind.Array && root.GetArrayLength() > 0)
        {
            return GenJsonHelper.GetString(root[0], "PersonalNumber", "personalNumber");
        }

        if (root.ValueKind == JsonValueKind.Object)
        {
            foreach (var name in new[] { "items", "value" })
            {
                if (root.TryGetProperty(name, out var arr) && arr.ValueKind == JsonValueKind.Array && arr.GetArrayLength() > 0)
                {
                    return GenJsonHelper.GetString(arr[0], "PersonalNumber", "personalNumber");
                }
            }
        }

        return null;
    }
}
