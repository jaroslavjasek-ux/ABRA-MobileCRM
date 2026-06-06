using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

internal static class GenValidation
{
    public static int GetErrorCount(JsonElement root)
    {
        if (!TryGetMeta(root, out var meta))
        {
            return 0;
        }

        if (!meta.TryGetProperty("validation", out var validation))
        {
            return 0;
        }

        if (!validation.TryGetProperty("errors", out var errors))
        {
            return 0;
        }

        if (errors.TryGetProperty("count", out var countProp) && countProp.TryGetInt32(out var count))
        {
            return count;
        }

        if (errors.TryGetProperty("values", out var values) && values.ValueKind == JsonValueKind.Array)
        {
            return values.GetArrayLength();
        }

        return 0;
    }

    private static bool TryGetMeta(JsonElement root, out JsonElement meta)
    {
        if (root.TryGetProperty("@meta", out meta))
        {
            return true;
        }

        if (root.TryGetProperty("meta", out meta))
        {
            return true;
        }

        meta = default;
        return false;
    }
}
