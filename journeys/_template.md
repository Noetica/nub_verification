# Journey template

Copy this file for each new journey. Rename to the journey's kebab-case name.
Written in plain words — no code, no selectors, no SQL.

```markdown
---
name: J<n> <journey name>
status: draft
owner: Sandra (rewrite in your own words) — [drafted by, if not Sandra]
last_reviewed: YYYY-MM-DD
crosses: [Product A] [Product B] [Product C]
---

# Journey: <Name> (J<n>)

## What it proves

One or two sentences. The business outcome this journey validates end to end.

## Before you start

- **Tenant:** [Fabrikam for UAT, Contoso for local dev].
- **Reserved resources:** [campaigns, lists, agents, numbers — Kim names these].
- **Data file:** [the import file and its records' intended outcomes].
- **Prerequisites:** [what must be true — e.g. one agent logged in, TEFT ready].

## Steps

1. [Plain English action.]
2. [Plain English action.]
3. ... (number each step)

## Check

(Expected results written BEFORE any run, from the product rules, not from what
the system returns. Sandra's/Kim's numbers.)

| [Record / Item] | [Expected outcome] | [Expected attempts] | [Expected final state] |
|-----------------|-------------------|---------------------|----------------------|
| [data] | [data] | [data] | [data] |

[Additional text checks as needed. Each check says where it is seen: the call,
the agent's screen, the record's history, a report.]

## Evidence to keep

- [The result page (results/README.md)]
- [Each call's timeline]
- [Each record's history (database query)]
- [The report, on screen and in the workbook]
- [Deployed build identities for: Product A, Product B, ...]
- [One run ID that links records, calls, and evidence]

## Clean up

- [What to remove — records, campaigns, agents, files.]
- [What to leave — evidence, reference data.]
- [Do NOT reset the entire tenant.]

## Status

- **Legs that need Stream A:** [list TEFT outcomes not yet available]
- **Legs that work today:** [list what runs against existing tools]
- **The unattended version:** [what needs Stream A's simulated agent]
```
