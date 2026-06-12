using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

public sealed record GenValidationError(
    string Field,
    int? Code,
    string? Message,
    string? DisplayLabel);

internal static class GenValidation
{
    private static readonly HashSet<string> ClassificationFields = new(StringComparer.OrdinalIgnoreCase)
    {
        "activityarea_id",
        "activitytype_id",
        "actqueue_id",
    };

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

    public static IReadOnlyList<GenValidationError> ParseErrors(JsonElement root)
    {
        if (!TryGetMeta(root, out var meta)
            || !meta.TryGetProperty("validation", out var validation)
            || !validation.TryGetProperty("errors", out var errors)
            || !errors.TryGetProperty("values", out var values)
            || values.ValueKind != JsonValueKind.Array)
        {
            return [];
        }

        var parsed = new List<GenValidationError>();
        foreach (var item in values.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.Object)
            {
                continue;
            }

            foreach (var property in item.EnumerateObject())
            {
                if (property.Value.ValueKind != JsonValueKind.Object)
                {
                    continue;
                }

                parsed.Add(new GenValidationError(
                    property.Name,
                    TryReadCode(property.Value),
                    GenJsonHelper.GetString(property.Value, "@description", "description"),
                    GenJsonHelper.GetString(property.Value, "@displaylabel", "displaylabel")));
            }
        }

        return parsed;
    }

    public static bool HasFieldError(JsonElement root, string fieldName)
    {
        foreach (var error in ParseErrors(root))
        {
            if (string.Equals(error.Field, fieldName, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }

    public static bool HasClassificationErrors(JsonElement root)
    {
        foreach (var error in ParseErrors(root))
        {
            if (IsClassificationError(error))
            {
                return true;
            }
        }

        return false;
    }

    public static bool TryParseResponseBody(string? body, out JsonElement root)
    {
        root = default;
        if (string.IsNullOrWhiteSpace(body))
        {
            return false;
        }

        try
        {
            using var doc = JsonDocument.Parse(body);
            root = doc.RootElement.Clone();
            return true;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static bool IsClassificationError(GenValidationError error)
    {
        if (ClassificationFields.Contains(error.Field))
        {
            return true;
        }

        return string.Equals(error.Field, "period_id", StringComparison.OrdinalIgnoreCase)
            && error.Code == 801;
    }

    private static int? TryReadCode(JsonElement detail)
    {
        if (detail.TryGetProperty("@code", out var codeProp) && codeProp.TryGetInt32(out var code))
        {
            return code;
        }

        if (detail.TryGetProperty("code", out codeProp) && codeProp.TryGetInt32(out code))
        {
            return code;
        }

        return null;
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
