# Jira Sprint Membership — Shared Resource

This file is included by `branch-from-jira`, `implement` and `create-pr`. It is a supporting resource, not a skill: it is never discoverable or invocable on its own.

## Purpose

Ensure a card being actively worked on is in the **active sprint**, so it always shows on the board and in burndown. Devs routinely forget to pull cards in, and an advisory reminder is ignored in practice, so the skills edit sprint membership themselves — **automatically, not as a prompt**. It is a mechanical side effect of the calling skill, not a card edit that needs a go-ahead (`SHARED-AGENT-GUIDANCE.md` § Jira § Conventions).

Called from more than one point on purpose. Sprint membership is **idempotent** — case 1 below is a no-op — so running it again on a card already in the sprint costs one read and prints one line. The redundancy is the point: `branch-from-jira` covers cards whose work starts with a new branch, `implement` covers resumed work on an existing branch, and `create-pr` is the catch-all for cards that reached a PR without ever passing through either (manual branch, work begun before these skills existed, the second repo of a multi-repo card).

## Inputs

- `<JIRA-KEY>` — e.g. `ENG-240`. `<PROJECT>` below is the key prefix before the dash, e.g. `ENG`.

## Steps

0. **Off-sprint card** — the card carries the `offsprint` label, which marks work deliberately kept outside any sprint. The skip applies to any card with that label, in any repository; `nub_model_repository`'s own cards carry it. Skip the rest; print `✓ Sprint: skipped — offsprint card`. Take the labels from the caller's earlier `getJiraIssue` response, re-fetching with `labels` if it lacks them. If they cannot be read, print `⚠ Sprint: couldn't read labels — <reason>; sprint left unchanged. Unless it is an offsprint card, pull <JIRA-KEY> into the active sprint in Jira.` and skip the rest, so an off-sprint card is never moved on a guess.

**Still in Discovery** — a Discovery card stays out of the live sprint. Take the card's current status from the caller: the target of a transition it has just applied, otherwise the status in its earlier `getJiraIssue` response (re-fetch with `status` only if neither is known). If that status is `Discovery`, the caller's transition did not apply: skip the rest and print the fail-soft advisory below with the reason `<JIRA-KEY> is still in Discovery`, adding `Move it forward in Jira first.`

Otherwise read the card's Sprint field (`customfield_10020`, the instance-wide Sprint field). If the caller's earlier `getJiraIssue` response did not include it, re-fetch with `fields` including `customfield_10020`.

1. **Already in the active sprint** — `customfield_10020` has an entry with `state: "active"`. No-op; print `✓ Sprint: already in current sprint`.

2. **Not in the active sprint** (field empty → backlog; or entries exist but none `active` → in a future/closed sprint). **Move it into the active sprint:**
   - **Find the active sprint id.** There is no board/sprint MCP tool, so probe via JQL: call `searchJiraIssuesUsingJql` with `project = <PROJECT> AND sprint in openSprints()`, requesting `fields: ["customfield_10020"]`. From any returned issue, take the `customfield_10020` entry with `state: "active"` and read its `id`. If the search returns nothing (no open sprint, e.g. between sprints or a board with no active sprint), skip to the fail-soft branch below.
   - **Set it.** Call `editJiraIssue` on `<JIRA-KEY>` setting `customfield_10020` to that sprint id. This **moves** the card — a card sitting in a future/closed sprint is reassigned to the active one (intended: you're working on it now).
   - On success print `✓ Sprint: added to current sprint <name-or-id>`.

## Failure handling — fail-soft

This partial **never blocks the caller**, exactly like `.agents/shared/jira-transition.md`. Whatever the caller was doing (creating a branch, implementing, opening a PR) has already happened or is the primary value; sprint membership is bookkeeping.

If the active sprint id can't be determined, or `editJiraIssue` rejects the field (some Jira configs only honour the Agile move-to-sprint endpoint for this — the MCP may not expose it), print the advisory fallback and continue, so the dev can finish the job by hand:

> ⚠ Sprint: couldn't add `<JIRA-KEY>` to the current sprint automatically (`<reason>`). Pull it into the active sprint in Jira so it shows on the board and in burndown.

## Scope

**Epics are out of scope.** Epics are not sprint members — they span sprints and their children carry the sprint. `branch-from-jira` already refuses on Epic before reaching this partial; callers that can be handed an Epic key should skip this partial rather than sprint it.
