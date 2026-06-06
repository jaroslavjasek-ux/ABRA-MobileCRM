using Microsoft.Extensions.Options;

namespace MobileCrm.Adapter.Gen;

public static class FirmSearchQueryBuilder
{
    public static string EscapeODataString(string value) =>
        value.Replace("'", "''", StringComparison.Ordinal);

    public static string BuildListQuery(string term, int take, int skip, GenOptions options)
    {
        var escaped = EscapeODataString(term.Trim());
        var star = EscapeODataString(term.Trim());
        var where = options.FirmSearchWhereTemplate
            .Replace("{q}", escaped, StringComparison.Ordinal)
            .Replace("{qStar}", star, StringComparison.Ordinal);

        if (options.FirmSearchExcludeHidden)
        {
            where = $"({where}) and (Hidden eq false)";
        }

        var select = Uri.EscapeDataString(options.FirmListSelect);
        var whereEnc = Uri.EscapeDataString(where);
        return $"firms?select={select}&where={whereEnc}&take={take}&skip={skip}";
    }
}
