using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

public static class FirmMapper
{
    public static GenFirmSummary ToSummary(JsonElement el)
    {
        var residence = AddressMapper.MapFromProperty(el, "residenceaddress_id", "ResidenceAddress_ID");
        return new GenFirmSummary(
            GenJsonHelper.GetString(el, "ID", "id") ?? "",
            GenJsonHelper.GetString(el, "Name", "name") ?? "",
            GenJsonHelper.GetString(el, "Code", "code") ?? "",
            GenJsonHelper.GetString(el, "OrgIdentNumber", "orgidentnumber", "ICO", "ico"),
            residence?.City,
            MapCommercialStatus(GenJsonHelper.GetString(el, "PMState_ID", "pmstate_id")));
    }

    public static IReadOnlyList<GenFirmSummary> ParseSummaryList(JsonElement root)
    {
        if (root.ValueKind == JsonValueKind.Array)
        {
            return root.EnumerateArray().Select(ToSummary).ToList();
        }

        return [];
    }

    public static string MapCommercialStatus(string? pmStateId) =>
        string.IsNullOrWhiteSpace(pmStateId) ? "unknown" : "active";

    public static GenContactSummary ToContactSummary(
        FirmpersonLink link,
        PersonContactInfo? person,
        string? primaryPersonId)
    {
        var phone = link.Address?.Phone1 ?? person?.Address?.Phone1;
        var email = link.Address?.Email ?? person?.Address?.Email;
        if (string.IsNullOrWhiteSpace(phone) && string.IsNullOrWhiteSpace(email))
        {
            phone = person?.Address?.Phone1;
            email = person?.Address?.Email;
        }

        return new GenContactSummary(
            link.PersonId,
            person?.DisplayName ?? link.DisplayName ?? "",
            person?.FirstName,
            person?.LastName,
            person?.JobTitle,
            primaryPersonId == link.PersonId,
            phone,
            email);
    }
}

public sealed record PersonContactInfo(
    string Id,
    string? DisplayName,
    string? FirstName,
    string? LastName,
    string? JobTitle,
    bool Hidden,
    bool IsEmployee,
    GenAddress? Address);
