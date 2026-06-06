using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace MobileCrm.Adapter.Gen;

public interface IFirmService
{
    Task<GenFirmSearchResult> SearchAsync(GenCredentials credentials, string query, int take, int skip, CancellationToken ct = default);
    Task<GenFirmDetail?> GetDetailAsync(GenCredentials credentials, string firmId, int recentTake, CancellationToken ct = default);
    Task<string?> ResolvePrimaryContactIdAsync(GenCredentials credentials, string firmId, CancellationToken ct = default);
}

public sealed class FirmService : IFirmService
{
    private readonly IGenApiClient _gen;
    private readonly GenOptions _options;
    private readonly ILogger<FirmService> _logger;

    public FirmService(IGenApiClient gen, IOptions<GenOptions> options, ILogger<FirmService> logger)
    {
        _gen = gen;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<GenFirmSearchResult> SearchAsync(
        GenCredentials credentials,
        string query,
        int take,
        int skip,
        CancellationToken ct = default)
    {
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var path = FirmSearchQueryBuilder.BuildListQuery(query, take + 1, skip, _options);
        var root = await _gen.GetAsync(path, credentials, ct);
        var all = FirmMapper.ParseSummaryList(root)
            .Where(f => !string.IsNullOrEmpty(f.Id))
            .ToList();

        var hasMore = all.Count > take;
        if (hasMore)
        {
            all = all.Take(take).ToList();
        }

        return new GenFirmSearchResult(all, all.Count, hasMore);
    }

    public async Task<string?> ResolvePrimaryContactIdAsync(
        GenCredentials credentials,
        string firmId,
        CancellationToken ct = default)
    {
        try
        {
            var root = await _gen.GetAsync($"firms/{firmId}", credentials, ct);
            var initialPersonId = GenJsonHelper.GetString(
                root, "InitialFirmPerson_ID", "initialfirmperson_id");
            var links = FirmpersonParser.ParseFromFirm(root);
            var visible = new List<FirmpersonLink>();
            foreach (var link in links)
            {
                var person = await LoadPersonContactInfoAsync(credentials, link.PersonId, ct);
                if (person is null || person.Hidden || person.IsEmployee)
                {
                    continue;
                }

                visible.Add(link);
            }

            return FirmpersonParser.ResolvePrimaryPersonId(initialPersonId, visible);
        }
        catch (GenApiException ex) when (ex.StatusCode == 404)
        {
            return null;
        }
    }

    public async Task<GenFirmDetail?> GetDetailAsync(
        GenCredentials credentials,
        string firmId,
        int recentTake,
        CancellationToken ct = default)
    {
        JsonElement root;
        try
        {
            root = await _gen.GetAsync($"firms/{firmId}", credentials, ct);
        }
        catch (GenApiException ex) when (ex.StatusCode == 404)
        {
            return null;
        }

        var id = GenJsonHelper.GetString(root, "ID", "id");
        if (string.IsNullOrEmpty(id))
        {
            return null;
        }

        if (GenJsonHelper.GetBool(root, "Hidden", "hidden") == true)
        {
            return null;
        }

        var initialPersonId = GenJsonHelper.GetString(
            root, "InitialFirmPerson_ID", "initialfirmperson_id");
        var links = FirmpersonParser.ParseFromFirm(root);
        var primaryPersonId = FirmpersonParser.ResolvePrimaryPersonId(initialPersonId, links);

        var contacts = new List<GenContactSummary>();
        foreach (var link in links)
        {
            var person = await LoadPersonContactInfoAsync(credentials, link.PersonId, ct);
            if (person is null || person.Hidden || person.IsEmployee)
            {
                continue;
            }

            contacts.Add(FirmMapper.ToContactSummary(link, person, primaryPersonId));
        }

        var residence = AddressMapper.MapFromProperty(root, "residenceaddress_id", "ResidenceAddress_ID");
        var electronic = AddressMapper.MapFromProperty(root, "electronicaddress_id", "ElectronicAddress_ID");
        contacts = ApplyCompanyLineFallback(contacts, residence, electronic)
            .OrderByDescending(c => c.IsPrimary)
            .ThenBy(c => c.DisplayName, StringComparer.OrdinalIgnoreCase)
            .ToList();
        var recentActivities = await LoadRecentActivitiesAsync(credentials, firmId, recentTake, ct);

        return new GenFirmDetail(
            id,
            GenJsonHelper.GetString(root, "Name", "name") ?? "",
            GenJsonHelper.GetString(root, "Code", "code") ?? "",
            GenJsonHelper.GetString(root, "OrgIdentNumber", "orgidentnumber", "ICO", "ico"),
            GenJsonHelper.GetString(root, "VATIdentNumber", "vatidentnumber", "TaxIdentNumber", "taxidentnumber"),
            FirmMapper.MapCommercialStatus(GenJsonHelper.GetString(root, "PMState_ID", "pmstate_id")),
            residence,
            electronic,
            GenJsonHelper.GetString(root, "WWWAddress", "wwwaddress", "WebAddress", "webaddress"),
            contacts,
            primaryPersonId,
            recentActivities,
            new
            {
                schemaVersion = "1.0",
                availability = new
                {
                    commercialHealth = "unavailable",
                    recentActivities = recentActivities.Count > 0 ? "available" : "empty",
                },
            });
    }

    internal static IReadOnlyList<GenContactSummary> ApplyCompanyLineFallback(
        IReadOnlyList<GenContactSummary> contacts,
        GenAddress? residence,
        GenAddress? electronic)
    {
        var companyPhone = residence?.Phone1 ?? electronic?.Phone1;
        var companyEmail = residence?.Email ?? electronic?.Email;
        if (string.IsNullOrWhiteSpace(companyPhone) && string.IsNullOrWhiteSpace(companyEmail))
        {
            return contacts;
        }

        return contacts
            .Select(c => new GenContactSummary(
                c.Id,
                c.DisplayName,
                c.FirstName,
                c.LastName,
                c.JobTitle,
                c.IsPrimary,
                string.IsNullOrWhiteSpace(c.Phone1) ? companyPhone : c.Phone1,
                string.IsNullOrWhiteSpace(c.Email) ? companyEmail : c.Email))
            .ToList();
    }

    private async Task<PersonContactInfo?> LoadPersonContactInfoAsync(
        GenCredentials credentials,
        string personId,
        CancellationToken ct)
    {
        try
        {
            var select = Uri.EscapeDataString(_options.PersonContactSelect);
            var root = await _gen.GetAsync($"persons/{personId}?select={select}", credentials, ct);
            return ParsePersonContact(root);
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "Failed to load person {PersonId}", personId);
            return null;
        }
    }

    internal static PersonContactInfo? ParsePersonContact(JsonElement root)
    {
        var id = GenJsonHelper.GetString(root, "ID", "id");
        if (string.IsNullOrEmpty(id))
        {
            return null;
        }

        var address = AddressMapper.MapFromProperty(root, "Address_ID", "address_id");
        return new PersonContactInfo(
            id,
            GenJsonHelper.GetString(root, "DisplayName", "displayname"),
            GenJsonHelper.GetString(root, "FirstName", "firstname"),
            GenJsonHelper.GetString(root, "LastName", "lastname"),
            GenJsonHelper.GetString(root, "Grade", "grade", "Title", "title"),
            GenJsonHelper.GetBool(root, "Hidden", "hidden") == true,
            GenJsonHelper.GetBool(root, "IsEmployee", "isemployee") == true,
            address);
    }

    private async Task<IReadOnlyList<GenActivityRow>> LoadRecentActivitiesAsync(
        GenCredentials credentials,
        string firmId,
        int recentTake,
        CancellationToken ct)
    {
        recentTake = Math.Clamp(recentTake, 1, 20);
        try
        {
            var select = Uri.EscapeDataString(ActivityMapper.ActivitySelectList);
            var where = Uri.EscapeDataString($"Firm_ID eq '{firmId}'");
            var path = $"crmactivities?select={select}&where={where}&take={recentTake}";
            var root = await _gen.GetAsync(path, credentials, ct);
            return ActivityMapper.ParseList(root)
                .OrderByDescending(r => r.ScheduledStart ?? DateTimeOffset.MinValue)
                .Take(recentTake)
                .ToList();
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "Recent activities for firm {FirmId} unavailable", firmId);
            return [];
        }
    }
}
