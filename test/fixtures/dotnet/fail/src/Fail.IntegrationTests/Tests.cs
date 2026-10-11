using NUnit.Framework;

namespace Fail.IntegrationTests;

public class Tests
{
    [Test]
    public void Runs() => Assert.Fail("Expected failure");
}
