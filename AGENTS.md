---
name: verify-reportmanager
description: Drive Report Manager the way a user does, prove the reports work, and capture evidence a human can judge. Use for "Test ENG-nnn please, Claude", report verification, and scheduled map sweeps.
---

# Verify Report Manager

Ground rules first:

- **Report Manager is Vue 3 + PrimeVue with HTML history routing** (`createWebHistory`,
  not Angular hash routing). The login button is `button.loginbutton`. The authenticated
  landing is `/content`.
- **Non-production only.** Contoso (dev) at
  `https://contoso.dev.noeticacloud.com/ReportManager` and Fabrikam (UAT). Never
  production.
- **Persona:** `admin` (zautotest-admin@noetica.com). The `user` persona's TOTP is
  known-bad (ENG-645, 2026-06). Use admin for the PoC.
- **Secrets never reach this file.** They come from `kv-noetica-dev-uksouth` at runtime:
  `zautotest-admin-password` and `zautotest-admin-totp`. Pull them into the environment
  with `scripts/fetch-e2e-secrets.ps1` (in `nub_web_reportmanager`), which calls
  `az keyvault secret show`.

## 1. Launch — connect and reach the intended build

1. Confirm the target environment. For ENG-645 this is Contoso (dev):
   `https://contoso.dev.noeticacloud.com/ReportManager/?path=entra`
2. Pull secrets:
   ```pwsh
   az login
   pwsh scripts/fetch-e2e-secrets.ps1 -Persona admin -KvName kv-noetica-dev-uksouth
   ```
3. The harness signs in through the Microsoft popup: username -> password -> TOTP
   -> stay-signed-in -> redirect to `/content`. Use the existing `AuthFixture` and
   `LoginPage` from `tests/ReportManager.E2E/` rather than reimplementing auth.
4. **Ready** means the `/content` dashboard renders report cards (PrimeVue
   `.report-card` elements) and the browser console has no errors. A database health
   check can pass while the front door is still redirecting from the login callback.

## 2. Doctor — is this instance worth driving?

Run these **before** any report checks. Stop and report if any fail:

| Check | How | Pass condition |
|-------|-----|----------------|
| Build identity | Sarah's deploy check (ENG-609) or `GET https://contoso.dev.noeticacloud.com/ReportManager/api/version` | Matches the build the card names |
| Environment reachable | `curl -fI https://contoso.dev.noeticacloud.com/ReportManager/` | HTTP 200, app-root URL |
| Auth valid | Run the `AuthFixture` login flow | Reaches `/content` with report cards |
| Reserved data | Sarah's stand-up tester conformance (`-Only`) checks Fabrikam reserved campaigns | Green on the target tenant |
| Secrets present | `az keyvault secret show` for both admin secrets | Both return a value |

A Doctor failure from skill drift (e.g. the login button moved) is a fix here; a Doctor
failure from a wrong build is a stop-and-report. See `tools/doctor/fabrikam.ps1` for
the scripted version that wraps Sarah's `Test-TenantFunctional.ps1`.

## 3. Drive — real user journeys through the harness

Each feature map entry in `maps/report-manager/` names which harness operation to run.
The harness is `nub_web_reportmanager/tests/ReportManager.E2E/` (from the repo root:
`tests/ReportManager.E2E/`), already wired with Playwright .NET, real TOTP login, and
per-test trace/screenshot/console capture via `PageObservation.RunAsync`.

**View a report:**
```pwsh
pwsh scripts/run-e2e-tests.ps1 -Category Verification -Persona admin -Filter "ReportNavigation"
```
If `run-e2e-tests.ps1` is not present in the repo (it's referenced in the README but
not found in the current checkout), fall back to `dotnet test` directly:
```bash
dotnet test tests/ReportManager.E2E/ReportManager.E2E.csproj -c Release --no-build \
  --filter "Category=Verification" \
  --logger "trx;LogFileName=e2e-verification.trx" \
  --results-directory "tests/ReportManager.E2E/TestResults"
```

**One report's View, Excel Check, Download:**
- The report page object (`ReportPage.cs`) navigates to the report's route.
- The map entry specifies the known date range and expected totals.
- The harness enters the range, clicks View Report, and asserts the grid matches the
  pre-agreed totals row by row.
- Excel Check: `ExcelTestReader.cs` opens the downloaded `.xlsx` and compares header
  + first rows against the on-screen grid.
- Download: save the workbook to the evidence directory and verify it opens.

**Key selectors** (from the page object classes, not a separate SELECTORS.md):
- Login: `button.loginbutton` (in `LoginPage.cs`)
- Dashboard cards: `.report-card` (PrimeVue, in `ContentPage.cs`)
- Results grid: `.p-datatable` (in `ReportPage.cs`)
- Export menu: `.export-button` (in `ReportPage.cs`)
- Date/range pickers: `.p-datepicker-input` / `.p-select` (in `ReportPage.cs`)

When a button moves, the agent updates the selector in the page object (the product
repo owns the harness) and the fix ships in the same PR. The feature map stays stable
because "Driving it" names the operation, not the selector.

## 4. Evidence — what proves it and where it goes

Every run produces an evidence bundle. Kim asked, 23 Oct 2026: a screen recording
and a trace of **every** browser step, pass or fail.

**Captured on failure (current state):**
- Playwright `trace.zip` (screenshots + DOM + console per step) — `PageObservation.cs`
  starts tracing in `StartAsync` and saves on failure via `CaptureFailureArtifactsAsync`.
- Page screenshots on failure — same path.
- Console logs: `page-errors.log` per test.

**Not yet captured on pass:** Video recording (`RecordVideo` is not set on the browser
context in `PlaywrightFixture.cs`) and traces are discarded on success (see
`tools/fix-escalation-gap.md` for the two-part fix: Part A adds `RecordVideo`, Part B
saves traces on success).

**Where it goes:**
- `tests/ReportManager.E2E/TestResults/<run-id>/` on the runner.
- On success, artifacts are uploaded (fix the current `if: failure()` gate).
- A copy of the run's `trace.zip`, video, and screenshots is written to
  `results/<run-id>/` in this repo so evidence survives cleanup.

**The result page** (see `results/README.md`) states, per check: pass, fail, blocked,
or not run; which builds were deployed; when; a run ID linking the records, calls, and
evidence; links to the trace/video/screenshot; and a cleanup status reported separately.

## 5. Cleanup — remove only what the run created

- Kill the Playwright browser context and any spawned `dotnet test` process.
- Remove temporary data files created during the run (e.g. downloaded workbooks in the
  scratch dir), but **never** the evidence bundle in `results/`.
- Do not reset the tenant, do not touch production schedules, do not delete seeded
  reference data unless this run seeded it.

---

## Drive it

For a single card:
```bash
claude -p "Test ENG-645 please, Claude" --allowedTools "Bash,Read,Write" --max-turns 20
```

For a scheduled sweep:
```bash
claude -p "Run the maintenance pass on the Report Manager maps" --max-turns 30
```

The scenario skill (`.claude/skills/scenario/SKILL.md`) is how Claude reads the card's
"How to verify" section, finds the journeys and feature maps it touches, and runs them.

For TEFT test calls, use the teft skill (`.claude/skills/teft/SKILL.md`). It covers the one-time
`teft` install, places a call as the customer outcome you choose (busy, no answer, an answering
machine, DTMF and so on), and reports its verdict and checks. Test tenants only. For example:

```bash
claude -p "Place a busy TEFT call on fabrikam and report the verdict" --allowedTools "Bash,Read" --max-turns 15
```
