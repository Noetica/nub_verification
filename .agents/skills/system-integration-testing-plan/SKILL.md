---
name: system-integration-testing-plan
description: Plan out-of-process integration tests and deployed system tests — real SQL, Testcontainers, NATS, or a deployed environment. Use when asked to plan integration or system testing.
---

# System and Integration Test Planner

Create a structured plan for adding **integration tests** and/or **deployed system tests** to this repository.

Do not generate test code in this step.

Create or update the plan as a Markdown artifact at:

`plans/automated-testing/<Plan ID>.md`

Follow the canonical guidance in:
`docs/context-pack/system-and-integration-testing-guidance.md`

Cross-reference, but do not duplicate, guidance from:

- `docs/context-pack/testing-patterns.md` — owns unit tests and in-process API integration tests
- `docs/context-pack/e2e-testing-guidance.md` — owns browser E2E tests, automation identity, and the Azure Key Vault secret flow that deployed system tests reuse

If `docs/context-pack/system-and-integration-testing-guidance.md` doesn't exist, stop and tell the human.

Treat that document as the source of truth for: out-of-process integration tests (for example SQL/database integration with Docker SQL Server / Testcontainers, NATS.io, or other real infrastructure dependencies), deployed system tests (DEV/UAT, JWT acquisition, secrets), test categorisation (`Integration`, dependency-specific categories such as `SqlIntegration` or `NatsIntegration`, `System`, `Smoke`), test data strategy, side-effect strategy, and pipeline shape.

This prompt is **not** for unit tests or in-process API integration tests. If the work belongs in `MyApi.Tests` (unit + in-process API), use `automated-testing-plan` instead.

If the repository already contains test projects, follow their conventions first. Otherwise, prefer the default split documented in `system-and-integration-testing-guidance.md`:

- `MyApi.IntegrationTests` for out-of-process integration tests such as `SqlIntegration` or `NatsIntegration` tests
- `MyApi.SystemTests` for deployed system tests

Create `plans/automated-testing/` if it does not already exist.

---

# Read First

Review the following context before planning:

- docs/context-pack/overview.md
- docs/context-pack/db-schema.md
- docs/context-pack/repo-map.compact.md
- docs/context-pack/system-and-integration-testing-guidance.md
- docs/context-pack/testing-patterns.md (for layer boundaries only)
- docs/context-pack/e2e-testing-guidance.md (for the auth/secrets contract if planning system tests)

Only read:

`docs/context-pack/repo-map.deep.md`

if the compact map is insufficient.

Also inspect:

- existing test projects and their categorisation
- solution structure
- external dependency boundaries (database access, messaging, cache, storage, search, or other real infrastructure dependencies)
- deployment configuration for DEV/UAT
- existing CI workflows under `.github/workflows/`
- any existing Playwright/E2E auth bootstrap that a system test could reuse

---

# Planning Goals

The goal is to introduce **high-value integration tests and/or deployed system tests** that:

- answer a clear confidence question (provider behaviour, deployed wiring, real auth, real configuration)
- avoid duplicating coverage that already lives in the unit / in-process API tests
- follow the layer boundaries defined across the testing documents
- are incremental, deterministic where possible, and easy to operate

Focus on **deployment risk, external-dependency risk, data-layer risk, and configuration risk**, not code coverage.

---

# Planning Constraints

When planning:

- propose only the test layers covered by `system-and-integration-testing-guidance.md` (out-of-process integration tests and `System` tests)
- if the behaviour can be validated in-process without a container, plan it under `automated-testing-plan` instead
- prefer Docker, Testcontainers, service containers, or equivalent isolated infrastructure over shared QA dependencies for integration tests
- for `System` tests, reuse the E2E automation identity (e.g. `zautotest001@noetica.com`) and the Azure Key Vault + OIDC secret flow rather than introducing a parallel auth model
- prefer black-box assertions through the public API for `System` tests; reserve direct database inspection for `SqlIntegration` tests and direct broker/cache/storage inspection for the matching integration layer
- keep the first system test pack small (Phase 1: existing `ping` endpoint plus auth/token acquisition; once `/health`, `/live`, `/ready`, and `/version` are exposed through APIM, add coverage for those and one controlled write/read/deactivate journey)
- keep the first integration pack small (for database integration: one schema build test, one repository method involving real SQL, plus any provider-specific behaviour the service depends on; for broker integration: one publish/consume flow plus any protocol-specific behaviour the service depends on)
- do not require Docker for the fast `MyApi.Tests` command from `testing-patterns.md`
- flag any new infrastructure (Key Vault entries, automation identities, GitHub Actions OIDC federation, sandbox downstream services) as risks/prerequisites rather than normal plan steps

---

# Output Sections (Required)

## 1. Plan ID

Start with:

```
Plan ID: <UTC timestamp in YYYY-MM-DDTHH-mmZ>-<scope-kebab-case>
```

Example:

```
Plan ID: 2026-04-30T14-30Z-orders-sql-and-system-tests
```

Use the `Plan ID` value as the filename stem and save the plan to:

```
plans/automated-testing/<Plan ID>.md
```

---

## 2. Repository Summary

Brief summary of:

- key projects
- data access approach (Dapper, ADO.NET, stored procedures, mixed); Noetica repositories use a standard `.sql` build script for schema, not EF Core migrations
- deployed environments and how they are reached
- which identity platform applies — Contoso (Azure AD B2C federated to Entra) or Fabrikam (Microsoft Entra direct) — and whether a Playwright-based login already exists for E2E whose Key Vault secrets and automation identity can be reused
- whether the standard platform endpoints (`/ping`, `/health`, `/live`, `/ready`, `/version`) are implemented and exposed through APIM, or whether Phase 1 smoke tests must rely on the existing `ping` endpoint only

---

## 3. Existing Test Coverage

Identify:

- existing test projects and their categories
- existing `Integration`, dependency-specific integration, or `System` coverage (if any)
- whether the fast `MyApi.Tests` suite already exists per `testing-patterns.md`
- whether E2E tests already exist per `e2e-testing-guidance.md` and whether their auth bootstrap can be reused
- major gaps in deployed-environment, data-layer, messaging, or other external-dependency confidence

---

## 4. Prioritised Targets

List the targets that should receive integration and/or `System` tests first.

For each include:

- target (endpoint, repository method, schema or seed script, broker subject/stream, deployed journey)
- which layer (`Integration`, a dependency-specific integration category such as `SqlIntegration` or `NatsIntegration`, or `System`) and why that is the correct layer
- risk/business impact (deployment risk, data corruption risk, security)
- why a unit or in-process API test would not give the same confidence

---

## 5. Detailed Test Strategy Per Target

For each target describe:

### Test Layer

Specify exactly one:

- `Integration` test, preferably with a dependency-specific category such as `SqlIntegration` or `NatsIntegration`
- `System` test (deployed)

Explain why this is the correct layer per `system-and-integration-testing-guidance.md`.

### Responsibilities

What the target does and what confidence question this test answers.

### Dependencies

For integration tests: target dependency and setup needs, such as database engine, the canonical `.sql` schema build script, optional `.sql` seed script, stored procedures, broker subjects/streams/consumers, cache instances, storage containers, or search indexes.

For `System` tests: deployed URL, identity platform (Contoso B2C or Fabrikam Entra), downstream services (real / sandbox / fake), message bus, etc.

### Fixture Strategy

For integration tests:

- container, Testcontainers, service container, or equivalent fixture
- per-run database/schema, subject, stream, queue, topic, consumer, bucket, or index name
- setup strategy: prefer running the canonical `.sql` schema build script once per test run, then optionally apply a separate `.sql` seed script for stable reference data; create scenario-specific data through application code paths during the test
- cleanup strategy, such as dropping a database/schema or deleting test-owned broker/cache/storage resources
- for SQL Server in GitHub Actions, reference the YAML in `docs/context-pack/examples/sql-server-integration-github-actions.md` rather than inlining a copy in the plan

For `System` tests:

- environment (DEV / UAT)
- identity platform (`ContosoB2C` or `FabrikamEntra`) and the headless authentication helper that signs in against that platform and returns access tokens; do not plan to reuse Playwright cached state for API system tests
- shared config keys consumed (`AppSettings:BaseUrl`, `EnvironmentName`, `TestRunId`, and the `Auth` profile shape: `Platform`, `Authority`, `TenantId`, `ClientId`, `Scopes`, `B2CPolicy`, `Username`, `Password`, `TotpSecret`)
- TOTP code generation from the Key Vault-backed seed when MFA is required
- API client and request builder reuse with other layers

### Scenarios

Include:

- happy path
- realistic failure or rejection cases
- provider-specific behaviour (for integration tests)
- auth, TLS, headers, correlation id (for `System`)
- side-effect boundaries (test tenants, sandbox queues, dry-run modes)

### Test Data

- naming prefix (`itest-`, `systest-`)
- unique per-run identifier
- creation strategy (API setup vs direct DB seed)
- cleanup or deactivation strategy

### Categorisation

Specify the xUnit `[Trait("Category", "...")]` value and the `dotnet test --filter` command that will run the suite.

---

## 6. Infrastructure and Secret Prerequisites

List anything that must exist outside the test code before the plan can run:

- Azure Key Vault secrets (e.g. `zautotest001-password`, `zautotest001-totp-seed`)
- GitHub Actions OIDC federation to Azure
- Automation identities, test tenants, sandbox accounts on downstream services
- Identity platform configuration for the target (Contoso B2C authority/policy/client id/scopes, or Fabrikam Entra tenant/authority/client id/scopes)
- Dedicated test queues/topics/subscriptions/subjects/streams/consumers
- DEV/UAT base URLs and connectivity
- Standard platform endpoints (`/ping`, `/health`, `/live`, `/ready`, `/version`) — note which are exposed through APIM today and which are blocked on a Jira-tracked rollout
- Docker image availability on the chosen runner, such as SQL Server or NATS.io images
- Teams channel URL for CI/CD failure notifications (held in CI/CD configuration or secrets, never in source control)

If any prerequisite does not exist yet, mark it as a blocker and propose who owns it.

---

## 7. Incremental Execution Steps

Provide an ordered list of steps. Each step must be small and self-contained. Use markdown checkboxes.

Example:

```
- [ ] Add MyApi.IntegrationTests project with integration trait helpers
- [ ] Add Testcontainers fixture creating a per-run database or broker namespace
- [ ] Add schema build smoke test that runs the canonical `.sql` script, or broker connectivity smoke test
- [ ] Add UserRepository SqlIntegration test for the create+read path, or a NatsIntegration publish/consume test for the critical subject
- [ ] Add MyApi.SystemTests project with shared config binding (`BaseUrl`, `EnvironmentName`, `TestRunId`, `Auth` profile)
- [ ] Add headless IdP auth helper for the target platform (Contoso B2C or Fabrikam Entra) that reads secrets via OIDC -> Key Vault and generates TOTP codes from the seed
- [ ] Add Phase 1 deployed smoke test against the existing `ping` endpoint
- [ ] Add CI job sql-integration-tests using a SQL Server service container (per `docs/context-pack/examples/sql-server-integration-github-actions.md`)
- [ ] Add CI job deployed-system-smoke gated on successful DEV deployment
- [ ] Wire integration and system test failures to the configured Teams channel notification
```

Step 1 must be fully executable without additional planning.

---

## 8. Risks and Assumptions

Document uncertainties. Mark unknown items as `ASSUMED`.

Examples:

- whether the headless IdP auth helper for the target platform (Contoso B2C or Fabrikam Entra) can complete sign-in non-interactively with TOTP from Key Vault
- whether `/health`, `/live`, `/ready`, and `/version` are exposed through APIM yet, or whether Phase 1 smoke coverage must rely solely on the existing `ping` endpoint
- whether DEV/UAT downstream integrations are safe to call from automation
- whether SQL Server, NATS.io, or other dependency containers run reliably on the chosen developer platforms
- whether the existing CI runner has Azure OIDC federation configured
- whether the Teams channel URL for CI/CD failure notifications is already provisioned

If a target appears to require true browser-level E2E coverage, mark it as out of scope here and refer to `e2e-testing-guidance.md`.

If a target appears to belong in the unit / in-process API layer, mark it as out of scope here and refer to `automated-testing-plan`.

---

# Constraints

The plan must:

- follow `docs/context-pack/system-and-integration-testing-guidance.md`
- preserve the layer boundaries defined across the three testing documents
- be incremental
- keep production code changes minimal
- never commit secrets, tokens, or cached auth state

Save the plan artifact under `plans/automated-testing/` and report the saved path in the response.
