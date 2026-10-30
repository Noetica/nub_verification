---
name: system-integration-testing-autopilot
description: Execute the next bounded batch from the current system/integration testing plan. Use when asked to continue or execute that plan.
---

# System and Integration Test Executor (Autopilot Batch)

Use this prompt as the **default executor** when working through an integration or `System` testing plan with lower human coordination overhead: it completes one bounded vertical slice per run instead of requiring review after every single plan step.

Implement a **bounded, coherent batch** from the latest automated-testing plan whose scope is out-of-process integration or deployed system tests.

Plan artifacts live in:

`plans/automated-testing/<Plan ID>.md`

Follow the canonical guidance in:

`docs/context-pack/system-and-integration-testing-guidance.md`

Cross-reference, but do not duplicate, guidance from:

- `docs/context-pack/testing-patterns.md` — owns unit and in-process API integration tests
- `docs/context-pack/e2e-testing-guidance.md` — owns the automation identity and Key Vault secret flow that deployed system tests reuse

If `docs/context-pack/system-and-integration-testing-guidance.md` doesn't exist, stop and tell the human.

This prompt is **not** for unit or in-process API integration tests. If the next plan steps are for the fast `MyApi.Tests` project, use `automated-testing-autopilot` instead.

---

# Execution Model

This prompt is intended for low-supervision autonomous runs (Claude Code, Copilot CLI autopilot).

The goal is not "exactly one step" — it is the **next small vertical slice, finished**: typically 1 to 3 consecutive incomplete plan steps that belong to the same target (one repository, one endpoint, one deployed journey) and the same test layer (`Integration`, a dependency-specific category such as `SqlIntegration` or `NatsIntegration`, or `System` — never a mix), implemented and validated in one run. A fixture plus the test that needs it is one slice; a SQL fixture combined with a deployed auth bootstrap is not, and neither is mixing a Contoso B2C auth helper change with a Fabrikam Entra one.

Optimize for one finished slice per run. A fixture-only or helper-only change is **not** a finished slice unless a real blocker prevents adding the dependent test immediately. Do not execute unrelated plan steps just because they are available.

---

# Workflow

1. Locate the **latest automated-testing plan artifact** (not the prompt template) in `plans/automated-testing/`. If none exists there, stop and tell the human to run `system-integration-testing-plan` first. If multiple exist and the human has not named one, choose the most recently modified plan whose scope includes integration or `System` work.

2. Read the plan and extract its **Plan ID**. Confirm the next incomplete step is an integration or `System` step — if it is a unit / in-process API step, stop and direct the human to `automated-testing-autopilot`.

3. Select the next 1 to 3 compatible incomplete steps that form one coherent slice within a single layer. State briefly which steps you selected, which layer they are in, why they belong together, and what "done" looks like for the batch — then continue straight into implementation; this status message is not a review checkpoint.

4. Implement the slice **red → green → refactor** where realistic. An integration test should fail because the dependency-facing behaviour under test is genuinely missing or wrong, not because the fixture is misconfigured; a `System` test should fail because the deployed behaviour is missing, not because the environment is unreachable.

5. Run tests using the appropriate project path or filter:

   ```
   dotnet test MyApi.IntegrationTests/MyApi.IntegrationTests.csproj
   dotnet test --filter "Category=Integration"
   dotnet test --filter "Category=SqlIntegration"
   dotnet test --filter "Category=NatsIntegration"
   dotnet test --filter "Category=System"
   ```

   For `System` tests, ensure the required environment variables and secrets are in place (per `system-and-integration-testing-guidance.md`). If the secret bootstrap or headless IdP auth helper is not yet wired up, treat that as a blocker rather than committing fallback values or reusing browser cached state.

6. Iterate up to 3 cycles of run → fix the smallest issue → re-run. If still failing after 3 attempts, stop and report the blocker — distinguishing clearly between a code/test failure and an environment/config/auth failure.

7. Self-review the result against `docs/context-pack/system-and-integration-testing-guidance.md`, the selected plan step wording, and the repository's existing test-support patterns. Fix any clear in-scope issue in the same run.

8. Update the plan file: change each completed step from `- [ ]` to `- [x]`, subject to the evidence bar below. Only the steps you selected for this batch — never unrelated future steps, and never a fixture or bootstrap step whose output the finished slice does not actually exercise.

9. Stop the batch when the next incomplete step belongs to a different layer or target, the change would require infrastructure that is not already provisioned (Key Vault secrets, OIDC federation, sandbox accounts, dedicated test queues, identity-platform app registration, Teams channel URL for failure notification, or `/health`/`/live`/`/ready`/`/version` exposed through APIM when the test depends on them), tests are still failing after 3 fix cycles, the remaining work needs a design decision from the human, or the production-edit bounds below would be exceeded.

---

# Evidence Discipline

Before marking a plan step complete or reporting the run done, audit each claim against something you can point to from this session: the file on disk (check the working tree, including untracked files) and the test run that exercised it. Only tick a checkbox you can back with a named file and a test run that passed under the relevant `--filter` — a step whose outcome is scaffolded but not validated, or whose test failed for an environment or auth reason that was not actually fixed, stays unchecked with a one-line note underneath naming the blocker. One exception: a step the plan explicitly frames as non-test preparatory work (a new integration or system test project, a CI job, a fixture scaffold) is evidenced by the named file alone. Be conservative with those — if the finished slice does not actually use the support, leave the step unchecked.

Report outcomes faithfully: failing output verbatim, deferred work stated plainly, facts rather than intent. Never include secrets, tokens, or cached auth state in the summary.

A run is complete only when code or test files were changed and the relevant tests were run, or you are stopping on a concrete, named blocker.

---

# Production Code Limits

Follow the minimal-production-change guidance in `docs/context-pack/testing-patterns.md` (it applies to all layers).

Production edits in a batch are what the selected tests require — constructor injection, a narrow interface seam, small data-access fixes that an integration test exposes as wrong, small deployed-configuration binding adjustments (`BaseUrl`, `EnvironmentName`, `TestRunId`, `Auth` profile) — and nothing more: no architectural refactors, DI rewrites, schema/seed restructuring beyond what the failing test requires, deployment-pipeline changes outside the explicitly selected step, or broad auth-model changes (switching identity platforms, rewriting the headless IdP auth helper).

A slice that needs more than ~4 production files or ~150 changed lines is too big for one autopilot batch — stop and report instead. Prefer one-target batches; only include a second or third plan step when it is mechanically part of finishing the same slice.

---

# Secrets and Environment Discipline

For `System` test batches:

- never commit passwords, TOTP seeds, bearer tokens, cookies, or cached auth state
- never log secrets in CI output, evidence summaries, or Teams failure notifications
- consume secrets only via the documented Key Vault + OIDC flow, or local developer bootstrap (`dotnet user-secrets`, macOS keychain, ignored local config)
- authenticate headlessly against the configured identity platform (Contoso B2C or Fabrikam Entra); do not fall back to Playwright cached browser state for API system tests
- if a required secret is missing, treat that as a blocker and stop

For integration batches:

- never use a shared QA database, broker, cache, or storage dependency for new tests added by this prompt unless the plan explicitly justifies isolated per-run state
- prefer Testcontainers, service containers, or per-run dependency namespaces
- ensure cleanup happens even when tests fail

---

# Output Expectations

End every run with a short evidence summary:

- the selected plan file and Plan ID
- which steps were completed, which layer they were in, and the exact checklist lines updated
- changed and untracked files, or a clear statement that no files were changed
- tests run, the project path or filter used, and the result
- whether any production seam was added
- any secret or infrastructure prerequisite the run depended on
- the exact blocker, if the batch stopped early

If the run did not achieve the "done" you declared at the start, say so explicitly and treat the batch as incomplete.
