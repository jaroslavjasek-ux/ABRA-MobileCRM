namespace MobileCrm.Adapter.Gen;

public sealed class ActivityDimensionOptions
{
    public const string SectionName = "ActivityDimensions";

    public bool BusinessCase { get; set; } = true;

    public bool WorkOrder { get; set; } = true;

    public bool Project { get; set; } = true;
}
