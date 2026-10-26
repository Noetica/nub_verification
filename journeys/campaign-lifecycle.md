---
name: verify-journey-campaign-lifecycle
status: draft
owner: John Girardi
reviewers: [Kim, Sandra]
last_reviewed: 2026-10-26
expected_values_status: pending Kim agreement
crosses: [Campaign Manager, Dialler, Voice Platform, Reports API, Report Manager]
---

# Journey: Campaign Lifecycle (J1)

## What it proves

A small set of synthetic records ends with the agreed calls, retries, record history,
final states and report totals. This is a draft for Sandra to review; it has not been
run and accepted as a complete journey.

## Before you start

- Run development checks on Contoso first; final evidence and verification use Fabrikam.
- Kim names the reserved campaign, list, agent and telephone numbers and agrees the
  intended result for each synthetic record. Those details are still pending.
- Prepare and agree the small import file. No agreed file is supplied by this draft.
- Confirm that the intended builds are deployed and the environment is ready.
- A person can take the live-answer call with today's tools. Busy, unanswered,
  voicemail and unattended-agent legs need the corresponding Stream A support;
  keep those legs visibly blocked until it exists.

## Steps

1. Import the agreed records into the reserved list through the product.
2. Check that the selected records are queued and have not already been dialled.
3. Let the dialler call the live-answer record and have the reserved agent take it.
4. When Stream A supports them, exercise the agreed busy, unanswered and voicemail
   cases. Until then, mark those steps blocked rather than substituting outcomes.
5. Retry the agreed record after the campaign's agreed delay, when that leg is supported.
6. Check the selected records' history and final states, then compare the report with
   the totals agreed before the run.

## Check

The following expectations are awaiting Kim's agreement. They are not Sandra's
approved values and must not be filled in from what the application happens to return.

| Record role | Expected calls/attempts | Expected final state/retry | Seen in |
| --- | --- | --- | --- |
| Live-answer record | Kim to agree | Kim to agree | Call evidence, agent screen, record history |
| Busy record — needs Stream A | Kim to agree | Kim to agree | Call evidence and record history |
| Unanswered/retry record — needs Stream A | Kim to agree | Kim to agree | Attempt history and final state |
| Voicemail record — needs Stream A | Kim to agree | Kim to agree | Call evidence and record history |
| Report totals | Kim to agree | Kim to agree | Daily Outbound Interval and its workbook |

The four named database-read tools needed for the record checks are agreed scope but
not implemented. Their checks remain blocked. Record Kim's agreement and date before
accepting final evidence; Sandra reviews the wording on her return.

## Evidence to keep

Keep one readable result page with pass, fail, blocked or not run for every required
check, including the legs that could not run. Identify the environment and all relevant
deployed builds, the journey/expected-values revision, tool versions, UTC time and run ID.
Link the call evidence, record observations, report and workbook, plus a screen recording
and trace for every browser step on success and failure. Contoso results are preliminary;
accepted final evidence must come from Fabrikam.

## Clean up

Remove only the records created for this run through supported product operations,
log out its agent and release its reserved resources. Retain the evidence. Report
cleanup separately and never reset the shared tenant.

Crosses: Campaign Manager, Dialler, Voice Platform, Reports API and Report Manager.
