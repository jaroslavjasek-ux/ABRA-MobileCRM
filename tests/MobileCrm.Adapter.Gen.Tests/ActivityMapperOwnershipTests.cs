using MobileCrm.Adapter.Gen;

namespace MobileCrm.Adapter.Gen.Tests;

public sealed class ActivityMapperOwnershipTests
{
    [Fact]
    public void BuildOwnershipWhere_includes_solver_and_responsible_only()
    {
        var where = ActivityMapper.BuildOwnershipWhere("1200000101");

        Assert.Contains("ResponsibleUser_ID eq '1200000101'", where);
        Assert.Contains("SolverUser_ID eq '1200000101'", where);
        Assert.DoesNotContain("CreatedBy_ID", where);
    }
}
