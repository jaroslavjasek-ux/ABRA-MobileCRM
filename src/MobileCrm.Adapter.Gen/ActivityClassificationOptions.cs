namespace MobileCrm.Adapter.Gen;

public sealed class ActivityClassificationOptions
{
    public const string SectionName = "ActivityClassification";

    public bool Area { get; set; } = true;

    public bool Type { get; set; } = true;

    public bool Queue { get; set; } = true;

    public bool Process { get; set; }

    public bool AutoHideSingleValue { get; set; } = true;
}
