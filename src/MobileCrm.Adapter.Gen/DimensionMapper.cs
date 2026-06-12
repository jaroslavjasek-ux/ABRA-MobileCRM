using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

public sealed record GenDimensionRow(string Id, string DisplayName);

public static class DimensionMapper
{
    public static GenDimensionRow ToRow(JsonElement el)
    {
        var id = GenJsonHelper.GetString(el, "ID", "id") ?? "";
        var displayName = GenJsonHelper.GetString(el, "DisplayName", "displayname")
            ?? GenJsonHelper.GetString(el, "Name", "name")
            ?? GenJsonHelper.GetString(el, "Code", "code")
            ?? id;
        return new GenDimensionRow(id, displayName);
    }

    public static IReadOnlyList<GenDimensionRow> ParseList(JsonElement root)
    {
        if (root.ValueKind == JsonValueKind.Array)
        {
            return root.EnumerateArray().Select(ToRow).ToList();
        }

        return [];
    }
}
