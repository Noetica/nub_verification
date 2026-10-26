# Run results

Every verification run writes a result page here. Sarah's stand-up tester format
(ENG-809) is the base: JSON plus readable text, one summary with a verdict, and
pinned failures that stay visible. The verification runs extend it with a run ID and
links to evidence.

This is a format example, not a fresh test result. Record journey and expected-value
commit IDs, tool versions, relevant non-secret settings, and every retry/partial run
as well as the deployed product builds. In this public repository, commit sanitized
summaries; keep authenticated browser traces, videos and settings in approved restricted
run storage and link them for authorized reviewers. An evidence filename alone is not
proof that the file exists or is retained.

## Result page format

```text
results/
  <run-id>/
    result.json          # machine-readable verdict
    result.md            # human-readable summary
    evidence/            # copies of trace.zip, video, screenshots, database rows,
    traces/              #   call timelines, workbook — all named by check
    cleanup.md           # what was created and removed
```

### `result.md`

```markdown
# Run <run-id> — <date> <time UTC>

## Verdict

| Check | Result | Evidence |
|-------|--------|----------|
| Daily Outbound Interval: View for 2026-10-01 to 2026-10-07 | PASS | traces/doi-view-trace.zip |
| Daily Outbound Interval: Excel Check | FAIL | traces/doi-excel-trace.zip |
| Daily Outbound Interval: Download workbook | NOT RUN | (skipped: Excel Check failed) |

**Proposed verdict:** FAIL — 1 of 3 checks failed, 1 not run.
**Deployed builds:** Report Manager webapp: v2610.2845.01; Reports API: v2610.2837.02
**Environment:** Contoso (dev)  | **Persona:** admin
**Journey:** J1 Campaign Lifecycle  | **Maps:** daily-outbound-interval
**Journey / expected-values revisions:** <commit> / <commit>
**Tool versions / settings / retries:** <tool commits and versions>; <non-secret settings>; <partial run or retry details>

## Failures that can't be hidden

- Excel Check: the workbook's total attempts (142) did not match the on-screen grid
  (155). Trace: traces/doi-excel-trace.zip. Screenshot: evidence/doi-excel-screenshot.png.
  See also: ENG-644 (same class of defect — substituted data).

## Evidence links

- View trace: traces/doi-view-trace.zip
- View screenshot: evidence/doi-view-screenshot.png
- Excel Check trace: traces/doi-excel-trace.zip
- Download workbook: evidence/DailyOutboundInterval.xlsx
- Database rows: evidence/db-records.csv
- Run ID: 20261023T143215Z-j1-campaign-lifecycle
```

### `result.json`

```json
{
  "run_id": "20261023T143215Z-j1-campaign-lifecycle",
  "timestamp_utc": "2026-10-23T14:32:15Z",
  "journey": "J1 Campaign Lifecycle",
  "environment": "contoso",
  "persona": "admin",
  "journey_revision": "<commit>",
  "expected_values_revision": "<commit>",
  "tool_versions": { "ReportManager.E2E": "<commit>", "Playwright": "<version>" },
  "relevant_settings": {},
  "execution": { "partial": false, "retries": [] },
  "deployed_builds": {
    "nub_web_reportmanager": "v2610.2845.01",
    "nub_api_reports": "v2610.2837.02"
  },
  "checks": [
    {
      "name": "Daily Outbound Interval: View for 2026-10-01 to 2026-10-07",
      "result": "PASS",
      "evidence_path": "traces/doi-view-trace.zip"
    },
    {
      "name": "Daily Outbound Interval: Excel Check",
      "result": "FAIL",
      "evidence_path": "traces/doi-excel-trace.zip",
      "reason": "Workbook total (142) did not match grid (155)"
    },
    {
      "name": "Daily Outbound Interval: Download workbook",
      "result": "NOT_RUN",
      "reason": "Skipped: Excel Check failed"
    }
  ],
  "proposed_verdict": "FAIL",
  "cleanup_status": "COMPLETE — 4 records removed from campaign, agent logged out"
}
```

## Rules

- A skipped check cannot look green. If a check was not run, it says `NOT RUN` with the
  reason (missing prerequisite, environment down, etc.).
- A check that could not be made (tool broken, environment unhealthy) is `BLOCKED`,
  never a pass.
- A check that was made and saw the product do the wrong thing is `FAIL`.
- Fail or blocked results are pinned — they stay visible at the top of the page.
- The cleanup status is reported separately from the checks, so evidence survives
  teardown.
