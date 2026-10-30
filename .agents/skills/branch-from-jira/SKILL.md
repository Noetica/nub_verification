---
name: branch-from-jira
description: Create a correctly named git branch from a Jira card and move the card to In Progress. Use when asked to branch from a card, start a card, or make a branch for a Jira key.
---

# Branch From Jira

Create a git branch tied to a Jira card with consistent naming and a side-effect Jira state transition. Operationalises the workflow in `../nub_specs/specs/2026/nub-2094-skill-to-create-branch-from-jira/spec.md`.

## Inputs

- A single Jira issue key argument, e.g. `ENG-23`. The argument is the only context — do not attempt to infer the key from the current branch or unrelated chat history.

## Goals

- Always branch from a fresh `origin/main` so devs never start work on stale local state.
- Enforce the team's branch naming convention without forcing devs to memorise it.
- Move Jira state forward (`To Do → In Progress`) as a side effect so cards don't drift.
- Add the card to the current (active) sprint automatically, so cards being worked on always show on the board and in burndown — devs no longer have to remember to pull them in. A card labelled `offsprint` is skipped by design; that is a success, not a failure. Fail-soft: if it can't, fall back to an advisory.
- If the card's spec is published on `nub_specs` `main`, attach a one-time Jira backlink comment so the card points at the spec.

## Steps

### 1. Validate the argument

The argument must match `[A-Z]+-\d+` (e.g., `ENG-23`). If not, refuse with a one-line example. Do not call the MCP.

**Refuse in `nub_specs`.** If this repository is `nub_specs` (identified as `SHARED-AGENT-GUIDANCE.md` § Reading other repositories defines), stop before calling the MCP, creating a branch or moving the card. `nub_specs` takes every change directly on `main` and its ruleset rejects branch creation (`SHARED-AGENT-GUIDANCE.md` § Reading other repositories):

> ✗ `nub_specs` takes changes directly on `main` — no branch. Commit and push the spec or ADR to `main`; implementation branches belong in the code repository that owns the work.

### 2. Fetch the Jira card — refuse on failure

Call `getJiraIssue` with the key. **This is essential input, not bonus output.** If the call fails (MCP unavailable, network error, auth expired, key not found), refuse the whole operation and print:

> ✗ Jira unreachable — cannot fetch `<KEY>`.
>
> This is usually an Atlassian MCP setup issue. See `nub_documents/engineering/Claude/using-claude.md` for setup.
>
> If Jira itself is down and you need to ship now:
> `git fetch origin main && git switch -c <type>/<KEY>-<your-slug> --no-track origin/main`
>
> Re-run `branch-from-jira <KEY>` once Jira is back to capture the In-Progress transition.

Do not silently fall back to a manual slug prompt. The refusal is deliberate — masking MCP misconfiguration with a manual workaround lets it drift indefinitely.

### 3. Refuse on Epic

If `fields.issuetype.name == "Epic"`, refuse:

> ✗ `<KEY>` is an Epic. Epics shouldn't have direct branches.
>
> Pick a child Story/Task/Bug and run `branch-from-jira <child-key>` instead.

### 4. Derive the branch name

Format: `<type>/<KEY>-<kebab-slug>`.

`<type>` mapping from `fields.issuetype.name`:

| Jira issue type | Branch prefix | Notes |
|---|---|---|
| Story, Task | `feature` | Default for net-new work. |
| Bug | `bugfix` | |
| Spike | `chore` | |
| Subtask | inherit parent's mapped prefix | Read `fields.parent.fields.issuetype.name` from the same `getJiraIssue` response — no extra API call. Recurse the mapping (Subtask of a Story → `feature`). If parent is also unmapped, fall through to `chore`. |
| Epic | refuse to branch | (Handled in step 3.) |
| Anything else | `chore` | Catch-all so the skill never fails on an unfamiliar type. |

`<KEY>` is preserved in original case (e.g., `ENG-23`).

`<kebab-slug>` is derived from `fields.summary`:
- lowercase
- drop English articles (`a`, `an`, `the`)
- drop punctuation
- replace whitespace with `-`
- truncate to max 50 characters
- trim trailing hyphens

Examples:
- `feature/NUB-2094-skill-to-create-branch-from-jira`
- `bugfix/NUB-2008-import-mixed-case-headers`

### 5. Spec advisory check

Check whether a spec exists for this card — read and follow `.agents/shared/locate-spec.md` as a read-only caller. The spec is advisory here: on **unavailable**, say its status couldn't be checked; on **local spec unresolved**, give the local path and ask locate-spec's publish-or-obsolete question. If it remains unresolved and the developer explicitly chooses to continue branching, preserve that outcome and post no spec backlink at step 9. Neither outcome is "no spec": print its advisory in place of the no-spec warning below, then ask the same continue question. A choice to continue branching is not a decision that the local spec is obsolete.

If no match, print the warning and ask for confirmation:

> ⚠ No spec found at `nub_specs/specs/<year>/<key-slug>/spec.md`.
>
> If this work needs a spec, run `spec-draft <KEY>` first.
>
> If a spec is not required (e.g., typo fix, trivial cleanup), proceed — you will be asked to capture the reason in the PR body's `Spec: not required - [reason]` field at PR time.
>
> Continue with branch creation? [y/N]

If the user declines, stop. If they proceed, continue. **Do not record a "spec-not-required" marker at branch time** — the durable record lives in the PR body.

### 6. Pre-flight git checks

Confirm the working tree state. Uncommitted changes that are already part of the planned work for this branch should be allowed to carry over (the new branch is created at `origin/main`, so non-conflicting working-tree changes carry forward). If you see uncommitted changes, show `git status --short` and confirm with the user before creating the branch — do not silently lose work.

### 7. Create the branch

```
git fetch origin main
git switch -c <type>/<KEY>-<slug> --no-track origin/main
```

Always branch from `origin/main`, never local `main` (which may be stale). The `switch -c` form is the modern equivalent of `checkout -b`.

`--no-track` is load-bearing: without it, the new branch's upstream is `origin/main`, and a later bare `git push` (with `push.default=upstream`, or tooling that pushes to upstream) goes **straight to remote `main`**, bypassing PR review entirely — this happened in practice on NUB-2213, where users with branch-protection bypass rights got no server-side backstop. With `--no-track` the branch has no upstream until `create-pr` pushes it with `-u` to its own remote ref.

After creation, confirm with `git branch --show-current` and show the result to the user.

### 8. Transition Jira → In Progress

Apply the shared transition logic — read and follow `.agents/shared/jira-transition.md` (do not duplicate its logic here).

Target status: `In Progress`. Failures here are advisory per the partial — never block the branch creation that has already happened.

### 9. Post Jira backlink comment (if spec exists)

Only when step 5's locate-spec outcome was **found** (a spec on `nub_specs` `main`); otherwise post nothing and report `skipped — <locate-spec outcome>`, preserving the distinction between an unavailable source and a successful search with no match. Check whether the Jira card already has a backlink comment posted by this skill:

- Call `getJiraIssue` again with `fields` including `comment` (or use `expand=comment`) and look for a comment whose body starts with `Spec: https://github.com/Noetica/nub_specs/blob/main/specs/`.
- If absent, post a new comment via `addCommentToJiraIssue` with body:

> Spec: https://github.com/Noetica/nub_specs/blob/main/specs/`<year>`/`<key-slug>`/spec.md

Build the `<year>/<key-slug>` segment from the **actual path matched in step 5**, not a recomputed slug — they must agree.

(One-time only — `spec-grill` and subsequent runs of this skill should not re-post.)

If `addCommentToJiraIssue` fails: log `⚠ Jira backlink comment skipped — <reason>` and continue. The spec file is the durable record; the Jira comment is convenience.

### 10. Add the card to the current sprint

Branching is the moment work actually starts, so the card belongs in the active sprint — unless it carries the `offsprint` label, which the partial skips by design.

Apply the shared sprint logic — read and follow `.agents/shared/jira-sprint.md` (do not duplicate its logic here).

Failures there are advisory per the partial — never block the branch creation that has already happened. If step 2's response already carried `customfield_10020`, hand it to the partial rather than re-fetching.

### 11. Summary

Print a final one-block summary the dev can read at a glance:

```
✓ Branch: <branch-name>  (from origin/main @ <sha>)
✓ Jira:   <KEY> → In Progress
[✓ Sprint: added to current sprint] | [✓ Sprint: already in current sprint] | [✓ Sprint: skipped — offsprint card] | [⚠ Sprint: couldn't read labels — sprint left unchanged; pull it in unless offsprint] | [⚠ Sprint: couldn't add — pull it in]
[✓ Spec:  <link>] | [⚠ Local spec unresolved — <local path>; decide whether to publish it or confirm it is obsolete] | [⚠ Spec status not checked — nub_specs main unreadable; authenticate gh or restore network access] | [⚠ No spec — see spec-draft]
[✓ Backlink: posted to Jira] | [skipped — already present] | [skipped — <locate-spec outcome>]

⮕ Next: implement <KEY> to plan and build
```

Skip the `⮕ Next` pointer when this prompt was chained from `implement` — the caller continues on its own.

## Scope

- Single-key invocation only. Bulk branch creation across multiple cards is not supported.
- This skill does not handle merge, push, or PR creation — those belong to `create-pr`.
- No bypass mechanism for the spec advisory warning at branch time — it stays advisory by design.
