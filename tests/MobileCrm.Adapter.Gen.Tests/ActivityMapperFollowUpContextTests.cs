using MobileCrm.Adapter.Gen;

namespace MobileCrm.Adapter.Gen.Tests;

public sealed class ActivityMapperFollowUpContextTests
{
    [Fact]
    public void ResolveFollowUpTextFields_copies_source_answer()
    {
        var (description, answer) = ActivityMapper.ResolveFollowUpTextFields(
            "Source brief",
            "08.06.2026 10:00 | JANO\nOutcome\n\n---\n\nOlder note",
            "Next step plan");

        Assert.Equal("Next step plan", description);
        Assert.Equal("08.06.2026 10:00 | JANO\nOutcome\n\n---\n\nOlder note", answer);
    }

    [Fact]
    public void ResolveFollowUpTextFields_inherits_source_description_when_user_blank()
    {
        var (description, answer) = ActivityMapper.ResolveFollowUpTextFields(
            "Original visit brief",
            "note history",
            null);

        Assert.Equal("Original visit brief", description);
        Assert.Equal("note history", answer);
    }

    [Fact]
    public void ResolveFollowUpTextFields_returns_nulls_when_source_empty()
    {
        var (description, answer) = ActivityMapper.ResolveFollowUpTextFields(null, null, null);

        Assert.Null(description);
        Assert.Null(answer);
    }

    [Fact]
    public void ResolveFollowUpTextFields_user_description_overrides_source_description()
    {
        var (description, answer) = ActivityMapper.ResolveFollowUpTextFields(
            "Old brief",
            "history",
            "  New plan  ");

        Assert.Equal("New plan", description);
        Assert.Equal("history", answer);
    }
}
