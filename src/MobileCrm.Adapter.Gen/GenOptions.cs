namespace MobileCrm.Adapter.Gen;

public sealed class GenOptions
{
    public const string SectionName = "Gen";

    public string BaseUrl { get; set; } = "http://localhost/demo";
    public int TimeoutSeconds { get; set; } = 60;
    public string TimeZoneId { get; set; } = "Europe/Bratislava";

    /// <summary>
    /// OData-style where template for firm search. Placeholders: {q} (escaped term), {qStar} (term wrapped in *).
    /// </summary>
    public string FirmSearchWhereTemplate { get; set; } =
        "(Name like '*{qStar}*' or Code like '*{qStar}*' or OrgIdentNumber like '*{qStar}*')";

    public bool FirmSearchExcludeHidden { get; set; } = true;

    public string FirmListSelect { get; set; } =
        "ID,Name,Code,OrgIdentNumber,Hidden,PMState_ID,residenceaddress_id";

    public string PersonContactSelect { get; set; } =
        "ID,FirstName,LastName,FullName,DisplayName,Grade,Address_ID,Hidden,IsEmployee";
}

public sealed class GenCredentials
{
    public required string LoginName { get; init; }
    public required string Password { get; init; }
}
