---
status: stub
owner: Sandra (rewrite in your own words) — pending
last_reviewed: 2026-10-26
---

# Data Penetration

One paragraph describing the user-visible behavior of this feature. What a user
can do, what they see, what changes.

## Sub-features

- **view-for-range** — load the report for a chosen date range and see the results.
- **excel-check** — download the workbook and confirm the same totals are inside it.
- **download-workbook** — save the `.xlsx` file and open it to prove it is readable.

## How to get to it (user POV)

1. Report Manager -> Reports -> Data Penetration.

## Driving it with the harness

Preconditions: admin persona signed in at `/content`; Contoso environment has
known data for the agreed range (see `TestData/report-inputs.contoso.json`, keyed
by route `datapenetrationreport`).

- **View the report:**
  Command: `DataDrivenReports_AcceptInputsAndRender` (Category=Verification).
  Observable result: `.p-datatable-table` populated with real rows; no console errors.

- **Run the Excel Check:**
  Command: `Export_DataPenetration_ExcelDownloads` (via `ExcelTestReader.ReadRows`).
  Observable result: workbook header + first 20 rows match the grid cell-by-cell.

- **Download the workbook (PDF):**
  Command: `Export_DataPenetration_PdfDownloads` (via `PdfTestReader.ReadAllText`).
  Observable result: non-empty `.pdf` containing report title + first-row values.

- **Export menu offers both options:**
  Command: `Export_DataPenetration_OffersPdfAndExcel`.

## Gotchas

- An empty-state row with no error still means the report failed.
- The deployed builds must be the ones the card names.

## Expected results (pre-agreed, before any run)

Pending Sandra's input. Draft values go here once agreed.
