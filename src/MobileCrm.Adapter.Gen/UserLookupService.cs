using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace MobileCrm.Adapter.Gen;

public sealed record GenUserSummary(
    string Id,
    string LoginName,
    string DisplayName,
    string? ShortName,
    bool IsActive = true);

public interface IUserLookupService
{
    Task<IReadOnlyList<GenUserSummary>> SearchAsync(
        GenCredentials credentials,
        string? query,
        int take,
        CancellationToken ct = default);

    Task<GenUserSummary?> GetByIdAsync(
        GenCredentials credentials,
        string userId,
        CancellationToken ct = default);
}

public sealed class UserLookupService : IUserLookupService
{
    private const string UserSelect = "ID,Name,LoginName,ShortName";

    private readonly IGenApiClient _gen;
    private readonly ILogger<UserLookupService> _logger;

    public UserLookupService(IGenApiClient gen, ILogger<UserLookupService> logger)
    {
        _gen = gen;
        _logger = logger;
    }

    public async Task<IReadOnlyList<GenUserSummary>> SearchAsync(
        GenCredentials credentials,
        string? query,
        int take,
        CancellationToken ct = default)
    {
        take = Math.Clamp(take, 1, 50);
        var term = (query ?? "").Trim();

        var fetchTake = string.IsNullOrEmpty(term) ? take : Math.Min(take * 4, 100);
        var path = $"securityusers?select={Uri.EscapeDataString(UserSelect)}&take={fetchTake}";

        JsonElement root;
        try
        {
            root = await _gen.GetAsync(path, credentials, ct);
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "securityusers list failed HTTP {Status}", ex.StatusCode);
            return [];
        }

        var users = ParseList(root)
            .Where(u => u.IsActive)
            .ToList();

        if (!string.IsNullOrEmpty(term))
        {
            users = users
                .Where(u =>
                    u.DisplayName.Contains(term, StringComparison.OrdinalIgnoreCase)
                    || u.LoginName.Contains(term, StringComparison.OrdinalIgnoreCase)
                    || (u.ShortName?.Contains(term, StringComparison.OrdinalIgnoreCase) ?? false))
                .Take(take)
                .ToList();
        }
        else
        {
            users = users
                .OrderBy(u => u.DisplayName, StringComparer.OrdinalIgnoreCase)
                .Take(take)
                .ToList();
        }

        return users;
    }

    public async Task<GenUserSummary?> GetByIdAsync(
        GenCredentials credentials,
        string userId,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(userId))
        {
            return null;
        }

        var id = userId.Trim();
        try
        {
            var root = await _gen.GetAsync(
                $"securityusers/{id}?select={Uri.EscapeDataString(UserSelect)}",
                credentials,
                ct);
            return ParseRow(root);
        }
        catch (GenApiException ex) when (ex.StatusCode is 404)
        {
            return null;
        }
    }

    private static IReadOnlyList<GenUserSummary> ParseList(JsonElement root)
    {
        var items = new List<GenUserSummary>();
        if (root.ValueKind == JsonValueKind.Array)
        {
            foreach (var el in root.EnumerateArray())
            {
                var row = ParseRow(el);
                if (row is not null)
                {
                    items.Add(row);
                }
            }

            return items;
        }

        if (root.ValueKind == JsonValueKind.Object)
        {
            foreach (var name in new[] { "items", "value", "data" })
            {
                if (root.TryGetProperty(name, out var arr) && arr.ValueKind == JsonValueKind.Array)
                {
                    foreach (var el in arr.EnumerateArray())
                    {
                        var row = ParseRow(el);
                        if (row is not null)
                        {
                            items.Add(row);
                        }
                    }

                    return items;
                }
            }

            var single = ParseRow(root);
            if (single is not null)
            {
                items.Add(single);
            }
        }

        return items;
    }

    private static GenUserSummary? ParseRow(JsonElement el)
    {
        var id = GenJsonHelper.GetString(el, "ID", "id");
        if (string.IsNullOrEmpty(id))
        {
            return null;
        }

        var login = GenJsonHelper.GetString(el, "LoginName", "loginname", "loginName") ?? id;
        var name = GenJsonHelper.GetString(el, "Name", "name", "displayName") ?? login;
        var shortName = GenJsonHelper.GetString(el, "ShortName", "shortname", "shortName");
        var locked = GenJsonHelper.GetBool(el, "Locked", "locked") ?? false;
        var isActive = GenJsonHelper.GetBool(el, "IsActive", "isactive", "isActive") ?? true;

        return new GenUserSummary(id, login, name, shortName, isActive && !locked);
    }
}
