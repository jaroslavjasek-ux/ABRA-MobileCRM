using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

public sealed record GenClassificationRow(
    string Id,
    string Code,
    string Name,
    string DisplayName);

public static class ClassificationMapper
{
    public static GenClassificationRow ToRow(JsonElement el)
    {
        var id = GenJsonHelper.GetString(el, "ID", "id") ?? "";
        var code = GenJsonHelper.GetString(el, "Code", "code") ?? "";
        var name = GenJsonHelper.GetString(el, "Name", "name") ?? "";
        var displayName = GenJsonHelper.GetString(el, "DisplayName", "displayname")
            ?? (string.IsNullOrEmpty(code) && string.IsNullOrEmpty(name) ? id : $"{code} {name}".Trim());
        return new GenClassificationRow(id, code, name, displayName);
    }

    public static IReadOnlyList<GenClassificationRow> ParseList(JsonElement root)
    {
        if (root.ValueKind == JsonValueKind.Array)
        {
            return root.EnumerateArray().Select(ToRow).ToList();
        }

        return [];
    }
}
