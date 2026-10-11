using NUnit.Framework;

namespace Pass.IntegrationTests;

public class Tests
{
    [Test]
    public void Runs() => Assert.Fail("Integration tests must not run with the default test-patterns");
}
