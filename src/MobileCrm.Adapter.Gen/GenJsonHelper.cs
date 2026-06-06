using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

internal static class GenJsonHelper
{
    public static readonly JsonSerializerOptions Options = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    public static string? GetString(JsonElement el, params string[] names)
    {
        foreach (var name in names)
        {
            if (el.TryGetProperty(name, out var prop) && prop.ValueKind == JsonValueKind.String)
            {
                return prop.GetString();
            }
        }
        return null;
    }

    public static int? GetInt(JsonElement el, params string[] names)
    {
        foreach (var name in names)
        {
            if (!el.TryGetProperty(name, out var prop))
            {
                continue;
            }

            if (prop.ValueKind == JsonValueKind.Number && prop.TryGetInt32(out var n))
            {
                return n;
            }

            if (prop.ValueKind == JsonValueKind.String && int.TryParse(prop.GetString(), out var parsed))
            {
                return parsed;
            }
        }
        return null;
    }

    public static bool? GetBool(JsonElement el, params string[] names)
    {
        foreach (var name in names)
        {
            if (!el.TryGetProperty(name, out var prop))
            {
                continue;
            }

            if (prop.ValueKind == JsonValueKind.True)
            {
                return true;
            }

            if (prop.ValueKind == JsonValueKind.False)
            {
                return false;
            }
        }

        return null;
    }

    public static JsonElement? GetObject(JsonElement el, params string[] names)
    {
        foreach (var name in names)
        {
            if (el.TryGetProperty(name, out var prop) && prop.ValueKind == JsonValueKind.Object)
            {
                return prop;
            }
        }

        return null;
    }

    public static IEnumerable<JsonElement> GetArray(JsonElement el, params string[] names)
    {
        foreach (var name in names)
        {
            if (!el.TryGetProperty(name, out var prop) || prop.ValueKind != JsonValueKind.Array)
            {
                continue;
            }

            foreach (var item in prop.EnumerateArray())
            {
                yield return item;
            }

            yield break;
        }
    }

    public static DateTimeOffset? GetDateTime(JsonElement el, params string[] names)
    {
        foreach (var name in names)
        {
            if (!el.TryGetProperty(name, out var prop) || prop.ValueKind != JsonValueKind.String)
            {
                continue;
            }

            var s = prop.GetString();
            if (string.IsNullOrWhiteSpace(s))
            {
                continue;
            }

            if (DateTimeOffset.TryParse(s, out var dto))
            {
                return dto;
            }
        }
        return null;
    }
}
