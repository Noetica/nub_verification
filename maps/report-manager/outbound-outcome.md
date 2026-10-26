---
status: stub
owner: Sandra (rewrite in your own words) — pending
last_reviewed: 2026-10-26
related: [[daily-outbound-interval]]
---

# Outbound Outcome

## View

One paragraph describing the user-visible behavior of this feature. What a user can do,
what they see, what changes.

## How to get to it

1. Main menu -> Reports -> Outbound Outcome.

## Pre-conditions

- Signed in as admin.
- Date range set.
- Campaign data imported for the range.

## Expected results (pre-agreed, before any run)

Pending Sandra's input. Draft values go here once agreed:

- [Grid total attempts]: [to be agreed]
- [Workbook total attempts]: [to be agreed]
- [Final state distribution]: [to be agreed]

## Gotchas

- **ENG-644 regression.** This report's underlying SQL adapter was exercised by API tests
  that used substituted data, not the real SQL adapter. The verification check must hit
  the real SQL adapter. The adapter should be driven directly, not through a substituted
  data layer.

## Driving it with the harness

- **View:** [Action] Open Outbound Outcome. [Result] Grid populates.
- **Excel Check:** [Action] Click Excel Check. [Result] Workbook totals match the screen.
- **Download:** [Action] Click Download. [Result] File saves and opens.

## Status

- **Legs that need Stream A:** [list TEFT outcomes]
- **Legs that work today:** [list what runs against existing tools]
- **The unattended version:** [what needs Stream A's simulated agent]

## Clean up

- [List what to remove]
