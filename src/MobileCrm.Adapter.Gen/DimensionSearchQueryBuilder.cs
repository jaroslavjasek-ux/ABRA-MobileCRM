namespace MobileCrm.Adapter.Gen;

internal static class DimensionSearchQueryBuilder
{
    private const string Select = "ID,DisplayName,Code,Name,Firm_ID";

    public static string BuildListQuery(
        string collection,
        string? query,
        string? firmId,
        int take,
        int skip)
    {
        var clauses = new List<string>();
        if (!string.IsNullOrWhiteSpace(firmId))
        {
            clauses.Add($"Firm_ID eq '{FirmSearchQueryBuilder.EscapeODataString(firmId.Trim())}'");
        }

        var term = (query ?? "").Trim();
        if (term.Length > 0)
        {
            var escaped = FirmSearchQueryBuilder.EscapeODataString(term);
            clauses.Add($"(Code like '*{escaped}*' or Name like '*{escaped}*')");
        }

        var whereEnc = clauses.Count > 0
            ? $"&where={Uri.EscapeDataString(string.Join(" and ", clauses))}"
            : "";

        var selectEnc = Uri.EscapeDataString(Select);
        return $"{collection}?select={selectEnc}&take={take}&skip={skip}{whereEnc}";
    }
}
