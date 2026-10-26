# Reconciliation of the preserved Contoso baseline

Audited 26 Oct 2026 during the Hermes/Codex consolidation. The original `result.json`
and `result.md` are preserved as historical records; this note clarifies their limits.

- `e2e-smoke.trx` records **1 test, 1 passed**.
- `e2e-verification.trx` records **22 total, 7 executed, 2 passed, 5 failed**;
  its result entries include **15 NotExecuted** tests.
- Daily Outbound Interval's populated grid was a successful observation inside the
  data-driven test that later failed at Data Import. It is not an extra passed xUnit test.
  The original JSON mixes observation counts with test totals; do not add them together.
- Of the five failed verification tests, Data Import is the initial observed failure
  and four later tests failed after the shared page remained on that report. The root
  cause of Data Import is still unconfirmed; stale fixtures are a hypothesis.
- The baseline did not identify deployed builds, agree report totals, or prove the
  workbook checks. It is preliminary Contoso evidence and cannot satisfy final
  Fabrikam acceptance or establish the whole Daily Outbound feature as verified.
- Raw TRX and browser files are held locally in the product checkout's
  `tests/ReportManager.E2E/TestResults/`. Paths in the historical result are not proof
  that portable copies exist in this repository. Do not publish raw authenticated
  traces or settings while consolidating this public repository.

See `consolidation-status.json` at the repository root for the source file hashes,
the PR snapshots and the next steps. No live tenant tests were rerun in this audit.
