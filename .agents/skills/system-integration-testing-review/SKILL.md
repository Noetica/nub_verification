---
name: system-integration-testing-review
description: Review newly added or modified out-of-process integration and deployed system tests. Use when asked to review integration or system tests.
---

# System and Integration Test Review

Review the **integration** and/or **deployed `System`** tests that were recently added or modified.

Follow the canonical guidance in:

`docs/context-pack/system-and-integration-testing-guidance.md`

Cross-reference, but do not duplicate, guidance from:

- `docs/context-pack/testing-patterns.md` — owns unit and in-process API integration tests
- `docs/context-pack/e2e-testing-guidance.md` — owns the automation identity and Key Vault secret flow that deployed system tests reuse

The goal is to improve **test quality, reliability, and maintainability** for the integration and deployed-system layers.

Do not add new test scenarios unless they are critical omissions.

Avoid large refactors.

If `docs/context-pack/system-and-integration-testing-guidance.md` doesn't exist, stop and tell the human.

This prompt is **not** for unit or in-process API tests. If the changed tests live in `MyApi.Tests` (unit + in-process API), use `automated-testing-review` instead.

Review the plan artifact that matches the work from `plans/automated-testing/`. If no plan artifact exists there, stop and tell the human to run the planner first. If multiple plan artifacts exist and the human has not named one, use the most recently modified file.

---

# Inputs

Review:

- newly created or modified integration test files, including dependency-specific categories such as `SqlIntegration` or `NatsIntegration`
- newly created or modified deployed `System` test files
- related fixtures (Testcontainers, service containers, dependency fixtures, `WebApplicationFactory`-style hosts only where they remain in this layer's scope, deployed environment fixtures)
- headless IdP auth helpers for the supported identity platforms (Contoso Azure AD B2C federated to Entra; Fabrikam Microsoft Entra direct), including TOTP generation from Key Vault-backed seeds
- shared API clients, request builders, scenario helpers, assertions used by these tests
- minimal production code changes introduced for testing
- CI workflow changes related to service containers, Testcontainers, deployed-environment runs, and Teams failure notifications

Also review the selected automated-testing plan artifact.

---

# Review Goals

Verify that tests:

- live in the correct layer per `system-and-integration-testing-guidance.md`
- answer a real confidence question that lower layers cannot answer
- remain deterministic where possible (and explicitly tolerate environment realities where not)
- avoid leaking secrets or polluting shared environments
- are readable and maintainable
- reuse cross-layer helpers without blurring layer boundaries

Focus on **layer fit, isolation, and deployment safety**, not formatting.

---

# Review Checklist

## 1. Layer Selection

Flag cases where:

- an integration test could have been a unit or in-process API integration test (and would be cheaper there)
- a `System` test is asserting pure logic, mapping, validation, or routing that should live in `MyApi.Tests`
- a `System` test duplicates an integration test without adding deployed-environment confidence
- the boundary between in-process API integration tests (in `MyApi.Tests`) and out-of-process integration tests is unclear or both layers are doing the same job

---

## 2. Test Project Placement

Flag cases where:

- containerised tests sit inside the fast `MyApi.Tests` project, putting Docker on the fast loop
- deployed system tests sit inside `MyApi.IntegrationTests` and would be picked up by integration CI jobs
- a single test project mixes layers in a way that prevents `dotnet test <project>` from being a clean filter

Confirm the chosen layout matches the repository's existing convention or the default split documented in `system-and-integration-testing-guidance.md`.

---

## 3. Categorisation

Flag cases where:

- the `[Trait("Category", "...")]` value is missing or wrong
- a test is reachable by the fast filter from `testing-patterns.md` but actually requires Docker, Testcontainers, service containers, or a deployed environment
- the documented `dotnet test --filter` commands no longer match what is in the repo

---

## 4. Integration Fixtures

For integration tests, flag cases where:

- SQLite is being used as a stand-in for SQL Server in `SqlIntegration` tests
- a shared QA database, broker, cache, or storage dependency is being written to without per-run isolation
- the fixture relies on row-level cleanup that fails open
- the canonical `.sql` schema build script is not used to set up the database, or partial schema fragments are being applied instead
- seed data is mixed into the schema script, or scenario-specific data is being put in the seed script instead of being created per-test
- EF Core migrations or similar ORM tooling are being used to set up schema in a repository that does not use them in production
- schema or seed scripts are applied inconsistently across tests
- the same database name is reused across parallel runs without isolation
- the fixture silently swallows container start-up errors
- NATS.io subjects, streams, consumers, queues, or similar broker resources are shared across runs without isolation
- a SQL Server GitHub Actions workflow inlines YAML that should reference `docs/context-pack/examples/sql-server-integration-github-actions.md` instead
- the SQL Server container password env var is set as `SA_PASSWORD` instead of the current `MSSQL_SA_PASSWORD`

Confirm provider-specific behaviour is actually being exercised; otherwise the test probably belongs in the in-process API integration layer per `testing-patterns.md`.

---

## 5. Deployed System Test Fixtures

For `System` tests, flag cases where:

- a custom auth model is implemented instead of reusing the E2E identity (e.g. `zautotest001@noetica.com`) and Key Vault flow from `e2e-testing-guidance.md`
- the headless IdP auth helper does not match the target platform: Contoso must use the Azure AD B2C authority/policy/client id federated to Entra; Fabrikam must use the Microsoft Entra authority/tenant/client id directly
- API system tests reuse Playwright cached browser state instead of authenticating headlessly against the identity platform
- the bearer token is attached per-request instead of via the `HttpClient` `Authorization` header
- TOTP codes are hard-coded, captured manually, or generated from a seed that is not sourced from Key Vault
- the test reads secrets from sources other than the documented Key Vault + OIDC or local developer bootstrap
- environment configuration is hard-coded rather than bound from the shared config contract (`AppSettings:BaseUrl`, `EnvironmentName`, `TestRunId`, and the `Auth` profile shape: `Platform`, `Authority`, `TenantId`, `ClientId`, `Scopes`, `B2CPolicy`, `Username`, `Password`, `TotpSecret`)
- a Phase 1 deployed smoke test asserts against `/health`, `/live`, `/ready`, or `/version` before those endpoints are exposed through APIM, instead of using the existing `ping` endpoint
- the test inspects the deployed database directly when a black-box API assertion would have been sufficient
- a destructive operation runs without a controlled test-data strategy

---

## 6. Test Data and Side-Effect Strategy

Flag cases where:

- created data lacks a recognisable automation prefix (`itest-`, `systest-`, `e2e-auto-`)
- created data lacks a unique per-run identifier
- cleanup is not idempotent or assumes previous runs cleaned up perfectly
- a `System` test triggers risky real-world side effects (real customer email/SMS, payment calls, irreversible exports, shared production-like queues) without explicit safeguards
- a `System` test relies on globally mutable records that may be modified by other automation

---

## 7. Determinism and Scope Boundaries

Flag tests that:

- are likely to be flaky for non-business reasons (network jitter, container start-up timing, eventual consistency without a wait helper)
- depend on external clocks, real time-of-day windows, or scheduler behaviour without explicit handling
- assume an environment state that is not guaranteed by the fixture or a setup step
- mix integration and `System` concerns in a single test method

---

## 8. Reuse Across Layers

Flag cases where:

- request builders, API clients, scenario helpers, or assertions are duplicated across the in-process, integration, and system layers when sharing them would be straightforward
- shared abstractions are over-generalised in a way that hides important layer-specific behaviour
- an integration test reaches into in-process API integration helpers, or vice versa, in a way that breaks the layer boundary

---

## 9. Secrets and CI Hygiene

Flag any:

- committed passwords, tokens, TOTP seeds, cached auth state, or cookies
- secrets logged or echoed in CI output or in Teams failure notifications
- connection strings with real credentials in workflow files or test config
- workflows that store secrets in places other than the documented Key Vault + OIDC flow (allow GitHub secrets only as a short-lived fallback if explicitly justified)
- Teams channel URLs committed to source control rather than held in CI/CD configuration or secrets
- Teams failure notification payloads that include bearer tokens, passwords, TOTP seeds, connection strings, personal data, or large raw logs instead of links to test results, logs, or telemetry
- `WriteIndented` test output that may include sensitive payloads

---

## 10. Production Code Changes

Confirm production edits follow the minimal-production-change guidance in `docs/context-pack/testing-patterns.md`. Flag:

- changes unrelated to making an integration or deployed-system test pass
- broad refactors disguised as test enablement
- changes to deployment configuration that go beyond the explicit plan step

---

# Optional Improvements

Suggest improvements such as:

- moving a test into the right layer
- replacing a custom auth helper with the shared E2E bootstrap
- isolating a database, broker, cache, or storage fixture better
- tightening test-data prefixes or per-run identifiers
- splitting a test that mixes integration and `System` concerns

Only recommend changes that significantly improve clarity, maintainability, or safety.

---

# Output Format

## Plan Reviewed

Plan path and Plan ID.

## Summary

Brief overall assessment of the test quality. One of:

- Good
- Acceptable with improvements
- Needs revision

## Findings

List issues grouped by category:

- Layer selection
- Project placement
- Categorisation
- Integration fixtures (SQL, broker, cache, storage)
- System fixtures and headless IdP auth
- Standard platform endpoints and Phase 1 `ping` rollout
- Test data and side effects
- Determinism
- Cross-layer reuse
- Secrets / CI hygiene (including Teams notifications)
- Production code changes

Each issue should include:

- file
- short explanation
- suggested fix

## Suggested Improvements

Optional improvements that would strengthen the suite. Keep them small and practical.

## Verdict

One of:

- ✅ Tests are ready
- ⚠ Improvements recommended
- ❌ Significant issues detected
