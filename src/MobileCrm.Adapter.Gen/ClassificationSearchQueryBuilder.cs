namespace MobileCrm.Adapter.Gen;

internal static class ClassificationSearchQueryBuilder
{
    private const string Select = "ID,Code,Name,DisplayName";

    public static string BuildListQuery(string collection, string? query, int take, int skip)
    {
        var clauses = new List<string>();
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
