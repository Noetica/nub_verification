# Jira Transition — Shared Resource

This file is included by `branch-from-jira`, `implement` and `create-pr`. It is a supporting resource, not a skill: it is never discoverable or invocable on its own.

## Purpose

Move a Jira card's status using the Atlassian Rovo MCP, with consistent fail-soft behaviour so the underlying git/PR action is never blocked by Jira issues.

## Inputs

- `<JIRA-KEY>` — e.g., `ENG-23`
- `<TARGET-STATUS-NAME>` — e.g., `In Progress`, `Peer Review`. Match by case-insensitive `name` on the transition's `to` status.

## Steps

1. Call `getTransitionsForJiraIssue` with the issue key.
2. Iterate the `transitions` array. Find the one whose `to.name` matches the target status (case-insensitive). The **ENG** workflow currently exposes:
   - `In Progress` (id 21)
   - `Peer Review` (id 51)
   - `Awaiting Verification` (id 61) — post-merge target (merged and on the dev/QA server; the verification team's pull queue), set automatically by the `notify-jira` CI leg, not by this interactive partial
   - `Verification` (id 71) — out of scope (a human verification step, not automated)
   - `Done` (id 31)
   - `To Do` (id 11), `Ready` (id 2), `Discovery` (id 41) — backward transitions, also out of scope

   Cards still **draining** in NUB (in-flight at the NUB→ENG cutover, keeping their NUB keys) expose the old NUB status names instead (`Deployment`, `Refined`, different ids). Matching is by name against what `getTransitionsForJiraIssue` actually returns for that card, so pass the name that exists on the card's own project and rely on fail-soft if it doesn't.
3. If a matching transition is found, call `transitionJiraIssue` with `{ "id": "<found-id>" }`.
4. Print a one-line confirmation: `✓ Jira <KEY>: → <Target Status>`.

## Failure handling — fail-soft

This partial **never blocks the caller**. The underlying git/PR action is the primary value; the Jira state move is gravy.

- **MCP unavailable** (no tool, network error): log `⚠ Jira transition skipped — Atlassian MCP not available` and continue.
- **Permission / workflow rule rejection**: log `⚠ Jira transition skipped — <reason>` and continue. Do not retry or escalate.
- **No matching transition** (target status not reachable from current state): log `⚠ Jira transition skipped — current state does not allow <Target>` and continue.

Failures here are advisory output, not errors. The caller proceeds to its next step regardless.

## Asymmetry with the fetch step

Note: this partial is the *transition* policy only. The fetch step in `branch-from-jira` (which needs the Jira card to derive the slug and branch type) has a different policy — **it refuses on failure** because the fetched data is essential input, not bonus output.
