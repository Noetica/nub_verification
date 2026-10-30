---
name: verify-journey-mini-journey-teft
description: J2 — Mini journey with TEFT. Queue four test records and a control, let one simulated agent take the dialler's calls, and compare each record's outcome with what was expected.
status: draft
owner: Ian Harrison (Kim or Sandra check the expected values at the handover)
last_reviewed: 2026-10-30
crosses: [Queue API] [Predictive dialler] [Voice platform] [TEFT] [TEFT runner]
---

# Journey: Mini journey with TEFT (J2)

## What it proves

Records queued through the Queue API, each with a different customer behaviour, are dialled by
the real dialler. Only the customer who answers in person reaches the agent, and each record ends
in the state the campaign's rules say it should.

## Before you start

- **Tenant:** Ian's dev tenant `ianh` on DEV-IANH, with its dialler, Kamailio and Ian's own TEFT
  and runner. Never the shared telephony-testing VM, and never a production tenant.
- **Campaign:** the journey's test campaign on `ianh`. The simulated agent's user is a member of
  it, and the campaign has an active call result called "Completed". The dialler is running.
- **Records:** five, each on the journey's own list:
  1. a customer who answers in person after a short ring
  2. a customer who's busy
  3. a customer who lets it ring and never answers
  4. an answering machine with a greeting and a beep
  5. **the control:** a customer who's busy, written down below as if they answer in person.
     Its check must fail. If it passes, the run is not valid.
- **Tools:** `teft` installed and signed in (the `teft` skill), and the Queue API reachable.
  TEFT's status shows it connected.
- **Expected values:** written in the Check table below before the first run.

## Steps

1. Check the tools are ready: TEFT is connected, the runner answers for `ianh`, and the
   deployed builds are the ones the card names.
2. Ask TEFT for each record's number: the customer behaviour, and a different sequence for each
   record.
3. Log one simulated agent into the campaign, giving it the five numbers.
4. Queue the five records through the Queue API. Keep each record's ID.
5. Let the dialler call them. Every few seconds, read each record's history.
6. When every record's call has ended and its history shows a final state or a time it is due
   again, stop the agent. If ten minutes pass first, the agent logs itself out, and the checks of
   records that haven't got that far are **blocked**.
7. Read the agent's session: the calls it took, and TEFT's call log for each number.
8. Read each record's history and final state.

## Check

Expected results, written before any run from the campaign's rules, not from what the system
returns. Ian fills these in before the first run; Kim or Sandra check them at the handover.

| Record | Customer | Expected outcome | Reaches the agent | Expected attempts | Expected final state |
|---|---|---|---|---|---|
| 1 | answers in person | [live answer] | yes | [1] | [completed] |
| 2 | busy | [busy] | no | [1] | [due again after the campaign's busy delay] |
| 3 | never answers | [no answer] | no | [1] | [due again after the campaign's no-answer delay] |
| 4 | answering machine | [answering machine] | no | [1] | [per the campaign's answering-machine rule] |
| 5 (control) | busy | live answer | yes | 1 | completed |

- Each record was called the expected number of times (the record's history).
- Only record 1 reached the agent, and the agent wrapped it up as completed (the agent's session).
- Each record's call behaved as its customer says (TEFT's call log for its number).
- Each record's history shows the expected outcome and final state (the record's history).
- Record 5's check fails. If it passes, the result page says the run is not valid.
- If TEFT is down, its checks are blocked, never passed.

## Evidence to keep

- The run's result page (see `results/README.md`), with one row per record.
- For each record: its TEFT call log and its attempt history, linked from its row.
- The agent's session: when it started and ended, why it ended, and the calls it took.
- The deployed builds of TEFT, the runner, the dialler and the voice platform.
- One run ID that links the records, the agent session and the evidence.

## Clean up

- Stop the agent, if it is still running.
- Take the five records out of the queue.
- Leave the evidence, the campaign and the list.
- Don't reset the tenant.

## Status

- **Legs that work today:** queueing through the Queue API (route 1), TEFT's customer behaviours
  by number, one simulated agent that stays ready (route 1).
- **Legs to verify on DEV-IANH:** the first end-to-end run; how the dialler presents a Queue API
  number to TEFT; that the agent gets the next call after each wrap-up.
- **Next:** Ian fills in the expected values; Kim or Sandra check them.
