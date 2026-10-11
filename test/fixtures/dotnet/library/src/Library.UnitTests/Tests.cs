using NUnit.Framework;

namespace Library.UnitTests;

public class Tests
{
    [Test]
    public void Runs() => Assert.That(Greeting.Hello(), Is.EqualTo("hello"));
}
