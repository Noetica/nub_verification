# Feature map template

Copy this file for each new feature. Rename to the feature's kebab-case name.
Fill in Sandra's words — no code, no selectors, no SQL.

```markdown
---
status: draft
owner: Sandra (rewrite in your own words) — [name of drafter, if not Sandra]
last_reviewed: YYYY-MM-DD
---

# <Feature Name>

One paragraph describing the user-visible behavior of this feature. What a user
can do, what they see, what changes.

## Sub-features

- **view** — [one line: what the view does]
- **excel-check** — [one line: what the Excel Check validates]
- **download** — [one line: what the download provides]
(Add or remove sub-features as appropriate.)

## How to get to it (user POV)

1. Main menu -> submenu -> feature name.
2. (Alternative entry point: e.g. a link from another report.)
3. (Alternative entry point: e.g. a deep link with parameters.)

## Driving it with the harness

Preconditions: [state what must be true before driving — e.g. signed in as admin,
the data file is imported, the date range is set].

- **View the report for the known range:**
  [Action] Open the feature. [Action] Set the date/range. [Action] Click View Report.
  [Result] Expect the grid to populate with [expected rows/columns]. [Result] Expect
  the totals row to match [pre-agreed values].
  Command: [name the Playwright test or harness operation, not a selector].
  Observable result: [.p-datatable grid populated, no console errors].

- **Run the Excel Check:**
  [Action] Click Excel Check. [Result] The workbook opens and the totals match the
  screen.
  Command: [ExcelTestReader.cs compares workbook against grid].
  Observable result: [workbook opens, totals match].

- **Download the workbook:**
  [Action] Click Download. [Result] The file saves and opens in Excel.
  Command: [the harness saves to results/<run-id>/downloads/].
  Observable result: [file exists, non-empty, header + first rows match].

## Gotchas

- **An empty-state row with no error still means the report failed.** [Why this
  matters and what to check instead.]
- **The deployed API and website builds must be the ones the card names.** Doctor
  checks this first.
- **[Feature-specific trap #3]:** [what usually goes wrong here.]
- **[Feature-specific trap #4]:** [what usually goes wrong here.]

## Expected results (pre-agreed, before any run)

Pending Sandra's input. Draft values go here once agreed:

- [Metric]: [to be agreed with Sandra]
- [Metric]: [to be agreed with Sandra]
```
