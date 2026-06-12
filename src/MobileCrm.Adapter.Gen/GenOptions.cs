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

    /// <summary>Tenant defaults for standalone activity create (ActQueue, Period, Division, …).</summary>
    public ActivityReferenceDefaultsOptions ReferenceDefaults { get; set; } = new();

    /// <summary>Firm used for Gen validate-probe classification filtering (DEMO: Galenit).</summary>
    public string? ClassificationProbeFirmId { get; set; }
}

public sealed class ActivityReferenceDefaultsOptions
{
    public string? ActQueueId { get; set; }
    public string? PeriodId { get; set; }
    public string? DivisionId { get; set; }
    public string? SolverRoleId { get; set; }
    public string? ActivityAreaId { get; set; }
    public string? ActivityTypeId { get; set; }
}

public sealed class GenCredentials
{
    public required string LoginName { get; init; }
    public required string Password { get; init; }
}
