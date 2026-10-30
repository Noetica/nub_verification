# Unit and In-Process API Integration Testing Patterns

This document is the canonical testing guidance for unit tests and in-process API integration tests, primarily targeting .NET API and service repositories.

For browser-level E2E testing of GUI applications (web apps, MVC, Angular, Vue, Knockout), see `docs/context-pack/e2e-testing-guidance.md` instead. Both documents may apply to a mixed repository.

Follow these preferred defaults when adding or reviewing tests, unless an existing test project already has a clear, established convention that the repository wants to keep.

Prioritize deterministic, readable tests and consistency with the repository's adopted patterns over forcing one specific harness or folder layout.

Default to a single shared test project for both unit tests and in-process API integration tests.

Do not split unit tests and in-process API integration tests into separate test projects unless the repository already has that structure and the team has explicitly decided to keep it.

## Supported Test Types

This workflow supports only these automated test types:

1. Unit tests
   - isolated component tests
   - mocked or faked collaborators
   - no ASP.NET host
   - no real database
   - no network or filesystem
2. In-process API integration tests
   - may use `WebApplicationFactory` and `HttpClient`
   - may exercise routing, middleware, model binding, serialization, DI wiring, and controller behavior
   - must remain in-process
   - must not depend on deployed Azure infrastructure, Front Door, APIM, live third-party services, or shared environment configuration

Out of scope:

- true end-to-end tests
- deployed-environment tests
- Azure infrastructure validation
- shared-environment smoke tests

## Frameworks and Libraries

Use:

- xUnit
- Awesome Assertions
- NSubstitute
- AutoFixture plus `AutoFixture.AutoNSubstitute`

For in-process API integration tests, use the ASP.NET Core testing stack already present in the repository where available, typically:

- `Microsoft.AspNetCore.Mvc.Testing`
- `WebApplicationFactory`
- `HttpClient`

The `Should()` examples in this document refer to the assertion API from Awesome Assertions.

Do not add `FluentAssertions`.

## Choosing the Test Level

Classify targets as follows:

- domain logic and application services -> unit tests
- API endpoints, request and response behavior, and pipeline behavior -> in-process API integration tests
- Azure infrastructure and deployed environment behavior -> out of scope

Prefer unit tests by default.

Use in-process API integration tests only when host or pipeline behavior is what you need to validate.

## Test Project Layout

Always keep unit tests and in-process API integration tests in one shared test project. Do not create a second test project. Separate the two test types by folders, fixtures, harnesses, and class naming.

This repository treats in-process API integration tests as lightweight enough to live alongside unit tests, which keeps test discovery, local execution, and CI wiring simpler.

Suggested layout inside one test project:

- `Tests/Unit/`
- `Tests/Integration/` for in-process integration tests
- `Testing/` for shared harnesses, fixtures, and test doubles when needed

## Test Structure and Naming

All tests should:

- follow Arrange / Act / Assert
- verify one clear behavior per test
- keep setup readable and near the assertion

Class naming defaults:

- unit test class: `<SubjectUnderTest>Tests`
- in-process API integration test class: `<FeatureOrEndpoint>IntegrationTests`

Test method naming default:

- `<Method>_<Scenario>_<ExpectedResult>`

Examples:

- `PlaceOrder_SendsConfirmationEmail`
- `GetUser_WhenUserMissing_ReturnsNull`

When adding tests to existing legacy code, assert the intended domain behaviour, not just what the code currently does. If the code's observable behaviour conflicts with reasonable domain expectations, write the test with the correct domain assertion — the test will fail, which surfaces a likely defect. Mark such tests clearly (e.g. a comment noting the suspected bug) so a human reviewer can confirm or correct the intent.

If you are genuinely unsure whether the current behaviour is intentional or a defect, write the test both ways: one that pins the current behaviour (marked as a characterization test) and one that asserts the expected domain behaviour (marked as a suspected defect). The human can then decide which to keep.

If a known defect is already identified, write the test to expose it first, then apply the smallest fix that makes it pass.

## Input Matrix Coverage

Test every supported input class, not only invalid inputs. Include acceptance cases for valid-but-unusual forms alongside rejection cases. For security fixes, guard against over-blocking as well as under-blocking.

Cover all source shapes the code accepts. Prefer data-driven tests when multiple input classes should behave similarly. Common input domains and their commonly-missed valid forms include:

- **Filesystem paths** — relative, absolute, UNC (`\\server\share`), trailing separators, embedded spaces, dot segments (`..`).
- **URLs** — scheme variations (HTTP, HTTPS, FTP/SFTP), port numbers (`https://host:8443/path`), query strings (`?key=value`), fragments (`#section`), percent-encoded characters (`%20`, `%2F`), userinfo (`user@host`), and combinations of these in a single URI.
- **Mixed or ambiguous inputs** — values that could be interpreted as either a local path or a URL depending on context.
- **Email addresses** — plus-addressing (`user+tag@example.com`), dots in the local part, long or uncommon TLDs, subdomains, quoted local parts.
- **Dates and times** — leap day (Feb 29), year boundaries (Dec 31 / Jan 1), DST transitions, UTC offsets, ISO 8601 variants (`2024-02-29T23:59:59+13:00`), epoch edge values.
- **Strings and text** — empty vs whitespace-only, Unicode normalization (single `é` vs combining `e` + `\u0301`), right-to-left characters, emoji, multi-byte UTF-8, embedded null bytes, BOM.
- **Numeric values** — negative zero, `int.MaxValue`/`int.MinValue`, decimal precision limits, locale-specific separators (`,` vs `.`), leading zeros.

## Unit Test Harness Pattern

For unit-tested classes with dependencies, prefer a test harness or the repository's equivalent shared setup pattern.

The harness should:

- expose relevant dependencies
- construct the system under test
- optionally provide helper setup methods

If the repository needs a shared base harness and does not already have a convention, `Testing/TestHarness.cs` is a reasonable default location.

If the repository already has an established shared test-support structure, stay consistent with that structure rather than forcing a new one.

Example base harness:

```csharp
using AutoFixture;
using AutoFixture.AutoNSubstitute;

public abstract class TestHarness<TSut>
{
    protected Fixture Fixture { get; } =
        new Fixture().Customize(new AutoNSubstituteCustomization());

    public TSut Sut => Fixture.Create<TSut>();
}
```

Example subject harness:

```csharp
public sealed class OrderServiceHarness : TestHarness<OrderService>
{
    public IOrderRepository Repository => Fixture.Freeze<IOrderRepository>();
    public IEmailSender EmailSender => Fixture.Freeze<IEmailSender>();
}
```

Tests should access the system under test through `h.Sut`.

Keep harnesses shallow and subject-specific. Avoid deep base-class hierarchies or heavily implicit AutoFixture-driven setup that hides what a test depends on. Use explicit values for inputs that drive the behavior under test; reserve AutoFixture for values that must exist but whose specific content does not matter to the assertion.

## In-Process API Integration Test Pattern

For endpoint and pipeline behavior, prefer a shared fixture built around `WebApplicationFactory`.

The fixture should:

- create the application host in-process
- expose an `HttpClient`
- centralize test-only service overrides
- keep external dependencies deterministic

Example:

```csharp
public class OrdersApiFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Replace external collaborators with deterministic test doubles.
        });
    }
}
```

Avoid rebuilding the host in every test method when a shared fixture is sufficient.

Prefer extending an existing shared fixture over creating a second competing integration-test setup pattern.

When the endpoint depends on infrastructure outside the process, replace those collaborators with deterministic fakes or test-only registrations.

In in-process API integration tests, replace external collaborators through test-only service registration.

Prefer deterministic fakes for outbound HTTP, queues, publishers, clocks, and similar infrastructure dependencies.

## Choosing Test Doubles

Prefer NSubstitute mocks when:

- verifying interactions
- the dependency is infrastructure
- the dependency has many members

Typical examples:

- repositories
- HTTP client collaborators other than `HttpClient` itself
- message queues or publishers
- loggers
- external services

Prefer hand-rolled fakes when:

- the interface is very small
- deterministic in-memory behavior is simpler than mocking
- the dependency models domain behavior

Typical examples:

- in-memory repositories
- in-memory queues
- simple domain gateways

Avoid mocking:

- value objects
- entities
- simple deterministic domain logic

## HTTP Client Test Doubles And Disposable Ownership

When unit testing code that uses `HttpClient`, prefer the repository's existing `HttpMessageHandler`-based harness or shared test-support helper.

If the test double returns `HttpResponseMessage`, make ownership explicit:

- create responses through named harness or helper methods rather than inline `Task.FromResult(new HttpResponseMessage(...))` callbacks in each test
- assume the system under test disposes responses it receives from `SendAsync`
- do not dispose the same response in both the test and the production code path

This keeps tests readable, avoids noisy disposal findings, and centralizes common response setup.

## Fake Placement

By default, place reusable fakes in `tests/TestDoubles/`.

If the repository already uses another shared location for test doubles, stay consistent with that location rather than moving everything to this default.

Avoid defining reusable fake classes inside individual tests.

Small helper objects that are only useful to one test file are acceptable.

## Behavior vs Interaction Assertions

Prefer observable behavior assertions when possible.

For in-process API integration tests, assert the full observable contract that matters to the scenario, not only the HTTP status code.

When relevant, also assert response body, headers, content type, validation payloads, and persisted or emitted side effects.

Use `Received()` only when interaction verification is required.

Examples:

```csharp
result.Should().Be(expected);
await repo.Received().Save(order);
```

Avoid verifying trivial interactions.

## Deterministic Tests

Unit tests must not depend on:

- real databases
- filesystem access
- HTTP or network access
- Azure services
- system clock
- randomness

In-process API integration tests may use in-process HTTP via `WebApplicationFactory` and `HttpClient`, but must not depend on:

- deployed Azure infrastructure
- Front Door or APIM
- live third-party services
- shared environment configuration
- real databases unless the repository already has an explicitly local, deterministic in-process test setup

Use abstractions, fakes, or test-only registrations to keep tests deterministic.

Where production code depends on time, prefer an injected clock abstraction.

Unit tests and in-process API integration tests must control time explicitly rather than reading the system clock.

## SQLite in In-Process Integration Tests

SQLite may be used only where the test has an explicitly local, deterministic in-process setup and persistence behaviour is part of the scenario being validated.

Use it to keep tests fast and self-contained when relational database behaviour adds confidence beyond mocks or fakes.

Do not use SQLite in unit tests.

Do not assume SQLite is equivalent to SQL Server. If the code under test depends on SQL Server-specific behaviour, validate that with a SQL Server-specific test approach rather than SQLite.

## Minimal Production Changes

Prefer test-only changes.

Change production code only when a narrow seam is required for testability or determinism.

Production code may introduce small seams when necessary for testability, for example:

- constructor injection
- interface extraction
- clock abstraction
- test-only service registration seams for in-process API integration tests

If a narrow seam will not make the behaviour meaningfully testable, a broader seam may be justified. In that case, explain why the smaller seam is insufficient, describe the minimum broader seam that would unlock the test, and ask the human before treating it as normal test implementation work.

Avoid architectural refactors when adding tests.

## Example Unit Test

```csharp
public class OrderServiceTests
{
    [Fact]
    public async Task PlaceOrder_SavesOrder()
    {
        // Arrange
        var h = new OrderServiceHarness();
        var order = new Order();

        // Act
        await h.Sut.PlaceOrder(order);

        // Assert
        await h.Repository.Received().Save(order);
    }
}
```

## Example In-Process API Integration Test

```csharp
public class OrdersIntegrationTests : IClassFixture<OrdersApiFactory>
{
    private readonly HttpClient client;

    public OrdersIntegrationTests(OrdersApiFactory factory)
    {
        client = factory.CreateClient();
    }

    [Fact]
    public async Task PostOrders_WithInvalidPayload_ReturnsBadRequest()
    {
        // Arrange
        var payload = new { Quantity = 0 };

        // Act
        var response = await client.PostAsJsonAsync("/orders", payload);
        var problem = await response.Content.ReadFromJsonAsync<ValidationProblemDetails>();

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        response.Content.Headers.ContentType?.MediaType.Should().Be("application/problem+json");
        problem.Should().NotBeNull();
        problem!.Errors.Should().ContainKey("Quantity");
    }
}
```

## Key Principles

1. Test behavior, not implementation details.
2. Keep tests small and readable.
3. Prefer harnesses or the repository's equivalent shared setup pattern over repeated setup when the system under test has dependencies.
4. Prefer simple fakes over complex mocks when practical.
5. Keep tests deterministic and fast.
6. Prefer minimal testability seams over broad production refactors.
7. Prefer existing repository test structure over introducing a competing shared layout unless the repository is standardizing on a new one.
8. When establishing a new test structure, keep unit tests and in-process API integration tests in one shared test project by default.
