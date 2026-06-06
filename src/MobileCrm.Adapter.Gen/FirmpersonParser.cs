using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

public sealed record FirmpersonLink(
    string PersonId,
    string? DisplayName,
    int PosIndex,
    GenAddress? Address);

public static class FirmpersonParser
{
    private static readonly string[] EmptyPersonIds = ["0000000000", "__________"];

    public static IReadOnlyList<FirmpersonLink> ParseFromFirm(JsonElement firm)
    {
        var links = new List<FirmpersonLink>();
        foreach (var fp in GenJsonHelper.GetArray(firm, "firmpersons", "FirmPersons"))
        {
            var personId = GenJsonHelper.GetString(fp, "Person_ID", "person_id");
            if (string.IsNullOrWhiteSpace(personId) || EmptyPersonIds.Contains(personId))
            {
                continue;
            }

            var displayName = GenJsonHelper.GetString(fp, "DisplayName", "displayname");
            var posIndex = GenJsonHelper.GetInt(fp, "PosIndex", "posindex") ?? int.MaxValue;
            var address = AddressMapper.MapFromProperty(fp, "Address_ID", "address_id");
            links.Add(new FirmpersonLink(personId, displayName, posIndex, address));
        }

        return links.OrderBy(l => l.PosIndex).ToList();
    }

    public static string? ResolvePrimaryPersonId(string? initialFirmPersonId, IReadOnlyList<FirmpersonLink> links)
    {
        if (!string.IsNullOrWhiteSpace(initialFirmPersonId)
            && !EmptyPersonIds.Contains(initialFirmPersonId)
            && links.Any(l => l.PersonId == initialFirmPersonId))
        {
            return initialFirmPersonId;
        }

        return links.OrderBy(l => l.PosIndex).FirstOrDefault()?.PersonId;
    }
}
