## Generic integration and deployed system testing guidance

Purpose: provide a consistent default approach for two test layers that sit above unit and in-process API integration tests:

1. **Integration tests** — exercise application code against real, test-controlled infrastructure dependencies such as SQL Server, PostgreSQL, Redis, Azurite, or NATS.io. Database integration tests are the main example because persistence failures are common and high-impact.
2. **Deployed system tests** — exercise a deployed API or service in a real non-production environment.

This is intentionally technology- and product-agnostic, but assumes the common Noetica shape of .NET services, xUnit, SQL Server-backed persistence, GitHub Actions, Azure-hosted non-production environments, and LLM-assisted code changes.

### Scope and related documents

This document covers only out-of-process integration tests and deployed system tests. For other test layers, follow the canonical guidance in the documents below and do not duplicate it here. Database integration tests are called out throughout as a particular integration-test example, not as the only valid use of this layer.

- **Unit tests and in-process API integration tests** — see [testing-patterns.md](testing-patterns.md). That document is the source of truth for xUnit conventions, harness and fake patterns, AutoFixture/NSubstitute/Awesome Assertions usage, `HttpClient` test doubles, `WebApplicationFactory` patterns, determinism rules, and minimal testability seams. Anything that can be tested in-process belongs there.
- **Browser-level E2E tests for UI repositories** — see [e2e-testing-guidance.md](e2e-testing-guidance.md). That document is the source of truth for Playwright usage, automation identities, MFA handling, cached auth state, and the shared automation config contract. Deployed system tests in this document deliberately reuse that auth model rather than inventing a parallel one.

The aim is not a rigid taxonomy. The aim is that each test answers a clear confidence question, runs at the right point in the delivery flow, and does not become a slow, fragile tax on normal development.

### Core principles

- Use different test layers for different confidence questions.
- Keep the fast developer and LLM guardrail loop small, deterministic, and infrastructure-light. That loop lives under [testing-patterns.md](testing-patterns.md).
- Use real infrastructure dependencies where correctness depends on provider, protocol, or broker behaviour.
- For database integration tests, use the real database engine where correctness depends on provider behaviour.
- Use deployed-environment tests to validate configuration, authentication, networking, and real service wiring.
- Prefer isolated, disposable test state over shared mutable test data.
- Reuse request builders, API clients, and scenario helpers across layers where it keeps tests readable, but keep fixtures separate.
- Do not make a shared DEV or UAT environment the only source of branch validation.

### How this fits with the wider suite

The full picture across the testing documents:

| Layer | Where defined | Confidence question |
|---|---|---|
| Unit / guardrail tests | [testing-patterns.md](testing-patterns.md) | Does pure logic behave correctly? |
| In-process API integration tests | [testing-patterns.md](testing-patterns.md) | Do routing, middleware, DI, validation, and persistence work together in-process? |
| Integration tests | This document | Does code work against real infrastructure dependencies such as databases, message brokers, caches, or storage emulators? |
| Deployed system tests | This document | Does the deployed system actually work in a real non-production environment? |
| Browser E2E tests | [e2e-testing-guidance.md](e2e-testing-guidance.md) | Does the UI work end-to-end as a user experiences it? |

A repository may not need every layer. Start with what gives the most confidence per unit of effort, given what the service actually does.

### Test project organisation

The boundary that earns its keep is **needs container vs does not need container**. Recommended default split:

- `MyApi.Tests` — unit tests + in-process API integration tests, in one project, per [testing-patterns.md](testing-patterns.md). Always Docker-free, always fast.
- `MyApi.IntegrationTests` — integration tests that need Docker, Testcontainers, service containers, or equivalent real infrastructure dependencies. Common examples include `SqlIntegration` tests for SQL Server and `NatsIntegration` tests for NATS.io.
- `MyApi.SystemTests` — deployed system tests; different config, different auth, different lifecycle.
- Optional `MyApi.Tests.Common` — only if shared API clients, request builders, scenario helpers, or assertions justify it.

Behaviour of `dotnet test`:

- run from the solution root, it executes **every** discovered test project. Locally, that means a developer without Docker will trip over the `IntegrationTests` and `SystemTests` projects unless they filter or target a specific project.
- run with a project path (`dotnet test MyApi.Tests/MyApi.Tests.csproj`), it executes only that project. CI jobs should target project paths rather than relying on `--filter` alone — structural separation is harder to get wrong than trait conventions.
- traits (`Category=SqlIntegration`, `Category=NatsIntegration`, or a broader `Category=Integration`) remain useful for slicing within a project, but should not be the only line of defence keeping containerised tests out of the fast loop.

If the repository already has a different test-project layout that works, prefer consistency with it over forcing this default.

---

## 1. Integration tests

Purpose:

- prove application code works against real infrastructure dependencies under test control
- for database integration tests, prove data-access code works against the real database engine
- catch provider-specific failures before deployment, such as schema setup, query, constraint, transaction, broker, subject, stream, or protocol issues

Characteristics:

- run in CI
- use isolated dependency instances, normally via Docker, Testcontainers, GitHub Actions service containers, or equivalent local test infrastructure
- create fresh database state per run where practical
- slower than unit tests, but still suitable for PR validation if kept focused
- must not depend on shared DEV/UAT data

Typical coverage:

- schema creation via standard `.sql` build scripts
- Dapper or ADO.NET query execution
- stored procedures, functions, and views
- schema constraints and indexes
- transaction behaviour
- repository methods
- data import/export logic
- SQL injection protection where real provider behaviour matters
- optimistic concurrency and duplicate handling
- outbox/audit rows where applicable
- message broker publish/subscribe flows, for example NATS.io subjects, streams, consumers, and acknowledgements
- cache, object storage, search, or local emulator behaviour where the real dependency contract matters

Guidance:

- use the same dependency family as production
- for database integration tests, do not use SQLite as proof of SQL Server or PostgreSQL correctness (this matches the SQLite caveat in [testing-patterns.md](testing-patterns.md))
- prefer containerised dependencies for PR validation
- avoid long-lived shared QA databases unless the test creates and drops isolated databases or schemas
- use unique test-run identifiers for created data
- prefer dropping an entire test database over row-by-row cleanup
- for messaging tests, use test-owned subjects, streams, queues, topics, or consumers and tear them down where the platform supports it

Example command:

```powershell
dotnet test MyApi.IntegrationTests/MyApi.IntegrationTests.csproj
```

For a specific dependency slice, use a more precise category such as `SqlIntegration` or `NatsIntegration`.

### Database integration example: choosing between Docker SQL, real QA SQL, and deployed environment tests

#### Docker SQL Server in CI

Use this as the default for automated database integration tests.

Best for:

- PR validation
- schema and seed validation tests
- repository/query tests
- SQL injection tests
- deterministic database state
- repeatable test data setup
- parallel CI jobs

Advantages:

- fresh environment per run
- isolated and disposable
- does not pollute shared environments
- easy to reason about when failures occur

Limitations:

- does not prove deployed configuration
- does not validate real network/firewall/auth infrastructure
- may not cover special corporate SQL Server configuration
- local SQL Server containers can be awkward on Apple Silicon

Recommendation:

- make this the normal database-backed integration test layer
- run on GitHub Actions Ubuntu (preferred) runners. Use Windows runners only if required.
- keep it separate from the default fast guardrail suite

#### Real QA SQL Server from CI

Use this only where it provides confidence that containers cannot. Check with the human if you think we need to test against a real SQL Server while doing integration tests, this is NOT our preferred approach.

Best for:

- validating against corporate SQL Server configuration
- SQL features not represented well in containers
- permissions, collation, linked server, job, or infrastructure-specific behaviour
- DBA-owned non-production validation

Risks:

- shared test data accumulation
- cross-run interference
- fragile cleanup
- difficult parallelism
- environment drift
- failures that are hard to diagnose

Recommendation:

- avoid writing into a shared permanent QA database as the main integration strategy
- if used, create a database or schema per test run and drop it afterwards (we have no way currently to do this in our UAT/DEV environments).
- do not rely on row-level cleanup alone
- keep this layer narrower than Docker-based integration tests

### Database schema and seed data setup

Noetica repositories do not use EF Core migrations. Database schema is owned by a standard `.sql` build script that creates the full structure from scratch.

Recommended layered approach:

1. **Schema script** — the canonical `.sql` file that creates the empty database structure. Run this first in the fixture to establish a known-good schema. Use the same script that would be used to build a fresh production database so the test environment matches reality. This is stored in nub_devops repository.
2. **Seed script (optional)** — a separate `.sql` file containing reference data that many tests depend on, such as lookup tables, system configuration rows, test users, test campaigns, or other domain fixtures. Keep this minimal, stable, and clearly test-owned.
3. **Per-test data** — created through application code, repository methods, or dedicated test helpers during the test itself. This is where specific scenario data belongs. Prefer creating it through the same code paths the application uses rather than raw SQL inserts, so the test exercises real behaviour.

Guidance:

- use the full schema script by default; partial schemas break on foreign key chains and give false confidence
- keep the seed script separate from the schema script so tests can run with or without seed data
- do not put scenario-specific data in the seed script; put it in per-test setup so each test owns its state
- name seed scripts clearly, for example `test-seed.sql` or `integration-seed.sql`
- prefer running the schema script once per test run, then use per-test isolation within the database (separate schemas, unique prefixes, or transaction rollback)

---

### SQL injection and security-sensitive database tests

SQL injection protection should be tested at more than one level. Fast guardrail-style structural checks belong in unit tests per [testing-patterns.md](testing-patterns.md). Database integration tests are the provider-specific integration case:

- dangerous-looking input can be stored, searched, or rejected safely as appropriate
- the real database provider handles parameters as expected
- command batching, escaping, and provider-specific behaviour do not undermine the protection
- security-sensitive queries return only authorised data

Guidance:

- do not use SQLite as proof of SQL Server injection safety
- test against the real database provider where database semantics matter
- prefer tests that prove user input is passed as SQL parameters instead of concatenated into command text
- include at least a small set of realistic malicious-looking inputs for important endpoints

Example malicious-looking input:

```text
Robert'); DROP TABLE Users;--
```

### Cross-platform guidance

The fast unit and in-process API tests defined in [testing-patterns.md](testing-patterns.md) must remain cross-platform and Docker-free. SQL Server container tests have different constraints:

- run in CI on Linux runners (`ubuntu-latest`)
- use SQL Server Linux container images
- on Windows developer machines, use Docker Desktop with Linux containers
- on Apple Silicon Macs, do not assume SQL Server containers will run reliably
- allow developers to run fast tests locally and rely on CI for SQL Server container validation where necessary

Do not make local SQL Server Docker support mandatory for every developer or coding agent.

### GitHub Actions example for SQL Server integration tests

Keep the main workflow guidance here and put copy-paste YAML in [examples/sql-server-integration-github-actions.md](examples/sql-server-integration-github-actions.md).

Guidance:

- pin action versions according to repository policy
- never commit real passwords; the SQL Server password above is a CI-only placeholder
- prefer generated or per-run database names
- publish test results and useful logs
- avoid leaking connection strings or secrets in diagnostic output

Use GitHub Actions service containers for a small number of dependencies (SQL Server, PostgreSQL, Redis, Azurite). Move to Docker Compose only when the dependency graph genuinely justifies it.

If SQL Server image pull time is a bottleneck, use the cached-image variant in the reference file. GitHub Actions creates service containers before workflow steps run, so `actions/cache` cannot warm the image used by a `services:` block; image caching requires a step-managed container.

---

## 2. Deployed system tests

Purpose:

- prove the deployed API or service works in a real non-production environment

Characteristics:

- run after deployment to DEV, UAT, or another controlled environment
- call the deployed API over real HTTPS
- use real environment configuration
- use real or sandbox authentication
- may exercise real networking, TLS, firewalls, service discovery, message bus, and downstream service wiring
- slower and less isolated than integration tests
- best used as deployment or release confidence gates
- can also be used against live customers (smoke tests only) to show that production is running correctly

Typical coverage:

- deployed API responds
- health checks are meaningful
- authentication and authorisation are wired correctly
- TLS/certificates work
- firewall and routing paths work
- app settings and secrets are correct
- database connectivity works
- message bus connectivity works
- critical happy-path API journeys work
- controlled write flows work using test-owned data
- real downstream integrations work where safe

### Standard platform endpoints

Target API shape:

- `/ping` — existing combined endpoint used by many Noetica APIs. Retain it for compatibility and use it for the first phase of deployed smoke tests.
- `/health` — general health endpoint for monitoring and human-readable diagnostics. Keep the response safe to expose through APIM and do not include secrets or sensitive dependency details.
- `/live` — liveness endpoint for ACA/Kubernetes probes. It should answer whether the process is running and should avoid deep dependency checks that could cause unnecessary restarts.
- `/ready` — readiness endpoint for ACA/Kubernetes probes. It should answer whether the service is ready to receive traffic, including critical startup/configuration checks and any dependency checks required before routing traffic.
- `/version` — deployed build/version endpoint, including enough information to confirm the expected build is deployed without exposing secrets.

Rollout guidance:

- this document records the target standard; implementation and APIM exposure should be tracked with Jira cards because rollout requires API and gateway changes
- do not remove or break existing `ping` endpoints while adding the standard endpoints
- Phase 1 deployed system tests should rely on `ping`, because the new endpoints may not yet be exposed through APIM
- once `/health`, `/live`, `/ready`, and `/version` are implemented and exposed, add system tests for them and move the smoke gate from `ping` to the standard endpoints

Guidance:

- do not use deployed system tests as the only branch validation mechanism
- prefer black-box assertions through the API rather than direct database inspection
- avoid destructive or irreversible side effects
- use dedicated automation identities, tenants, queues, topics, or sandbox integrations
- record a correlation id or test-run id on data created by tests
- keep smoke tests small enough to run after every deployment
- run broader system verification manually, on schedule, or as part of release promotion once stable

Example command:

```powershell
dotnet test --filter "Category=System"
```

### Authentication: aligning with the E2E auth model

Deployed system tests need real credentials to obtain an identity token and access token for the deployed API. Reuse the automation identity and secret-management approach already defined for E2E in [e2e-testing-guidance.md](e2e-testing-guidance.md), but do not rely on browser session state or cached Playwright auth files for API system tests.

Defaults:

- use `zautotest001@noetica.com` (or another dedicated automation identity) rather than personal accounts
- if MFA is required, automate it in a supported way using the same TOTP seed used by E2E
- use Azure Key Vault as the source of truth for `Password` and `TotpSecret`
- in CI, use GitHub Actions OIDC federation to Azure to read those secrets at runtime; do not duplicate them into GitHub environment secrets
- locally, developers fetch the same secrets from Key Vault using their Entra identity (`az login`) via a small bootstrap script that writes to `dotnet user-secrets`, the macOS keychain, or an ignored local config file
- never commit passwords, tokens, TOTP seeds, cookies, or cached auth state to source control
- never share passwords or TOTP seeds with Copilot

#### Obtaining a JWT for API system tests

Use a headless authentication helper that signs in against the configured identity provider and returns the tokens needed by the API client. The deployed system does not need to expose its own OAuth token endpoint for this; the test harness should authenticate against the same identity platform used by the product.

Required platform profiles:

1. **Contoso.** Authenticate through the Azure AD B2C authority, user flow, or custom policy used by Contoso, federated to Entra. The test configuration must provide the B2C authority, policy, client id, scopes, automation username, password, and TOTP seed.
2. **Fabrikam.** Authenticate directly against the Microsoft Entra authority used by Fabrikam. The test configuration must provide the tenant, authority, client id, scopes, automation username, password, and TOTP seed.

Guidance:

- generate TOTP codes programmatically from the Key Vault-backed seed when MFA is required
- cache tokens only in memory for the lifetime of the test run, and refresh or reacquire them on expiry
- attach the access token via the `Authorization` header on the API `HttpClient`
- keep platform-specific auth details in configuration, not scattered through tests
- fail early if the configured auth profile cannot produce a token; do not fall back to cached browser state in CI

#### Shared configuration contract

Use a small auth-profile shape so the same test runner can support Contoso and Fabrikam without changing test code:

```json
{
  "AppSettings": {
    "BaseUrl": "<deployed API URL>",
    "EnvironmentName": "DEV",
    "TestRunId": "<generated per run>",
    "Auth": {
      "Platform": "ContosoB2C|FabrikamEntra",
      "Authority": "<B2C or Entra authority>",
      "TenantId": "<tenant id>",
      "ClientId": "<test client app id>",
      "Scopes": "<space-delimited API scopes>",
      "B2CPolicy": "<Contoso only>",
      "Username": "zautotest001@noetica.com",
      "Password": "<from Key Vault>",
      "TotpSecret": "<from Key Vault>"
    }
  }
}
```

### Test data strategy

Use explicit ownership for all data created by automated tests.

- use a unique test-run id, e.g. `systest-20260430-153012-githubrun12345`
- prefix names with a recognisable automation prefix such as `systest-` or `e2e-auto-`
- keep test users, tenants, and workspaces separate where possible
- prefer creating required data through supported APIs or setup helpers
- clean up at the end where safe, and design tests to tolerate previous failed cleanup
- prefer API-level cleanup or deactivation over direct database deletion
- make cleanup idempotent
- ensure failed tests leave enough information to diagnose the failure

### Side-effect strategy

Not every real-world side effect should be real in automated tests.

Usually acceptable:

- creating test-owned records
- writing to isolated test tenants
- writing to test queues or topics
- calling sandbox APIs
- sending email to captured test inboxes
- writing audit records in non-production

Risky:

- sending real customer emails or SMS
- payment calls
- irreversible exports
- real customer-affecting downstream API calls
- shared production-like queues consumed by uncontrolled services
- scheduled jobs that pick up test data unexpectedly

Guidance:

- use sandbox downstream services where available
- use test tenants and automation identities
- use dry-run modes where the product supports them
- use dedicated test queues/topics/subscriptions
- include correlation ids and idempotency keys
- prefer "create then deactivate" over destructive delete when the product has audit obligations
- do not enable dangerous side-effect tests automatically until the environment is deliberately designed for them

---

## Recommended pipeline shape

### Pull request validation

Decide whether a branch is safe to merge.

```text
Pull Request
  build
  unit + guardrail tests          (per testing-patterns.md)
  in-process API integration pack (per testing-patterns.md)
  containerised integration tests (this document; for example Docker SQL)
```

Keep PR validation deterministic. Do not require deployed DEV or UAT environments for normal PR validation. Keep write-heavy or slow suites out of the first PR gate until they have proved stable.

### Main branch / post-merge validation

Prove the merged branch still builds, tests, packages, and deploys.

```text
Main branch
  build
  unit + in-process API tests
  integration tests               (for example SQL-backed tests)
  package artifact
  deploy to DEV
  run deployed smoke tests
```

### DEV deployment validation

Prove the deployed application is alive and basically usable.

```text
Deploy to DEV
  API ping / existing smoke endpoint
  auth check (token acquisition succeeds)
  critical smoke journeys
  controlled test-data cleanup
```

Use the existing `ping` endpoint for Phase 1 deployment validation. Move to `/health`, `/live`, `/ready`, and `/version` once those endpoints are implemented and exposed through APIM.

### UAT / release validation

Provide higher confidence before release or stakeholder testing.

```text
Promote to UAT
  smoke tests
  selected high-value system tests
  optional broader verification
```

Selected here means a deliberate release-gate subset, not a random sample. Run all system tests at UAT promotion if the suite is fast, reliable, and safe enough. If the suite is broader than that, choose the release-gate subset by risk and confidence value.

Good selection criteria:

- authentication and token acquisition for the target platform
- health, version, and read-only checks that prove the deployed API is reachable
- one or two critical business journeys that would block release if broken
- areas changed by the release
- integrations or configuration that differ between DEV and UAT
- tests with controlled side effects, isolated test data, and dependable cleanup

Keep slower, destructive, or broad regression-style system tests out of the automatic UAT promotion gate until the environment and data strategy are deliberately designed for them. Run those manually, on a schedule, or as an explicit release-hardening step.

---

## Reusing scenarios across layers

Integration and system tests will overlap. That is expected. The difference is the execution boundary, not the business scenario.

A `CreateUser` scenario may expect:

```text
POST /users returns 201 Created
GET /users/{id} returns the created user
the user has the expected email and display name
```

In-process API integration test (per [testing-patterns.md](testing-patterns.md)):

```text
xUnit
  -> WebApplicationFactory / in-process host
  -> Docker SQL Server or in-process persistence
  -> fake or controlled downstream dependencies
```

Deployed system test:

```text
xUnit API client
  -> deployed DEV/UAT API URL
  -> real authentication (JWT)
  -> deployed API
  -> configured SQL/database
  -> real or sandbox downstream dependencies
```

Guidance:

- reuse request builders, API clients, scenario helpers, and common assertions
- keep fixtures separate for in-process versus deployed execution
- avoid maintaining three completely independent suites where the same scenario can be shared
- do not hide too much behind a universal test framework
- in-process API integration tests may inspect database state directly where useful (per [testing-patterns.md](testing-patterns.md))
- deployed system tests should prefer black-box assertions through the public API

Example structure:

```text
MyApi.Tests.Common
  ApiClients/
  TestData/
  ScenarioHelpers/
  Assertions/
MyApi.Tests                    (per testing-patterns.md: unit + in-process API in one project)
MyApi.IntegrationTests         (Docker/Testcontainers fixtures, e.g. SQL Server or NATS.io)
MyApi.SystemTests              (deployed API, DEV/UAT fixtures, auth bootstrap)
```

Layer-specific assertions should stay in the layer that needs them.

Integration-only assertions:

- SQL row exists
- computed or normalised database fields are correct
- audit row was created
- outbox row was created
- transaction rollback happened
- database constraint rejected invalid state
- message was published, consumed, acknowledged, or rejected as expected
- stream, queue, topic, or subject state changed as expected

System-only assertions:

- request works through real auth
- deployed URL responds
- expected security headers are present
- correlation id is returned or logged
- downstream sandbox side effect occurred
- message reached the expected test queue or topic

---

## Test categorisation

Use clear test categories or separate projects so suites can be run independently. Recommended categories (a superset across all the testing documents):

- `Unit`
- `Guardrail`
- `ApiIntegration`
- `Integration`
- `SqlIntegration`
- `NatsIntegration`
- `System`
- `Smoke`
- `Regression`

Example xUnit trait:

```csharp
[Trait("Category", "SqlIntegration")]
public sealed class UserRepositorySqlTests
{
}
```

Standard commands:

```powershell
dotnet test --filter "Category!=Integration&Category!=SqlIntegration&Category!=NatsIntegration&Category!=System"
dotnet test MyApi.IntegrationTests/MyApi.IntegrationTests.csproj
dotnet test --filter "Category=SqlIntegration"
dotnet test --filter "Category=NatsIntegration"
dotnet test --filter "Category=System"
```

Keep categories consistent across repositories and document the standard commands in the repo README or test project README.

---

## Failure diagnostics

Automated tests should produce enough evidence to diagnose failures without rerunning immediately.

For integration tests:

- publish test results
- capture SQL schema script output for database integration tests
- capture failed request/response details where safe
- capture container logs for SQL, NATS.io, or other services
- capture broker, stream, queue, topic, or consumer diagnostics where safe
- include correlation ids

For deployed system tests:

- capture request method, URL path, status code, and correlation id
- avoid logging secrets, bearer tokens, cookies, or personal data
- capture relevant response bodies only where safe
- link to environment logs or telemetry where possible
- record test-run id in created data and logs

For CI/CD failure notification:

- post integration and system test failures to the configured Teams channel URL
- keep the Teams URL in CI/CD configuration or secrets, never in source control
- include the repository, branch, workflow run link, environment, suite/category, failing test names, and correlation or test-run id where available
- link to test results, logs, telemetry, or container diagnostics rather than pasting large logs into Teams
- avoid posting secrets, bearer tokens, cookies, passwords, TOTP seeds, connection strings, or personal data

Make failures actionable. Avoid noisy logging that hides the relevant issue. Never leak credentials or sensitive production-like data into CI logs.

---

## What to test first

For a new API/service repository, start with:

- build
- the fast test command from [testing-patterns.md](testing-patterns.md)
- one containerised integration test proving the highest-risk external dependency setup works; database integration is the usual first example
- one critical API happy path through an in-process or local test host (per [testing-patterns.md](testing-patterns.md))
- one deployed DEV smoke test after deployment, with real auth

Good early system test candidates:

- existing `ping` endpoint for Phase 1 smoke coverage
- `/health`, `/live`, `/ready`, and `/version` after implementation and APIM exposure
- authentication challenge or token validation
- one read-only endpoint
- one controlled create/read/deactivate journey

Good early integration test candidates:

- one schema build test (run the `.sql` build script against the container and verify the database is usable)
- one repository method involving real SQL
- one message publish/consume flow if messaging is the highest-risk external dependency

Do not start with:

- a large regression matrix
- complex destructive workflows
- every edge case through the deployed environment
- shared QA database tests that require fragile cleanup
- fully real downstream side effects before the environment is designed for them

---

## Delivery model

### Phase 1

- define test categories and standard commands
- ensure unit and in-process API tests run locally and in CI per [testing-patterns.md](testing-patterns.md)
- add an integration harness or Testcontainers fixture for the highest-risk external dependency, such as SQL Server or NATS.io
- add one high-value SQL-backed, broker-backed, or equivalent infrastructure-backed scenario
- use the existing `ping` endpoint for the first deployed smoke test while `/health`, `/live`, `/ready`, and `/version` are rolled out separately
- document local and CI execution

### Phase 2

- make containerised integration tests part of PR validation
- improve test data isolation
- publish useful test results and logs

### Phase 3

- add deployed DEV smoke tests after automatic deployment
- add `/health`, `/live`, `/ready`, and `/version` smoke coverage after the endpoints and APIM definitions are available
- add authentication and secret bootstrap for system tests, reusing the E2E identity and Key Vault flow
- add controlled write flows with explicit test data strategy
- introduce broader system verification only after smoke tests are reliable

### Phase 4

- expand release/UAT system coverage
- add selected downstream integration checks
- consider scheduled or manual broader verification
- revisit whether any QA SQL Server validation is needed beyond containerised tests

---

## Good outcomes to aim for

- developers and agents have one fast command (per [testing-patterns.md](testing-patterns.md)) that works without infrastructure
- PR validation catches real dependency breakage before merge via containerised integration tests; database breakage via Docker SQL integration tests is the common example
- deployed environment tests catch configuration and wiring failures after deployment
- system tests share the E2E automation identity and secret store rather than maintaining a separate one
- test data is isolated, recognisable, and cleanable
- system tests are high-signal rather than a second flaky regression suite
- integration and system tests reuse clients, builders, and scenario helpers where appropriate
- failures point clearly toward code, database, deployment, or environment problems

---

## Suggested Copilot instruction text

If you are adding or changing tests in this repository, preserve the distinction between the four layers documented across the context pack:

- unit tests and in-process API integration tests follow [testing-patterns.md](testing-patterns.md);
- integration tests and deployed system tests follow this document;
- browser E2E tests follow [e2e-testing-guidance.md](e2e-testing-guidance.md).

Do not put provider-specific external dependency behaviour in the in-process suite from `testing-patterns.md`; put it in integration tests and run those against controlled real dependencies using Docker, Testcontainers, service containers, or equivalent CI infrastructure. Database integration tests are the common example: use `SqlIntegration` tests against the real database engine using Docker SQL Server or Testcontainers in CI. For message brokers such as NATS.io, use a similarly isolated broker instance with test-owned subjects, streams, consumers, or queues. Put deployed-environment checks in `System` tests that call the configured DEV or UAT API URL using dedicated automation credentials and safe test data. Reuse the E2E automation identity (e.g. `zautotest001@noetica.com`), the same Azure Key Vault secrets, and the same OIDC-based GitHub Actions flow rather than inventing a parallel auth and secret model.

Reuse request builders, API clients, scenario helpers, and common assertions where this keeps tests readable, but keep fixtures separate. Integration tests may inspect database state directly where useful. System tests should prefer black-box assertions through the public API and should validate deployment, authentication, configuration, networking, and real service wiring. For Phase 1 deployed smoke tests, use the existing `ping` endpoint until `/health`, `/live`, `/ready`, and `/version` are implemented and exposed through APIM; keep `ping` for compatibility after adding those standard endpoints. Do not use a shared QA database with accumulating test data unless each run creates and tears down isolated state. Keep secrets out of source control and CI logs.
