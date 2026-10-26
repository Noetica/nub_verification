---
status: draft
owner: Sandra (rewrite in your own words) — currently drafted by John
last_reviewed: 2026-10-23
---

# Daily Outbound Interval

The report shows how many outbound calls were attempted in a chosen time period, broken
down by day, with totals you can check in Excel and download as a workbook.

## Sub-features

- **view-for-range** — load the report for a chosen date range and see the daily totals.
- **excel-check** — download the workbook and confirm the same totals are inside it.
- **download-workbook** — save the `.xlsx` file and open it to prove it is readable.

## How to get to it (user POV)

1. Report Manager -> Reports -> Daily Outbound Interval.
2. The date range picker appears at the top of the page.
3. For a different range: change the picker and click View Report.

## Driving it with the harness

Preconditions: the admin persona is signed in at `/content`; the Contoso environment has
known data for the agreed date range (see `TestData/report-inputs.contoso.json`, keyed
by the route `dailyoutboundintervalreport`, date `2025-12-29`, list `sandra > EMAIL > list01`).

- **View the report for the known range:**
  Open the Daily Outbound Interval report. In the date picker, enter the agreed date
  and tick the agreed list path. Click View Report. Expect the results grid to populate
  with data rows.
  Command: `DataDrivenReports_AcceptInputsAndRender` (Category=Verification).
  Observable result: `.p-datatable-table` populated with real rows; no browser console
  errors.

- **Run the Excel Check:**
  Click Export -> Excel. Expect a download of a `.xlsx` workbook whose header and first
  20 rows match the on-screen grid cell-by-cell.
  Command: `Export_DailyOutboundInterval_ExcelDownloads` (which calls
  `ReportPage.AssertExcelMatchesGridAsync` via `ExcelTestReader.ReadRows`).
  Observable result: workbook opens in ExcelDataReader; no cell mismatches.

- **Download the workbook (PDF):**
  Click Export -> PDF. Expect a non-empty `.pdf` whose text contains the report title
  plus distinctive first-row values.
  Command: `Export_DailyOutboundInterval_PdfDownloads` (which calls
  `ReportPage.AssertPdfContainsGridDataAsync` via `PdfTestReader.ReadAllText`).

- **Export menu offers both options:**
  Open the Export menu. Expect both PDF and Excel options visible.
  Command: `Export_DailyOutboundInterval_OffersPdfAndExcel`.

## Gotchas

- **An empty-state row with no error still means the report failed.** If the grid loads
  but shows zero rows without a data error, the report is silently broken. The check must
  assert non-empty data, not just navigation success.
- **The deployed API and website builds must be the ones the card names.** Doctor checks
  this first; a mismatch is a stop, not a test run.
- **ENG-644 pattern:** a report that looks right but was produced by substituted data is
  not evidence. Daily Outbound Interval's SQL adapter must be the real one. If the
  backend is mocked or the data is fabricated, the check must fail.
- **Date ranges must come from known, agreed data.** Do not pick a range at random; the
  expected totals must be pre-agreed by Sandra/Kim from product rules, not read from
  whatever the system returns on the day.
- **Off the allow-listed environments (contoso, fabrikam), the data-driven checks skip
  entirely.** A skipped check is not a pass.

## Expected results (pre-agreed, before any run)

Pending Sandra's input. For the PoC, draft values:
- Date range: 2026-10-01 to 2026-10-07 (one week).
- Total attempts: [to be agreed with Sandra].
- Total live answers: [to be agreed with Sandra].
- Total no answers: [to be agreed with Sandra].
- Workbook row count: [to be agreed with Sandra].
