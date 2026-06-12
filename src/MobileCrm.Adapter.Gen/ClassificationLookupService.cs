using Microsoft.Extensions.Logging;

namespace MobileCrm.Adapter.Gen;

public enum ClassificationKind
{
    Area,
    Type,
    Queue,
}

public sealed record GenClassificationSearchResult(
    IReadOnlyList<GenClassificationRow> Items,
    int Total,
    bool HasMore);

public interface IClassificationLookupService
{
    Task<GenClassificationSearchResult> SearchAsync(
        GenCredentials credentials,
        ClassificationKind kind,
        string? query,
        int take,
        int skip,
        CancellationToken ct = default);
}

public sealed class ClassificationLookupService : IClassificationLookupService
{
    private readonly IGenApiClient _gen;
    private readonly ILogger<ClassificationLookupService> _logger;

    public ClassificationLookupService(IGenApiClient gen, ILogger<ClassificationLookupService> logger)
    {
        _gen = gen;
        _logger = logger;
    }

    public async Task<GenClassificationSearchResult> SearchAsync(
        GenCredentials credentials,
        ClassificationKind kind,
        string? query,
        int take,
        int skip,
        CancellationToken ct = default)
    {
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        var collection = ResolveCollection(kind);
        var path = ClassificationSearchQueryBuilder.BuildListQuery(collection, query, take + 1, skip);
        var root = await _gen.GetAsync(path, credentials, ct);
        var all = ClassificationMapper.ParseList(root)
            .Where(row => !string.IsNullOrEmpty(row.Id))
            .ToList();

        var hasMore = all.Count > take;
        if (hasMore)
        {
            all = all.Take(take).ToList();
        }

        _logger.LogDebug(
            "Classification search {Kind} returned {Count} items (hasMore={HasMore})",
            kind,
            all.Count,
            hasMore);

        return new GenClassificationSearchResult(all, all.Count, hasMore);
    }

    private static string ResolveCollection(ClassificationKind kind) =>
        kind switch
        {
            ClassificationKind.Area => "crmactivityareas",
            ClassificationKind.Type => "crmactivitytypes",
            ClassificationKind.Queue => "crmactivityqueues",
            _ => throw new ArgumentOutOfRangeException(nameof(kind)),
        };
}
