using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace MobileCrm.Adapter.Gen;

internal sealed record ActivityLookupResult(JsonElement Root, string CanonicalId, string Strategy);

internal static class ActivityLookup
{
    public static async Task<ActivityLookupResult?> LoadAsync(
        IGenApiClient gen,
        GenCredentials credentials,
        string activityKey,
        ILogger logger,
        CancellationToken ct)
    {
        var key = activityKey.Trim();
        if (string.IsNullOrEmpty(key))
        {
            logger.LogWarning("Activity lookup rejected: empty activity key");
            return null;
        }

        logger.LogInformation("Activity lookup started for key {ActivityKey}", key);

        var select = Uri.EscapeDataString(ActivityMapper.ActivityDetailSelect);

        var byPath = await TryLoadByPathAsync(gen, credentials, key, select, "path", logger, ct);
        if (byPath is not null)
        {
            return byPath;
        }

        foreach (var (where, strategy) in BuildFallbackWheres(key))
        {
            var fromList = await TryLoadByWhereAsync(
                gen, credentials, where, select, strategy, logger, ct);
            if (fromList is not null)
            {
                return fromList;
            }
        }

        var byPathFull = await TryLoadByPathAsync(
            gen, credentials, key, select: null, "path-full", logger, ct);
        if (byPathFull is not null)
        {
            return byPathFull;
        }

        logger.LogWarning(
            "Activity lookup failed for key {ActivityKey}: no match via path or fallback where",
            key);
        return null;
    }

    private static IEnumerable<(string Where, string Strategy)> BuildFallbackWheres(string key)
    {
        var escaped = FirmSearchQueryBuilder.EscapeODataString(key);
        yield return ($"ID eq '{escaped}'", "where-id");
        yield return ($"id eq '{escaped}'", "where-id-lower");
        yield return ($"DisplayName eq '{escaped}'", "where-displayname");
    }

    private static async Task<ActivityLookupResult?> TryLoadByPathAsync(
        IGenApiClient gen,
        GenCredentials credentials,
        string key,
        string? select,
        string strategy,
        ILogger logger,
        CancellationToken ct)
    {
        var path = string.IsNullOrEmpty(select)
            ? $"crmactivities/{key}"
            : $"crmactivities/{key}?select={select}";

        logger.LogInformation("Activity Gen GET {Path} (strategy {Strategy})", path, strategy);

        try
        {
            var root = await gen.GetAsync(path, credentials, ct);
            return MapResult(root, strategy, logger);
        }
        catch (GenApiException ex) when (ex.StatusCode is 404)
        {
            logger.LogWarning(
                "Activity Gen GET 404 for key {ActivityKey} (strategy {Strategy})",
                key,
                strategy);
            return null;
        }
        catch (GenApiException ex)
        {
            logger.LogWarning(
                ex,
                "Activity Gen GET failed with {Status} for key {ActivityKey} (strategy {Strategy})",
                ex.StatusCode,
                key,
                strategy);
            return null;
        }
    }

    private static async Task<ActivityLookupResult?> TryLoadByWhereAsync(
        IGenApiClient gen,
        GenCredentials credentials,
        string where,
        string select,
        string strategy,
        ILogger logger,
        CancellationToken ct)
    {
        var query =
            $"crmactivities?select={select}&where={Uri.EscapeDataString(where)}&take=1";

        logger.LogInformation(
            "Activity Gen list fallback {Strategy}: {Query}",
            strategy,
            query);

        try
        {
            var root = await gen.GetAsync(query, credentials, ct);
            var rows = ActivityMapper.ParseList(root);
            logger.LogInformation(
                "Activity fallback {Strategy} returned {Count} row(s)",
                strategy,
                rows.Count);

            if (rows.Count == 0)
            {
                return null;
            }

            var canonicalId = rows[0].Id;
            if (string.IsNullOrEmpty(canonicalId))
            {
                logger.LogWarning(
                    "Activity fallback {Strategy} row missing canonical ID",
                    strategy);
                return null;
            }

            if (canonicalId == rows[0].Subject)
            {
                logger.LogWarning(
                    "Activity fallback {Strategy} suspicious ID equals subject",
                    strategy);
            }

            return await TryLoadByPathAsync(
                gen,
                credentials,
                canonicalId,
                select,
                $"{strategy}-refetch",
                logger,
                ct);
        }
        catch (GenApiException ex)
        {
            logger.LogWarning(
                ex,
                "Activity fallback {Strategy} failed with Gen status {Status}",
                strategy,
                ex.StatusCode);
            return null;
        }
    }

    private static ActivityLookupResult? MapResult(
        JsonElement root,
        string strategy,
        ILogger logger)
    {
        var canonicalId = ActivityMapper.GetCanonicalId(root);
        if (string.IsNullOrEmpty(canonicalId))
        {
            logger.LogWarning(
                "Activity lookup strategy {Strategy} returned payload without ID/id",
                strategy);
            return null;
        }

        logger.LogInformation(
            "Activity lookup succeeded via {Strategy}: canonicalId={CanonicalId}",
            strategy,
            canonicalId);

        return new ActivityLookupResult(root, canonicalId, strategy);
    }
}
