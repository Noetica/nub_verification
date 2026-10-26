# Fix guide: escalation gaps in e2e-verification.yml

Three concrete problems in `nub_web_reportmanager`'s verification workflow. All
line references are to `.github/workflows/e2e-verification.yml` (cloned at
`rpm_clone/`). The same skip-gate pattern appears in `e2e-smoke.yml`.

## Problem 1: Skip-gate reports success (the core issue)

**Where:** `e2e-verification.yml` lines 97-102.

```yaml
  verification:
    needs: ensure-runner
    if: ${{ vars.E2E_RUNS_ON != '' && vars.E2E_KEYVAULT_NAME != '' }}
```

When the variables are unset, GitHub marks the job **skipped** (neutral). A skipped
job is not a failing job — the workflow reports **success** with zero evidence. The
README (lines 130-132) admits this: "Both workflows skip cleanly (neutral, not red)
until the repo Variables are set."

**Fix:** Remove the `if:` gate from the job. Replace it with an unconditional
pre-flight step that checks the variables and **fails** (red, not skip-green) when
they are missing:

```yaml
  verification:
    needs: ensure-runner
    # No if: gate — the job always runs so missing config is a hard failure.
    runs-on: ${{ vars.E2E_RUNS_ON || 'windows-latest' }}
    steps:
      - name: Check E2E prerequisites
        if: always()
        shell: pwsh
        run: |
          $missing = @()
          if (-not "${{ vars.E2E_RUNS_ON }}")       { $missing += "E2E_RUNS_ON" }
          if (-not "${{ vars.E2E_KEYVAULT_NAME }}") { $missing += "E2E_KEYVAULT_NAME" }
          if (-not "${{ vars.E2E_DEV_BASE_URL }}")  { $missing += "E2E_DEV_BASE_URL" }
          if (-not "${{ vars.E2E_DEV_LOGIN_URL }}") { $missing += "E2E_DEV_LOGIN_URL" }
          if ($missing.Count -gt 0) {
            throw "VERIFICATION BLOCKED — missing repo Variables: $($missing -join ','). A skipped run is NOT evidence of passing."
          }
```

Apply the same fix to `e2e-smoke.yml` lines 117-123 for the PR gate.

## Problem 2: No evidence on success (artifacts only on failure)

**Where:** `e2e-verification.yml` lines 203-208.

```yaml
      - name: Upload failure artifacts
        if: failure()
```

A passing run uploads nothing. Traces, screenshots, and test results exist only
transiently on the runner.

**Fix:** Change `if: failure()` to `if: always()`, and bump retention to 14 days:

```yaml
      - name: Upload verification artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-verification-artifacts-${{ env.E2E_ENVIRONMENT }}
          path: tests/ReportManager.E2E/TestResults/
          retention-days: 14
```

## Problem 3: No video recording on pass (Kim's ask, 23 Oct 2026)

**Where:** `PlaywrightFixture.cs` lines 29-35 — launch options set `Headless` and
`SlowMo` but never set `RecordVideo` on the context.

And `PageObservation.cs`: tracing starts in `StartAsync` (line 89) but the trace is
only saved to disk in `CaptureFailureArtifactsAsync` (line 128), called only from
the catch block (line 51). So **both traces and screenshots are failure-only**.

**Fix (two parts):**

### Part A: Record video on every run

The browser context is created in `AuthFixture.CreateAuthenticatedPageAsync()`.
Add `RecordVideo` to the context options there:

```csharp
var context = await playwright.Chromium.NewContextAsync(new BrowserContextOptions
{
    // ... existing options ...
    RecordVideo = new() { Dir = videoDir },  // add this
});
```

where `videoDir` is wired from `E2ESettings` (e.g. `E2E__VideoDir`).

### Part B: Save traces on every run

Move the artifact-directory creation from `CaptureFailureArtifactsAsync` (line 135)
to `StartAsync` so it exists before the step runs. Then in `DisposeAsync`
(line 202-224), change the unconditional `Tracing.StopAsync` to save the trace:

```csharp
// In DisposeAsync — save the trace on success too
await page.Context.Tracing.StopAsync(new TracingStopOptions
{
    Path = Path.Combine(artifactDirectory, "trace.zip")
});
```

This keeps one trace per observed step, pass or fail.
