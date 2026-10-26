# Feature map: Report Manager

This directory is the maintained source for verifying the user-facing behavior of Report Manager.
Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- The verification skill (`AGENTS.md`) at the repo root has been followed: secrets are in the
  environment, the target environment URL is set, and Doctor has passed.
- The `admin` persona is signed in to `/content` (the dashboard of report cards).
- Test data for each data-driven report is in `TestData/report-inputs.<env>.json` in
  `nub_web_reportmanager/tests/ReportManager.E2E/` (currently `contoso` and `fabrikam`).
- `ReportCatalog.cs` lists the 12 dashboard reports in render order.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say otherwise.
- Prefer ARIA roles and accessible names over CSS selectors or DOM position.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Run browser actions through Playwright (the harness drives a real browser).
- Run terminal actions through `pwsh scripts/run-e2e-tests.ps1` or `dotnet test`.
- Restore seeded data after a mutation. Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final screen.
- UI proof includes an ARIA snapshot, a screenshot, the console log, and a trace.
- Report proof includes the command, stdout, stderr, and exit code.
- Mutation proof includes a read-only second view of the stored value.
- Record the feature ID and entry point used with every artifact.
- Report an unreachable path with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible
behavior. It then uses exactly four H2 sections in this order.

1. `## Sub-features` — short IDs with one line for each behavior.
2. `## How to get to it (user POV)` — every user entry point.
3. `## Driving it with the harness` — labeled bullets pairing each user action with an
   exact command and observable result.
4. `## Gotchas` — traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles,
required state, commands, and observable proof.

| Report | Status | Route | Tests |
|--------|--------|-------|-------|
| Daily Outbound Interval | VERIFIED (2026-10-26) | `dailyoutboundintervalreport` | Grid populated 2.1s, no errors |
| Outward Outcome | stub (ENG-644 regression) | `outboundoutcomereport` | Pending |
| Data Import | stub (cascading failure observed) | `dataimportreport` | Grid did not populate (30s timeout) |
| Data Penetration | stub | `datapenetrationreport` | Pending |
| Monthly Outbound Interval | stub | `monthlyoutboundintervalreport` | Pending |
| Outbound Calls Data | stub | `outboundcallsdatareport` | Pending |
| Agent Breaks | stub | `agentbreaksreport` | Pending |
| Email SMS Data | stub | `emailsmsdatareport` | Pending |
| Daily Agent Productivity | stub | `dailyagentproductivityreport` | Pending |
| Campaign Performance | stub | `campaignperformancereport` | Pending |
| Campaign Performance by Hour | stub | `campaignperformancebyhourreport` | Pending |
| Data Penetration Extended | stub | `datapenetrationextendedreport` | Pending |

All 12 dashboard reports have feature-map stubs. Daily Outbound Interval is the
first verified; Data Import is the first failure (grid did not populate in the
shared session, cascading through the remaining tests).
