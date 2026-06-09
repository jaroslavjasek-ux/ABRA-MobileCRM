using MobileCrm.Adapter.Gen;

namespace MobileCrm.Adapter.Gen.Tests;

public sealed class ActivityMapperAppendAnswerTests
{
  private const string Separator = "\n\n---\n\n";

  [Fact]
  public void AppendAnswer_prepends_new_entry_before_existing_history()
  {
    var timestamp = new DateTimeOffset(2026, 6, 8, 10, 0, 0, TimeSpan.FromHours(2));
    var existing = ActivityMapper.AppendAnswer(
      null,
      "entry A",
      new DateTimeOffset(2026, 6, 7, 9, 0, 0, TimeSpan.FromHours(2)),
      "Jaroslav Novák");

    var result = ActivityMapper.AppendAnswer(existing, "entry B", timestamp, "Jaroslav Novák");

    var separatorIndex = result.IndexOf(Separator, StringComparison.Ordinal);
    Assert.True(separatorIndex > 0, result);

    var newest = result[..separatorIndex];
    var older = result[(separatorIndex + Separator.Length)..];

    Assert.StartsWith("08.06.2026 10:00 | Jaroslav Novák", newest);
    Assert.Contains("entry B", newest);
    Assert.Contains("entry A", older);
    Assert.True(result.IndexOf("entry B", StringComparison.Ordinal) < result.IndexOf("entry A", StringComparison.Ordinal));
  }

  [Fact]
  public void AppendAnswer_empty_existing_includes_header()
  {
    var timestamp = new DateTimeOffset(2026, 6, 9, 8, 50, 0, TimeSpan.FromHours(2));

    var result = ActivityMapper.AppendAnswer(null, "odovzdávam JAROJ", timestamp, "Jaroslav Novák");

    Assert.StartsWith("09.06.2026 08:50 | Jaroslav Novák", result);
    Assert.EndsWith("odovzdávam JAROJ", result);
    Assert.DoesNotContain(Separator, result);
  }

  [Fact]
  public void AppendAnswer_includes_author_in_newest_block()
  {
    var timestamp = new DateTimeOffset(2026, 6, 8, 10, 0, 0, TimeSpan.FromHours(2));

    var result = ActivityMapper.AppendAnswer("entry A", "entry B", timestamp, "Jaroslav Novák");

    Assert.StartsWith("08.06.2026 10:00 | Jaroslav Novák", result);
    Assert.Contains($"{Separator}entry A", result);
  }

  [Fact]
  public void AppendAnswer_third_entry_becomes_topmost()
  {
    var first = ActivityMapper.AppendAnswer(null, "entry A", new DateTimeOffset(2026, 6, 6, 9, 0, 0, TimeSpan.FromHours(2)));
    var second = ActivityMapper.AppendAnswer(first, "entry B", new DateTimeOffset(2026, 6, 7, 9, 0, 0, TimeSpan.FromHours(2)));
    var third = ActivityMapper.AppendAnswer(second, "entry C", new DateTimeOffset(2026, 6, 8, 9, 0, 0, TimeSpan.FromHours(2)));

    Assert.Contains("entry C", third);
    Assert.True(third.IndexOf("entry C", StringComparison.Ordinal) < third.IndexOf("entry B", StringComparison.Ordinal));
    Assert.True(third.IndexOf("entry B", StringComparison.Ordinal) < third.IndexOf("entry A", StringComparison.Ordinal));
  }
}
