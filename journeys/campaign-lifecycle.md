---
name: verify-journey-campaign-lifecycle
description: J1 — Campaign Lifecycle: import, queue, dial, record outcome, check history and report.
---

# Journey: Campaign Lifecycle (J1)

## What it proves

A small file of records with distinct intended outcomes ends in the attempt history,
final states, retries, and report totals agreed before the run.

## Before you start

- **Tenant:** Fabrikam (or Contoso for local PoC without telephony).
- **Reserved resources:** one campaign, one list, one agent (Kim names these on the
  kickoff; see `environments/fabrikam.md`).
- **Data file:** `TestData/j1-records.csv` — four records, each with a distinct intended
  outcome (live answer, busy, no answer, voicemail). The agent uses the real Campaign
  Manager import, never SQL that manufactures the result.
- **Agent:** one simulated or real agent logged in and ready (the TEFT runner's simulated
  agent plays this today; Stream A's SAIL agent-side layer can take over when it lands).

## Steps

1. Import the data file into the reserved campaign. Every record has an intended outcome
   chosen by its number (per TEFT's number-range routing, once Stream A delivers it; for
   the PoC, the outcomes are pre-seeded in the data).
2. Wait for the queue to build. The database shows every record queued and none dialled.
3. Let the dialler call them. TEFT answers each call the way the number says: live answer,
   busy, no answer, voicemail. An agent is logged in through the harness.
4. One record is not answered first time, becomes eligible again after the configured
   recycling interval, then completes.
5. Outcomes and recycling. The database shows the attempt history and final state of
   every record.
6. Daily Outbound Interval -> maps/report-manager/daily-outbound-interval.md, expecting
   the totals below.

## Check

(Expected results written before any run, from the product rules, not from what the
system returns. Sandra's numbers.)

| Record | Expected outcome | Expected attempts | Expected final state |
|--------|-----------------|-------------------|---------------------|
| 1 | live answer | 1 | completed |
| 2 | busy | 1 | retry-eligible after busy delay |
| 3 | no answer | 2 (one retry) | completed |
| 4 | voicemail | 1 | completed |

- Each record was called the expected number of times.
- No call reached the agent except record 1 (the live answer).
- The busy and no-answer records are due again after the campaign's configured delays.
- Each record's history shows its attempt(s) with the correct outcome code.
- The Daily Outbound Interval report shows the expected totals (see the feature map
  entry for the agreed values).

Each check says where it is seen: the call timeline (TEFT results), the agent's screen
(Campaign Manager), the record's history (database), and the report (Report Manager).

## Evidence to keep

- The run's result page (see `results/README.md`).
- Each call's timeline (from TEFT's results API).
- Each record's history (from the read-only database queries in `tools/db/`).
- The Daily Outbound Interval report, on screen and in the workbook.
- Deployed build identities for: Campaign Manager, the dialler, the voice platform,
  Reports API, Report Manager.
- One run ID that links the records, calls, and evidence.

## Clean up

- Take the four records out of the campaign.
- Log the agent out.
- Release the reserved campaign, list, and agent resources.
- Do not reset the entire tenant; remove only what this run created.

## Status

- **Legs that need Stream A:** busy, no answer, answering machine (voicemail), number-range
  routing. Mark these *needs stream A* and link Stream A's outcome catalogue once published.
- **Legs that work today:** live answer (someone takes the predictive call), queue build
  (database check), report totals (Report Manager).
- **The unattended version** (simulated agent plays the agent side on every call) needs
  Stream A's A6. Mark *needs stream A*.

## Next actions

1. Draft this journey with Kim: agree the expected results and the data file.
2. Mark the Stream A-dependent legs and link its outcome catalogue.
3. Write the database read queries (`tools/db/`) that this journey's checks need.
4. When Stream A lands, run end to end on Fabrikam.
