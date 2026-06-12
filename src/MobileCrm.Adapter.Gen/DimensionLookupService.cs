using Microsoft.Extensions.Logging;

namespace MobileCrm.Adapter.Gen;

public enum DimensionKind
{
    BusinessCase,
    WorkOrder,
    Project,
}

public sealed record GenDimensionSearchResult(
    IReadOnlyList<GenDimensionRow> Items,
    int Total,
    bool HasMore);

public interface IDimensionLookupService
{
    Task<GenDimensionSearchResult> SearchAsync(
        GenCredentials credentials,
        DimensionKind kind,
        string? query,
        string? firmId,
        int take,
        int skip,
        CancellationToken ct = default);
}

public sealed class DimensionLookupService : IDimensionLookupService
{
    private readonly IGenApiClient _gen;
    private readonly ILogger<DimensionLookupService> _logger;

    public DimensionLookupService(IGenApiClient gen, ILogger<DimensionLookupService> logger)
    {
        _gen = gen;
        _logger = logger;
    }

    public async Task<GenDimensionSearchResult> SearchAsync(
        GenCredentials credentials,
        DimensionKind kind,
        string? query,
        string? firmId,
        int take,
        int skip,
        CancellationToken ct = default)
    {
        take = Math.Clamp(take, 1, 50);
        skip = Math.Max(0, skip);

        if (!string.IsNullOrWhiteSpace(firmId))
        {
            var scoped = await FetchPageAsync(credentials, kind, query, firmId.Trim(), take, skip, ct);
            if (scoped.Items.Count > 0 || !string.IsNullOrWhiteSpace(query))
            {
                return scoped;
            }

            _logger.LogDebug(
                "Dimension search firm-scoped empty for {Kind} firmId={FirmId}; falling back to global list",
                kind,
                firmId);
        }

        return await FetchPageAsync(credentials, kind, query, firmId: null, take, skip, ct);
    }

    private async Task<GenDimensionSearchResult> FetchPageAsync(
        GenCredentials credentials,
        DimensionKind kind,
        string? query,
        string? firmId,
        int take,
        int skip,
        CancellationToken ct)
    {
        var collection = ResolveCollection(kind);
        var path = DimensionSearchQueryBuilder.BuildListQuery(collection, query, firmId, take + 1, skip);
        var root = await _gen.GetAsync(path, credentials, ct);
        var all = DimensionMapper.ParseList(root)
            .Where(row => !string.IsNullOrEmpty(row.Id))
            .ToList();

        var hasMore = all.Count > take;
        if (hasMore)
        {
            all = all.Take(take).ToList();
        }

        return new GenDimensionSearchResult(all, all.Count, hasMore);
    }

    private static string ResolveCollection(DimensionKind kind) =>
        kind switch
        {
            DimensionKind.BusinessCase => "bustransactions",
            DimensionKind.WorkOrder => "busorders",
            DimensionKind.Project => "busprojects",
            _ => throw new ArgumentOutOfRangeException(nameof(kind)),
        };
}
