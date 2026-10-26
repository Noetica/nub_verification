# Run 20261026T130500Z-verification-run — 2026-10-26

## Verdict

| Check | Result | Evidence |
|-------|--------|----------|
| Smoke: Real login as admin, dashboard loads with 12 report cards, no console errors | PASS | e2e-smoke.trx |
| AllReportCards_NavigateToTheirReports — all 12 cards reach their report | PASS | e2e-timing.log (lines 29-140) |
| AllReports_ListPickerOpensPopulatedAndCloses — picker opens/populated/closes on all 12 reports | PASS | e2e-timing.log (lines 141-262) |
| DataDrivenReports_AcceptInputsAndRender — Daily Outbound Interval renders grid | PASS (sub-check) | e2e-timing.log lines 266-276 (grid populated in 2.1s) |
| DataDrivenReports_AcceptInputsAndRender — Data Import grid does not populate | FAIL | failures/20261026-130903993-report-inputs/trace.zip |
| Export_DailyOutboundInterval_OffersPdfAndExcel | FAILED (cascade) | Stuck on dataimportreport page after Data Import failure |
| Export_DailyOutboundInterval_PdfDownloads | FAILED (cascade) | Same |
| Export_DailyOutboundInterval_ExcelDownloads | FAILED (cascade) | Same |
| OpenReportThenLogout_EndsSession | FAILED (cascade) | Same |

**Proposed verdict:** FAIL — 1 of 12 reports (Daily Outbound Interval) renders correctly.
The Data Import report's results grid never appears after clicking View Report (30s
timeout waiting for `.p-datatable-table-container`). This cascaded: all subsequent
tests share one browser session and were stuck on the Data Import page, causing 5
cascading failures.

**Deployed builds:** Not yet identified. The environment URL is
`https://contoso.dev.noeticacloud.com/ReportManager`. The `/api/version` endpoint should
confirm the build identity — this check was NOT run during this pass (the harness does
not call it; it is a Doctor-level check).

**Environment:** Contoso (dev) | **Persona:** admin | **Headless:** false

**Journey:** N/A (direct report verification) | **Maps:** daily-outbound-interval, data-import (pending)

## Failures that can't be hidden

- **Data Import report grid does not populate.** After entering date range
  `2026-01-01` to `2026-05-31` and selecting list `Paul > Campaign001 > george3`,
  clicking View Report left the page on `/dataimportreport` with no results grid.
  The test waits 30s for `.p-datatable-table-container` and times out. Trace:
  `failures/20261026-130903993-report-inputs/trace.zip`.
  This is a test-isolation issue as much as a product issue: the data-driven test
  loops all 12 reports in one session, so a failure at report N cascades through
  reports N+1 through 12. The Daily Outbound Interval report (the first one tested)
  rendered correctly in 2.1 seconds.

- **Cascading failures mask real results.** Tests 3-7 all failed with the same
  `UnexpectedUrl: expected /content, was /dataimportreport` because the shared
  session never returned to the dashboard after the Data Import failure.

## What this proves

1. The entire login flow works end-to-end against Contoso (admin, TOTP, MSAL popup).
2. The dashboard loads all 12 report cards (confirmed by `ContentPage: report card count = 12`).
3. Navigation works: all 12 cards can be opened and the report shell mounts.
4. List picker opens, populates, and closes on all reports.
5. Daily Outbound Interval specifically works: date entered, list selected, View Report
   clicked, grid populated in 2.1s.
6. Failure artifacts are captured automatically per failure (trace.zip, page.png,
   console.log, page-errors.log) — confirming the evidence pipeline works.
7. The existing Data Import report in `TestData/report-inputs.contoso.json` is dated
   `2026-01-01` to `2026-05-31` with list `Paul > Campaign001 > george3` — this data
   may not exist in the current Contoso tenant.

## Evidence links

- Smoke test trx: TestResults/e2e-smoke.trx (PASS)
- Verification trx: TestResults/e2e-verification.trx (2 pass, 5 fail, 15 skip)
- Timing log: TestResults/e2e-timing.log
- Failure artifacts:
  - failures/20261026-130903993-report-inputs/trace.zip (Data Import grid timeout)
  - failures/20261026-130909317-export-excel/trace.zip (cascade)
  - failures/20261026-130914470-export-options/trace.zip (cascade)
  - failures/20261026-130919601-export-pdf/trace.zip (cascade)
  - failures/20261026-130924741-logout-flow/trace.zip (cascade)
