using NUnit.Framework;

namespace Library.UnitTests;

public class Tests
{
    [Test]
    public void Runs() => Assert.That(Greeting.Hello(), Is.EqualTo("hello"));

    // dotnet-build excludes LocalOnly tests; fixture-dotnet-library asserts it ran only Runs.
    [Test]
    [Category("LocalOnly")]
    public void Is_excluded() => Assert.Fail("LocalOnly tests must not run in CI");
}
