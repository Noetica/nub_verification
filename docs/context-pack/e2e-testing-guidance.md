## Generic E2E testing guidance for UI repositories

> Audience: coding agents and LLM prompts first. Humans can skim this for strategy; the verification-team starting point is the org-wide onboarding suite in `nub_documents/verification/e2e-testing/`, plus any repo-specific tester guide alongside the E2E test project.

Purpose: provide a consistent default strategy source for agent-assisted E2E testing across repositories that may use different frontend technologies, including older Angular, modern Angular, Vue, and older ASP.NET MVC or Knockout applications.

This is intentionally framework-agnostic and detailed. The `/Add E2E Test` prompt and `playwright-qa` agent use it to guide implementation decisions so that different repos end up with a broadly similar test strategy, workflow shape, and maintenance model.

If the repository does not yet have a Playwright harness, start with `docs/context-pack/e2e-testing-bootstrapping-a-new-project.md` (synced to web-family repos; if it is not present in this repository, the canonical copy is in `nub_model_repository`).

Most of this guidance should transfer cleanly between web projects. For Noetica web projects, the shared Azure estate, Azure Key Vault secret flow, Teams notifications, and `zautotest-*` automation users are expected defaults. For projects outside that estate, treat those sections as concrete implementation patterns to adapt rather than mandatory dependencies.

### Python-family exception

For the `python` sync family (currently `noe_shared_agent` / Conductor), use
Playwright Test with TypeScript. Do not add a .NET test toolchain for these browser
tests; after setting up the harness and browsers, run `npx playwright test`.
This exception overrides the C# examples, .NET defaults and `dotnet test` commands
elsewhere in this guide; other repository families keep their existing defaults.

Python-family sync does not install `add-e2e-test` or `playwright-qa`; those helpers
remain `nub_web_*`-only. Skip the helper-copy prerequisites in the bootstrapping
guide for this family and create a minimal TypeScript harness directly. The shared
browser-testing strategy still applies, adapted to the application's actual auth
and hosting setup.

### Core principles
- Prefer one primary browser automation approach across the organisation rather than a different tool in every repo.
- Treat E2E tests as a product-quality safety net, not just a last-mile verification convenience.
- Use E2E tests to prove the system works as a user experiences it: authentication, routing, page load, key workflows, permissions, and obvious failure states.
- Keep the first suite small, reliable, and high-signal.
- Separate fast smoke coverage from broader verification coverage.
- Run code-quality smoke tests against the branch build of the application in CI, not only against a shared deployed environment.
- Use deployed-environment runs for verification and release confidence, not as a substitute for branch validation.
- Treat post-deployment smoke as a deployment-health check: run it after the deployment has completed, and keep it smaller than the full verification pack.
- Run scheduled or manually dispatched full verification against the deployed non-production environments that matter for release confidence, usually dev and UAT.

### Default tool choice
- Default to Playwright for browser-based E2E testing unless there is a hard technical blocker.
- Use one implementation language consistently where possible so the same engineers can maintain tests across repos.
- If the team strongly prefers C# or the frontend toolchain is old or awkward, Playwright .NET is a good default.
- If the repo has a modern JavaScript toolchain and the team prefers TypeScript, Playwright with TypeScript is also valid, but it is not preferred here because team knowledge is .NET first.
- Do not choose a different E2E framework per repo unless there is a strong reason.

### Where tests should live
- Keep E2E tests in the same repository as the application unless there is a clear operational reason not to.
- Keep test changes versioned with the UI changes they validate.
- Use a clear top-level location for E2E automation so the structure is easy to find and reuse.
- If test-only changes should not trigger deployment, solve that in CI workflow design rather than immediately splitting repos.

### Standard suite split

#### 1. PR smoke tests
Purpose:
- catch high-value regressions before merge
- protect routine maintenance and LLM-assisted changes

Characteristics:
- very small
- very reliable
- non-destructive where possible
- runs against the branch build in CI
- required for merge once stable
- target a fast feedback budget, usually low single-digit minutes rather than tens of minutes
- should usually support both automatic PR triggering and manual `workflow_dispatch` runs so the same branch-build smoke can be exercised during setup, debugging, or infrastructure validation without opening a throwaway PR

Guidance:
- default to smoke-only PR gating rather than running the full verification pack on every pull request
- if the PR smoke suite starts drifting upward, shrink scope or remove redundant checks before accepting a slower merge gate
- treat the smoke suite as protection against obvious breakage, not as exhaustive release certification

Typical coverage:
- login works
- authenticated landing page loads
- authenticated landing page does not emit browser console errors
- main navigation works
- key page loads succeed
- obvious app-level errors do not appear

#### 2. Verification regression tests
Purpose:
- cover broader business workflows
- reduce manual regression effort for normal releases
- prove that deployed non-production environments remain healthy over time

Characteristics:
- larger than smoke
- may include selected write flows
- should usually run on a schedule such as nightly, or on demand for risky work
- can run locally or against a branch build when an engineer or agent wants extra confidence before a PR
- should target deployed dev and UAT for routine release-confidence checks

Guidance:
- do not make the full verification pack a normal PR blocker unless it becomes both fast and consistently reliable enough not to damage developer flow
- when a scheduled or on-demand verification run fails, send a Teams or Slack notification from the workflow with the run link and the failing suite summary
- treat verification failures on main as a team-owned follow-up item to fix or revert quickly rather than as a reason to slow every PR by default
- be explicit about the target environment in the run result; a UAT failure only says something about the version currently deployed to UAT, which may lag behind dev

#### 3. Post-deployment smoke checks
Purpose:
- answer questions like "did the deployment complete successfully?", "can we log in?", and "is the deployed system basically alive?"

Characteristics:
- separate concern from product PR validation
- may reuse some browser journeys from the E2E harness
- should be triggered by a real deployment-success signal or deployment pipeline continuation, not by an arbitrary sleep
- should usually run against deployed dev after automatic promotion to dev
- should stay much smaller than the full verification pack

Guidance:
- run deployed smoke after dev deployment has completed, especially when dev is automatically promoted from main
- do not assume UAT contains the merged code unless the UAT deployment has completed; when UAT promotion is manual, test UAT on a schedule or as part of the UAT promotion/verification process
- keep deployed smoke conceptually separate from PR code-quality gating

#### 4. Operational or client-system smoke checks
Purpose:
- answer longer-term availability questions for customer-like systems, outside the normal development and release workflow

Characteristics:
- separate concern from product PR validation and release verification
- may reuse some browser journeys from the E2E harness
- can evolve into synthetic monitoring later

Guidance:
- do not make this the first implementation goal unless that is the urgent business need
- keep it conceptually separate from code-quality gating and release verification

### Authentication guidance
- Authentication is usually the hardest part of browser automation and should be treated as first-class design work.
- Use dedicated automation identities rather than personal accounts.
- For Noetica web projects, use the shared `zautotest-*` automation identities for interactive login flows where the target app supports them (see _Standard users for testing_ below).
- Start with one stable automation identity for the initial harness if that is the fastest route to a reliable smoke test. Add extra personas once the core auth and landing flow is stable.
- If MFA is required, automate it in a supported way rather than disabling it arbitrarily.
- Log in once per run where possible and reuse the same live authenticated browser context or page for the rest of that run to keep tests fast and stable.
- Only add Playwright storage-state reuse across separate runs if it is proven stable in the application's auth stack. Do not keep a speculative restore path that adds delay and harness complexity without buying real confidence.
- In older MSAL Angular applications, do not assume cross-run storage-state restore is reliable even when cookies, localStorage, and refresh tokens are present. If the application immediately forces logout or returns to the login route after restore, remove the restore path and prefer one interactive login per job plus a shared live browser context for the suite.
- If the suite uses one shared automation identity with interactive popup auth and MFA, disable test parallelization or otherwise serialize login-capable tests. Concurrent login attempts against the same account can interfere with each other before the app is even reached.
- Do not adopt persistent browser profiles as the default auth-reuse strategy. Prefer storage state or one-login-per-job reuse first, especially when CI runners are ephemeral and later Firefox/WebKit validation matters.
- Never commit cached auth state, cookies, or tokens to source control.
- Never commit the automation password or TOTP seed to source control.
- Never let an automation password or TOTP seed reach the CI run log in plain text. See the Azure-backed secret management bullet under CI guidance for the runner-masking rules.
- When extra personas are introduced later, keep cached auth state separate per persona. Do not reuse an administrator's saved browser state for limited-access or denied-access journeys.
- In popup-based auth flows, clicking the app's `LOGIN` button may leave the original tab unchanged and open a separate popup or tab for the identity provider. Tests should model that explicitly instead of expecting navigation in the original page.
- In multi-environment systems, the visible pre-login page can remain identical while the popup authority differs by environment, tenant, or query-string parameters. Parameterize auth assumptions by environment rather than hard-coding a single authority URL.
- If a newly provisioned automation user completes identity-provider login but the SPA fails before it reaches the authenticated shell, treat user provisioning and claim shape as the first debugging target. Do not change the product auth code just to satisfy the test unless the application genuinely needs to support the new claim contract.
- If local secret bootstrap uses Azure CLI plus Key Vault, a stale CLI session can block test setup before Playwright starts. `AADSTS700082` is the usual indicator that `az login` must be repeated.
- Microsoft reuses `#idBtn_Back` as the element ID for both the MFA "Cancel" button and the "Stay signed in" "No" button. Always confirm the page heading before clicking `#idBtn_Back` to avoid cancelling MFA instead of dismissing the post-auth prompt.
- The Microsoft popup `Enter code` page uses `input[name='otc']` for the TOTP input and a `Verify` button, not `#idSIButton9`. The stay-signed-in page heading contains "Stay signed in" or "reduce the number of times".
- TOTP codes are only valid for ~30 seconds. In E2E automation, generate the code immediately before filling it — not minutes earlier during a multi-step inspection.
- Chromium-based browsers show a native save-password bubble after password entry. This is browser chrome, not page DOM, so Playwright cannot interact with it. Suppress it with launch args: `--disable-save-password-bubble`, `--disable-password-generation`, `--password-store=basic`.
- For Angular hash-routing apps (`useHash: true`), do not use `Page.WaitForURLAsync()` with a load event. Use `Page.WaitForFunctionAsync()` with `window.location.hash.startsWith(...)` instead, since hash changes do not trigger navigation load events.

Reusable Microsoft popup auth fixture pattern:
- Trigger auth with `Page.RunAndWaitForPopupAsync()` because the app page often stays on `/#/login` while Microsoft opens in a separate popup.
- Wait for the popup to leave `about:blank` before interacting, otherwise selectors can race the real Microsoft page load.
- Username step: watch for `input[name='loginfmt']` or `input#i0116`, then submit with `#idSIButton9`.
- Password step: watch for `input[name='passwd']` or `input#i0118`, then submit with `#idSIButton9`.
- MFA code step: watch for heading text like `Enter code`, fill `input[name='otc']`, and submit with Enter or the visible continue button.
- Stay-signed-in step: only click `#idBtn_Back` after confirming the prompt text contains `Stay signed in` or `reduce the number of times`, because the same element ID is also the MFA `Cancel` button.
- Completion step: wait for the application route and authenticated shell, not popup closure alone. The popup may remain briefly on a redirect URL after the main app is already authenticated.

Example Playwright .NET shape:

```csharp
var popup = await page.RunAndWaitForPopupAsync(loginPage.ClickLoginAsync);
await WaitForMeaningfulPopupUrlAsync(popup);

await popup.Locator("input[name='loginfmt'], input#i0116").FillAsync(username);
await popup.Locator("#idSIButton9").ClickAsync();

await popup.Locator("input[name='passwd'], input#i0118").FillAsync(password);
await popup.Locator("#idSIButton9").ClickAsync();

var totpInput = popup.Locator("input[name='otc'], input#idTxtBx_SAOTCC_OTC");
if (await totpInput.IsVisibleAsync())
{
  await totpInput.FillAsync(currentCode);
  await totpInput.PressAsync("Enter");
}

var kmsiText = await popup.Locator("body").InnerTextAsync();
if (kmsiText.Contains("Stay signed in", StringComparison.OrdinalIgnoreCase)
  || kmsiText.Contains("reduce the number of times", StringComparison.OrdinalIgnoreCase))
{
  await popup.Locator("#idBtn_Back, input[value='No'], button:has-text('No')").First.ClickAsync();
}

await page.WaitForFunctionAsync(
  "expectedHash => window.location.hash.startsWith(expectedHash)",
  "#/agents");
await page.Locator("igx-grid").First.WaitForAsync();
```

Cross-browser note:
- Keep the fixture browser-agnostic where possible.
- Localise browser-specific workarounds such as Chromium password-manager suppression behind conditional launch options.
- Once the Chromium-first path is stable, rerun the same auth flow in Firefox and WebKit before introducing engine-specific branches.

### Standard users for testing

A small, fixed set of automation identities is preferred over trying to toggle permissions at runtime. Three roles cover the meaningful branches in most management apps without needing finer-grained variants.

| User | Role | Typical coverage in the application under test |
|---|---|---|
| `zautotest-admin@noetica.com` | Admin / superuser — has all permissions plus admin bypass | Smoke only — proves the admin path works end to end |
| `zautotest-user@noetica.com` | Normal user with all app permissions, no admin bypass | Primary target for the full test suite — exercises the real permission-check code paths |
| `zautotest-agent001@noetica.com` | Agent identity with no access to the application | One rejection/denied-access test — confirms they cannot reach a protected app they are not assigned to |

Notes:
- Use `zautotest-user` as the default automation identity for new suites. The admin user should not be the only thing the harness exercises, because admin bypass can hide permission-logic regressions.
- The agent identity is numbered (`-agent001`) to leave room for additional agent personas across other repos. A given project usually only needs one denied-access identity to prove that path.
- Keep cached auth state separate per persona. Do not reuse an administrator's saved browser state for limited-access or denied-access journeys.
- The harness needs to support picking between these identities. One concrete pattern is `E2E__Persona=admin|user|agent` plus persona-specific secret names. Equivalent named-config approaches are also fine if documented clearly.

### Shared automation config contract
- Across repos, keep the automation config shape broadly the same even if individual values differ.
- A useful shared contract is `StartDirectory`, `LoginUrl`, `Username`, `Browser`, `Password`, and `TotpSecret`.
- Safe values to document in a repo are the automation username, preferred browser, and the repo-specific login URL shape.
- Sensitive values such as `Password` and `TotpSecret` should come from local secret storage, CI secrets, or a shared secret manager rather than the repository.

Recommended default for Noetica / Azure-hosted teams:
- Use Azure Key Vault as the source of truth for E2E secrets.
- Let GitHub Actions fetch those secrets at runtime using OIDC federation to Azure rather than duplicating the secret values into GitHub environment secrets.
- Let local developers fetch the same secrets from Key Vault using their Entra identity, usually via `az login` plus a small bootstrap script that copies values into a machine-local ignored store.
- Where interactive local runs depend on those secrets, prefer a harness or runner that can attempt the Key Vault bootstrap automatically when secrets are missing instead of immediately failing with a manual setup error.
- Provide one obvious local entry point such as `pwsh scripts/run-e2e-tests.ps1 -Category Smoke` so engineers adding tests do not have to remember a separate secret-fetch, browser-install, and test command sequence.
- Use GitHub environment secrets only for non-secret environment metadata if needed, or as a short-lived fallback during initial setup.

Example shape:

```json
{
  "AppSettings": {
    "StartDirectory": "C:\\tests\\",
    "LoginUrl": "<this-project login url>",
    "Username": "zautotest-user@noetica.com",
    "Browser": "chrome",
    "Password": "<from secret store>",
    "TotpSecret": "<from secret store>"
  }
}
```

Example Azure Key Vault mapping (one password/TOTP pair per persona):
- Key Vault: `https://<vault-name>.vault.azure.net/`
- Admin: `zautotest-admin-password`, `zautotest-admin-totp`
- Normal user: `zautotest-user-password`, `zautotest-user-totp`
- Agent: `zautotest-agent001-password`, `zautotest-agent001-totp`

### Azure identity configuration for E2E

The Azure identity used by the workflow reads Key Vault; the `zautotest-*` persona logs into the
application. Keep these two identities distinct in setup instructions. A client ID identifies an
Azure identity; it is not a password and does not grant access by itself. OIDC federation and the
identity's Key Vault permissions must also match the workflow.

For new E2E workflows, use this configuration vocabulary:

| Setting | Meaning |
|---|---|
| `AZURE_CLIENT_ID` | Client ID of the identity authorised to read E2E secrets |
| `AZURE_TENANT_ID` | Entra tenant containing that identity |
| `AZURE_SUBSCRIPTION_ID` | Subscription used by the Azure login |
| `E2E_KEYVAULT_NAME` | Vault holding the persona password/TOTP pairs |

These are identifiers, not the persona secrets. Document each setting's actual GitHub scope
(organisation, repository or environment) and whether the workflow reads `vars` or `secrets`.
Existing names such as `uami_noetica_dev_clientid`, `ORG_AZURE_TENANT_ID` and
`ORG_AZURE_SUBSCRIPTION_ID_DEV` can remain when their mapping is documented; renaming a setting
does not change its availability to a workflow. Migrate a working name only with its configuration
and consumers together, not as a prerequisite for adopting this guide.

Keep the E2E identity's purpose separate from deployment access. Do not substitute a deployment
setting such as `ENV_AZURE_MANAGED_IDENTITY` without verifying its intended trust and permissions.
The repo's E2E README should identify the vault, the Azure identity, the GitHub environment, the
federated subject and the required vault-read scope. Shared identities may serve multiple repos
only where their existing trust and permissions cover those repos; copying another repo's client
ID does not establish that trust. Use the actual environment subject, for example
`repo:Noetica/<repository>:environment:dev`, when the job declares `environment: dev`.

### Environment strategy
- Tests should be configurable by environment rather than tied to one URL.
- Standard inputs should include at least base URL, environment name, browser, username, password, and any MFA or auth bootstrap settings.
- The same harness should be able to run against:
  - a local developer build
  - a CI-started branch build
  - a deployed non-production environment
- Prefer a single canonical environment for CI smoke to avoid noisy results caused by environment drift.
- When the frontend can be built and served locally with CI-style runtime config, prefer that for branch validation instead of deploying the frontend first. It is usually enough to point the local or CI-served branch build at the target non-production backend and validate the real auth and app bootstrap flow there.

### What to test first
- login and session establishment
- permission or role-based landing behavior
- navigation to main application areas
- page load success for the highest-value modules
- one or two critical read-only user journeys

Add later, once the initial harness is stable:
- allowed-user behavior for at least one non-admin persona
- denied-access behavior for at least one authenticated but unauthorized persona

Do not start with:
- a huge regression matrix
- fragile visual checks
- complex destructive CRUD flows without a data strategy
- exhaustive edge-case permutations better covered by lower-level tests

### Data and state guidance
- Prefer read-only or low-impact scenarios first.
- When write flows are needed, define ownership of test data clearly.
- Use unique names or identifiers for created records to avoid collisions.
- Add explicit cleanup rules for destructive tests.
- If setup through the UI is slow or brittle, consider backend-assisted setup later, but keep the primary assertions at the browser level.

### Test data strategy — idempotent marker data

All test-created data must be immediately identifiable and safe to clean up.

#### Naming convention
- All test-created records use the prefix `e2e-auto-` (e.g. `e2e-auto-20260411143022`).
- If `e2e-auto-` is unsuitable for a field (character restrictions, length limits), fall back to `e2e-` or `e2e` as the prefix.
- If possible, append a UTC timestamp or GUID to avoid collisions across parallel or repeated runs.
- Never use real user names, customer names, or production-meaningful identifiers.

#### In-test cleanup
- Each write test is responsible for cleaning up what it creates, within the same test method or a deterministic teardown.
- If the UI supports deletion (even soft-delete), use the UI flow to remove the record and verify removal.
- If the system soft-deletes rather than hard-deletes, accept that the record persists in the database but is no longer visible. The test should handle re-creation gracefully (e.g. accepting a "restore" or "undelete" prompt if the same identifier is reused).

#### Housekeeper cleanup for residual data
- Some operations cannot be fully reversed through the UI (e.g. data uploads, batch jobs, configuration changes with downstream side-effects).
- For these, add a scheduled housekeeper task that identifies and removes test artifacts by their `e2e-auto-` or `e2e-` prefix.
- The housekeeper should run on a schedule (e.g. nightly or weekly) and only operate on non-production environments.
- The housekeeper does not replace in-test cleanup — it is a safety net for partial failures and orphaned records.

#### Environment restrictions
- E2E write tests must never run against production customer environments.
- It is acceptable to run them against a dedicated test server hosted in the production infrastructure, provided that server does not share a database or downstream services with real customer data.
- The test runner configuration should make the target environment explicit. Prefer a named environment enum or URL allowlist rather than relying on engineers to remember not to point at production.
- CI workflows should hard-code the target environment rather than accepting arbitrary URLs for write-capable test categories.

#### What this means in practice

| Scenario | Approach |
|---|---|
| Agent CRUD (soft-delete available) | Create with `e2e-auto-` prefix → verify → delete in UI → verify removal. Handles undelete transparently. |
| Data upload job (not UI-reversible) | Upload with `e2e-auto-` marker in the payload → verify the upload succeeded → rely on the housekeeper to clean up. |
| Configuration change with side-effects | Prefer route interception (`page.route()`) for PR smoke to avoid real changes. For verification runs, use marker data and housekeeper cleanup. |
| Read-only verification | No test data created — no cleanup needed. |

### Agent-assisted test authoring

When coding agents (Copilot, Claude, etc.) are writing or maintaining E2E tests, two Playwright tools are available to bridge the gap between reading source code and knowing what the browser actually renders.

#### Playwright CLI + Skills (primary agent tool)
- Install globally: `npm install -g @playwright/cli@latest`
- Install skills for your agent: `playwright-cli install --skills`
- CLI+Skills is token-efficient — it avoids loading large accessibility trees into the model context.
- Use it for:
  - discovering selectors against the live app (`playwright-cli snapshot`)
  - verifying that source-derived selectors actually match at runtime
  - debugging failing tests by replaying steps interactively
  - generating test code from recorded interactions
- Recommended as the default tool for coding agents writing tests.

#### Playwright MCP (for exploration and debugging)
- Install as an MCP server: `npx @playwright/mcp@latest`
- MCP provides a persistent browser context with rich accessibility snapshots.
- Use it for:
  - longer exploratory sessions across multiple pages
  - iterative reasoning over complex page state
  - self-healing selectors when the DOM structure is unclear
  - investigating flaky test failures with live state inspection
- MCP is more token-expensive than CLI but better suited for deep investigation.
- If MCP reports `Browser is already in use` after the browser window was closed, the usual cause is a stale `@playwright/mcp` wrapper process still holding the profile lock. Kill the stale wrapper processes and retry before assuming the install is broken.
- Treat `.playwright-cli/` and `.playwright-mcp/` as transient local artifact folders and add them to `.gitignore`.

#### Recommended agent workflow per test
1. Agent reads source code (templates, routing, component TS) to write the test skeleton and probable selectors.
2. Agent uses `playwright-cli snapshot` against the live app to verify selectors and discover element refs.
3. Agent refines selectors based on snapshot evidence.
4. Developer runs `dotnet test` (or equivalent) to execute the full suite.
5. On failure, agent uses CLI or MCP to diagnose and fix.

#### Selector discovery with component libraries
When the app uses a component library (IgniteUI, Material, PrimeNG, etc.), source-derived selectors are often insufficient because the library renders additional wrapper DOM. Prefer this approach:
- Start with component tag selectors (e.g., `igx-grid`, `mat-table`) from source.
- Verify with `playwright-cli snapshot` to see the actual accessibility tree.
- Fall back to text content or ARIA roles when component tags are ambiguous.
- Add `data-testid` attributes to the application templates only where selectors prove fragile.
- Document verified selectors in a `SELECTORS.md` file in the test project.

### Locator and maintainability guidance
- Prefer stable accessible locators such as roles, labels, and visible names.
- Add dedicated test selectors only where necessary.
- Keep page objects or helper abstractions thin and focused on reusable actions.
- Keep authentication fixtures focused on proving that the authenticated landing page is ready. Put role- or permission-specific UI assertions in separate tests so auth failures are not conflated with authorization differences.
- When a legacy auth stack invalidates restored sessions across separate runs, keep the app unchanged unless there is strong product appetite for auth-risk work. Compensate in the harness instead by authenticating once per suite and opening additional pages inside that same authenticated context, rather than preserving a flaky cross-run restore mode.
- If auth stability requires reusing one already-authenticated SPA page, keep the shared page but wrap each test in its own tracing and browser-log capture scope so failures still produce isolated artifacts.
- Avoid over-abstracting too early.
- Keep tests readable enough that a reviewer can understand the user journey quickly.

### CI guidance
- Build and serve the application under test inside CI for PR smoke runs whenever practical.
- Run only the small smoke pack in PR validation.
- Keep the PR smoke pack intentionally fast; if a scenario is valuable but slow, move it into the broader verification suite.
- Run the broader verification suite locally/on demand for risky branches, and scheduled or manually against deployed non-production environments rather than by default on every PR.
- For automatic post-merge coverage, prefer a deployed smoke suite triggered after the dev deployment reports success. Avoid fixed waits as a substitute for deployment readiness.
- Run scheduled deployed verification against both dev and UAT when both environments are part of the release path; keep their results separate so environment-specific failures are clear.
- Send a Teams notification from scheduled, post-deploy, or on-demand deployed verification workflows when they fail so the team sees main-branch or environment regressions quickly.
- Keep smoke and diagnostic notifications failure-only by default. If a temporary success notification is used while validating a new webhook path, record the cleanup explicitly and remove the success path once the webhook is proven.
- Publish useful failure artifacts such as traces, screenshots, console output, and page errors to an ignored `TestResults/` path.
- Keep broader verification suites manual or scheduled until they are stable and fast enough.
- Isolate deployment workflows from test-only changes if necessary.
- Remember that `workflow_dispatch` only works once the workflow file exists on the default branch. For pre-merge debugging of a new workflow, use an existing default-branch workflow as the validation carrier or add a temporary branch trigger rather than assuming the brand-new workflow can be run manually immediately.
- For Azure OIDC bring-up, add a small diagnostic path that logs which non-secret Azure inputs are present and prints selected GitHub OIDC claims before `azure/login`. This usually narrows wrong-client-id, wrong-tenant, and wrong-subject problems faster than debugging the failing login step blind.
- For Teams Workflows notifications, use the Workflows webhook envelope (`type: "message"` with an Adaptive Card attachment), not the legacy connector card format. If direct user notification is required, encode user mentions in `msteams.entities` and assume tag mentions are unavailable unless proven otherwise in the target delivery path.
- If the production build keeps a fixed base href such as `/my-app/`, stage the built files under a matching subdirectory before serving them in CI instead of changing application routing or auth behavior just for tests.
- Prefer a committed CI-only runtime appsettings asset with non-secret auth and API metadata, and copy it over the built `appsettings.json` at serve time rather than editing the app code for CI.
- Prefer environment-variable overrides for test-runner settings such as `BaseUrl`, `LoginUrl`, `Headless`, `Password`, and `TotpSecret` so CI can inject runtime values without creating tracked config files.
- Use workflow path filters so markdown-only PRs skip the E2E smoke workflow, while `tests/**` or workflow-only changes do not trigger unrelated deployment jobs.
- For Azure-backed secret management, prefer this flow:
  - GitHub Actions authenticates to Azure using OIDC federation.
  - The workflow reads E2E secret values from Azure Key Vault at runtime.
  - The workflow exports those values only for the lifetime of the job.
  - The repository does not store the password or TOTP seed.
  - Before writing any Key Vault value to $GITHUB_ENV (or echoing it for any reason), register it with the runner by emitting `::add-mask::<value>` so the runner redacts it from subsequent log output. Masking only takes effect for values registered before they first appear in the log, so do this immediately after the `az keyvault secret show` call and before the heredoc or echo that exports it.
  - Do not enable `set -x` in steps that handle Key Vault values, and do not echo the fetched values for debugging. Masking is a backstop, not a substitute for keeping secrets out of the log in the first place.

#### Dependency updates and authenticated smoke

Dependabot-triggered runs use the Dependabot secret store, not Actions secrets. Re-running the
same failed run as a developer retains that restriction. A missing Azure client-ID input in such
a run is a configuration/context failure, not evidence of a dependency regression or a reason to
rename the input. See [GitHub's Dependabot workflow restrictions](https://docs.github.com/en/code-security/reference/supply-chain-security/troubleshoot-dependabot/dependabot-on-actions).

Follow the [dependency-management policy](https://github.com/Noetica/nub_documents/blob/main/engineering/dependency-management.md):
routine updates accompany feature work; an explicitly authorised maintenance change can carry
the selected updates too. Run the full branch-build smoke pack on the resulting maintainer-owned,
same-repository PR using
the established OIDC/Key Vault configuration, and record the commit actually tested. Confirm the
run's actor, credential availability and results rather than assuming that a branch name or an
older green check establishes coverage. The original dependency PRs remain open until their
updates land through the normal review and validation path.

Do not turn an authenticated smoke gate into build-only validation, skip login assertions or
expand credential access just to clear a Dependabot failure. An existing repo-specific build-only
exception reports build coverage only; it is not a shared default or evidence of a smoke pass.
If a manual run is needed, use an existing authorised `workflow_dispatch` path against the exact
candidate branch and verify its tested SHA. A run against deployed `main` does not validate that
branch's frontend. Keep missing access or failed smoke explicit until full validation is available.

### Local developer secret flow
- For local execution, prefer the same source of truth as CI rather than a second manually maintained secret copy.
- Developers authenticate with `az login` using their Entra identity.
- A small bootstrap script reads the needed secrets from Azure Key Vault and stores them in a machine-local ignored location such as:
  - `.NET user-secrets`
  - macOS keychain
  - an ignored local config file such as `.env.local` or `appsettings.local.json`
- The test runner should read local machine values first and fall back to environment variables when appropriate.
- Keep the local bootstrap path and the CI OIDC path aligned so both flows use the same Key Vault secret names and only differ in how Azure authentication is obtained.
- For Azure-hosted self-hosted runners, managed identity is a good fit. For normal developer laptops, use user identity via `az login` instead.
- Avoid making test authors run the bootstrap script manually as a prerequisite they have to remember. Prefer one of these patterns:
  - a wrapper script that restores secrets, installs browsers if needed, and then runs the requested test category
  - test-startup logic that detects missing local secrets and attempts the Azure CLI bootstrap automatically before failing
- If automatic local bootstrap is implemented, make the failure message actionable and specific. It should say whether Azure CLI is missing, `az login` is stale, or Key Vault access failed.
- Treat low-friction local execution as part of the harness design, not as documentation polish. If the goal is for test engineers who are not full-time developers to add or run tests, the default local path should be one command, not a checklist.

### Relationship to lower-level tests
- E2E tests are not the only tests worth having, but they usually provide the highest early return in UI-heavy systems.
- Add lower-level tests selectively for pure logic that is cheap to test and expensive to debug through the UI.
- Do not spend large amounts of effort on brittle UI unit tests unless they clearly pay off.
- For frontend-heavy repos, the usual order of return on investment is:
  - first: a reliable E2E smoke suite
  - second: broader E2E verification coverage
  - third: targeted lower-level tests for pure logic

### Delivery model

#### Phase 1
- choose the single primary E2E tool and language
- define the environment and auth contract
- create the harness foundation
- implement the first smoke journeys

#### Phase 2
- gate PRs on the stable smoke suite
- improve selector reliability where needed
- document local and CI execution clearly

#### Phase 3
- expand into broader verification coverage
- add selected write flows with controlled test data
- support deployed non-production execution, starting with manual dispatch against dev

#### Phase 4
- add post-dev-deploy smoke once there is a reliable deployment-complete signal
- schedule full deployed verification against dev and UAT, with UAT runs tied to the code actually deployed there
- revisit operational smoke monitoring as a separate track if needed
- add targeted lower-level tests where they offer clear value
- fold the proven verification-workflow and notification lessons back into the shared guidance before upstreaming it to other repos

### Good outcomes to aim for
- every repo has a recognisable smoke-versus-regression split
- browser automation uses the same core tool and similar workflow shape across repos
- auth is handled through dedicated automation users such as the `zautotest-admin`, `zautotest-user`, and `zautotest-agent001` personas
- login state is cached for speed where appropriate
- PR validation proves the branch build basically works
- post-deploy smoke proves the automatic dev deployment basically works before the team treats dev as healthy
- broader verification can run against deployed dev and UAT without redesigning the suite
- teams can trust routine changes more without manually verifying every screen on every release

### Suggested Copilot instruction text
If you are adding or planning E2E testing in this project, use a consistent Playwright-based approach unless there is a hard blocker. Keep tests in the same repo as the application, split them into a very small PR smoke suite and a broader verification suite, and run PR smoke against the branch build in CI rather than only against shared deployed environments. Use deployed runs for deployment and release confidence: run a small smoke suite after the automatic dev deployment has completed, and run the broader verification pack on a schedule or manually against deployed dev and UAT, keeping UAT results tied to the version actually deployed there. Treat authentication as first-class design work: prefer shared automation personas where available, such as the Noetica `zautotest-admin`, `zautotest-user`, and `zautotest-agent001` identities; use the normal-user persona as the primary target for full suites so admin bypass does not hide permission-logic regressions; support MFA automation if required; and cache authenticated browser state for reuse within a run to keep tests fast. Use a shared automation config shape such as `StartDirectory`, `LoginUrl`, `Username`, `Browser`, `Password`, and `TotpSecret`, but keep the password and TOTP secret in a proper secret store rather than source control. For local runs, prefer one obvious command entry point and a harness that can attempt local secret bootstrap automatically when required, so test authors do not have to remember a separate secret-fetch step before running authenticated tests. Start with login, landing-page load, navigation, and the highest-value journeys, keep early tests reliable and mostly non-destructive, and publish useful failure artifacts from CI. Add lower-level tests later for pure logic where they clearly pay off, but do not lead with brittle UI unit tests. When writing or maintaining tests as an agent, use Playwright CLI + Skills (`playwright-cli snapshot`) to verify selectors against the live app rather than guessing from source code alone. Use Playwright MCP for longer exploratory or debugging sessions where persistent browser state is useful.
