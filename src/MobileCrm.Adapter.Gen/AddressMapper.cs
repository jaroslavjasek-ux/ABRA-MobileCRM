using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

public sealed record GenAddress(
    string? Line1,
    string? Street,
    string? City,
    string? PostCode,
    string? CountryCode,
    string? Phone1,
    string? Phone2,
    string? Email,
    string? Fax);

public static class AddressMapper
{
    public static GenAddress? Map(JsonElement? addressEl)
    {
        if (addressEl is null || addressEl.Value.ValueKind != JsonValueKind.Object)
        {
            return null;
        }

        var el = addressEl.Value;
        var street = GenJsonHelper.GetString(el, "Street", "street", "OfficialStreet", "officialstreet");
        var city = GenJsonHelper.GetString(el, "City", "city", "OfficialCity", "officialcity");
        var postCode = GenJsonHelper.GetString(el, "PostCode", "postcode", "ZIP", "zip");
        var countryCode = GenJsonHelper.GetString(el, "CountryCode", "countrycode", "Country", "country");
        var phone1 = GenJsonHelper.GetString(el, "PhoneNumber1", "phonenumber1");
        var phone2 = GenJsonHelper.GetString(el, "PhoneNumber2", "phonenumber2");
        var email = GenJsonHelper.GetString(el, "EMail", "email");
        var fax = GenJsonHelper.GetString(el, "FaxNumber", "faxnumber");
        var line1 = GenJsonHelper.GetString(el, "ShortAddress", "shortaddress", "DisplayName", "displayname");

        if (string.IsNullOrWhiteSpace(line1))
        {
            var parts = new[] { street, city, postCode }.Where(p => !string.IsNullOrWhiteSpace(p));
            line1 = string.Join(", ", parts);
            if (string.IsNullOrWhiteSpace(line1))
            {
                line1 = null;
            }
        }

        if (string.IsNullOrWhiteSpace(line1)
            && string.IsNullOrWhiteSpace(street)
            && string.IsNullOrWhiteSpace(city)
            && string.IsNullOrWhiteSpace(phone1)
            && string.IsNullOrWhiteSpace(email))
        {
            return null;
        }

        return new GenAddress(line1, street, city, postCode, countryCode, phone1, phone2, email, fax);
    }

    public static GenAddress? MapFromProperty(JsonElement parent, params string[] propertyNames)
    {
        var obj = GenJsonHelper.GetObject(parent, propertyNames);
        return Map(obj);
    }
}
