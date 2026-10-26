# Report Manager skip-gate and evidence work

Snapshot: 26 Oct 2026. [PR #267](https://github.com/Noetica/nub_web_reportmanager/pull/267)
is **OPEN**, at `8d55c0073d8ae332af4476fe879b5c3328b9b00a`; it has not landed on main.
This is the existing ENG-645 product-harness work, not a second implementation in
`nub_verification`. The merged verification-repo PR #1 only documented this PR.

## What the branch implements

- `.github/workflows/e2e-smoke.yml` and `e2e-verification.yml` remove the job's
  skip-on-missing-variables gate and add an explicit failing preflight. It requires
  `E2E_RUNS_ON`, `E2E_KEYVAULT_NAME`, `E2E_DEV_BASE_URL` and `E2E_DEV_LOGIN_URL`.
- Both workflows upload artifacts on `always()`, instead of failure only.
- `tests/ReportManager.E2E/Fixtures/AuthFixture.cs` sets
  `BrowserNewContextOptions.RecordVideoDir` when creating the authenticated context.
- `tests/ReportManager.E2E/Support/PageObservation.cs` saves successful traces under
  `TestResults/traces/`, preserving the failure-artifact path separately.

Use the actual branch code and owning repository guidance; the earlier illustrative
`RecordVideo` property and guessed fixture APIs are not implementation instructions.

## What has been demonstrated

The PR's [smoke workflow run](https://github.com/Noetica/nub_web_reportmanager/actions/runs/40335002616)
failed because all four required variables were missing. That proves visible
configuration blockage in this run; it does not demonstrate a successful browser
execution, video finalization, retained pass traces or activation on main.

The separate local Contoso baseline predates final verification and failed overall.
Its observed grid is not proof of agreed totals, exports or final Fabrikam acceptance.

## Remaining work in ENG-645

Resolve the approved runner, Azure/vault access and environment URL prerequisites;
review and merge through the owning repository's normal process; run on Contoso
before final Fabrikam verification. Demonstrate evidence for successful and failed
browser steps, retained videos after context shutdown, exact deployed website/API
builds, and visible skipped/blocked required coverage. Preserve current failures and
do not expand ENG-824 into an isolation refactor or fixture-data repair.
