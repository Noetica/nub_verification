# Verification agent guidance

This is an unfinished ENG-824 PoC. Start with `HANDOVER.md`, `DECISIONS.md` and the
canonical spec/grill record they link. The current progress snapshot is descriptive;
it does not approve unfinished functionality or waive acceptance gates.

## Connect

Tests run against Contoso first for development feedback. Fabrikam is the final
evidence and verification environment. Read `environments/fabrikam.md`; obtain the
card's expected website/API builds and agreed synthetic test data before driving.
Use the existing Report Manager harness in the owning product repository. Credential
sources are named in the environment guide; retrieve their values at runtime without
printing them. Do not commit local settings or session artifacts containing secrets.

## Doctor

`tools/doctor/fabrikam.ps1` is incomplete. Exit 0 means GO; exit 1 means a failed
check; exit 2 means a blocked prerequisite. Both failure and blockage stop driving.
A reachable site alone is not readiness. Check exact deployed builds, authentication,
approved data, reserved tenant resources and relevant dependencies.

Sarah's current `nub_devops/Powershell/Stand Up/Test-TenantFunctional.ps1` takes a
settings file and selected functional steps. It does not accept `-Only Conformance`,
`-Environment` or `-Persona`. The existing wrapper does not yet integrate its result.
Use supported interfaces only, consult Sarah before changing her work, and do not
report the integration as passing because a script path exists.

## Drive

Follow `.agents/skills/scenario/SKILL.md`. Fetch the user's named card through the
available Jira connector, read its How to verify section and select the matching map
or journey. Missing instructions or unavailable tools produce BLOCKED/NOT RUN checks.

The existing product harness is `nub_web_reportmanager/tests/ReportManager.E2E/`.
The prior baseline used `dotnet test` with Category=Smoke and Category=Verification;
confirm current project guidance before choosing the command for a new run. Do not
copy its page objects or tests into this repository. Database scripts under `tools/db/`
are agreed scope but not implemented; do not substitute invented tables or free-form SQL.
Sarah's earlier write tests were removed, so they cannot be assumed available for setup.

The first J1 live-answer leg can use a human agent. Busy, no-answer, voicemail,
number-based outcome selection and unattended agent operation need Stream A support;
keep unsupported legs visible. Do not implement new TEFT tooling here.

## Evidence

Follow `results/README.md`: per-check PASS/FAIL/BLOCKED/NOT RUN, exact website/API builds,
environment, UTC time, run ID, journey/expected-values commit, tool versions, settings,
partial runs/retries and cleanup outcome. Keep video and Playwright trace for every
browser step, pass or fail. Verify that the files exist before linking them.

Report Manager PR #267 adds skip-gate failure and evidence retention but is OPEN as of
the consolidated snapshot. Its failed smoke preflight proves missing configuration
is visible in that PR; it does not prove successful video/trace retention or activation
on main. Recheck GitHub status before relying on that change.

The saved Contoso baseline has one smoke pass, two passed verification tests, five
failed verification tests and fifteen unexecuted tests. Daily Outbound's populated grid
is a subcheck inside a failing test, not full report verification. Deployed builds were
not identified. Preserve that result and its `audit.md`; do not silently relabel it green.

## Cleanup

Remove only resources created by the run using the product's supported operations.
Keep proof artifacts; do not reset the shared tenant or remove existing reference data.
During verification, never edit product code, change expected outcomes to fit observed
results, or move Jira status. Prepare a proposed verdict for the human. Post a Jira
summary only when the verification request authorizes it; never post during a read-only
audit or this consolidation.
