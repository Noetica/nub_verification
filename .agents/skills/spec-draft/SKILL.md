---
name: spec-draft
description: Draft a concise, human-readable specification from a Jira card, exposing proposed additions and unresolved decisions. Use when asked to write, draft or start a spec for a card.
---

# Spec Draft

Produce a concise proposal the human can understand and review with `spec-grill`: the intended
behaviour, the shape and consequences of the change, and decisions still needed. Leave ordinary
implementation mechanics to the implementer. A confident agent proposal is still a proposal.

## Inputs

- A single Jira issue key argument, e.g. `ENG-23`.

## Goals

- Turn a Jira card body + repo context into a spec file at the canonical path.
- Surface consequential agent additions as well as uncertainty with `[ESCALATE: ...]` markers or Open Questions.
- Be honest about scope: if the Jira summary doesn't match the spec scope that emerges, say so at the top.
- Draft to the card's INTENT, carried into the spec word for word. The INTENT's rules have one home: `.agents/shared/card-intent.md`.
- Never commit. Never post Jira comments. Both belong to downstream skills (`branch-from-jira` posts the backlink; the dev commits when they're satisfied). The one Jira write this skill makes is the INTENT or exemption record the human supplies at step 3a.

## Steps

### 1. Validate the argument

Match `[A-Z]+-\d+`. Refuse with example if not.

### 2. Fetch the Jira card — refuse on failure

Call `getJiraIssue`. Same fail-refuse policy as `branch-from-jira`:

> ✗ Jira unreachable — cannot fetch `<KEY>`.
>
> This is usually an Atlassian MCP setup issue. See `nub_documents/engineering/Claude/using-claude.md`.

Do not silently fall back.

### 3. Refuse on Epic

Epics don't get specs of their own — the child stories/tasks do. Refuse with a pointer.

### 3a. Check the INTENT

Read and follow `.agents/shared/card-intent.md` against the card in hand. When the card needs an
INTENT and has neither one nor a recorded exemption, ask its one question and wait: do not draft
until the human has answered.

### 4. Confirm `../nub_specs` is checked out, then refuse if a spec already exists

This command reads its template and reference specs from `../nub_specs` and **writes the new spec there**, so that sibling repo must be present in the session. Read and follow `.agents/shared/locate-spec.md` as an authoring caller — the writable checkout's availability check first, then the case-insensitive key-prefix search as a duplicate check, in the working tree and on published `main`. A miss here is worse than elsewhere: it creates a **second, duplicate** spec for a card that already has one. If `../nub_specs` isn't available, stop and ask; don't fall back to writing into this repo:

> ✗ `nub_specs` isn't available in this session — I can't read the spec template or write the spec.
>
> Clone it beside this repo, or add it to the directories this session can read, then re-run `spec-draft <KEY>`.

If a working-tree spec matches the key, refuse:

> ✗ Spec already exists at `<path>`.
>
> Use `spec-grill <KEY-or-path>` to refine the existing spec instead.

On **missing locally**, use locate-spec's reconciliation guidance instead of the duplicate message above. Stop authoring and give the `spec-grill` pointer only after the checkout is reconciled.

`spec-draft` writes new specs only; refinement is `spec-grill`'s job.

### 5. Read the template and reference material

Read the template first, then gather the independent reference material together where supported
by the client (see `SHARED-AGENT-GUIDANCE.md` § Tool use). Reuse the Jira card already in hand:

- `../nub_specs/templates/spec-template.md` — the active template and authoring rules; it owns the human-facing shape, supporting detail and optional sections
- `../nub_specs/DevOps/08-operating-model.md` — broader context for what specs are for
- A recent spec only if useful for domain context; do not copy its length or older boilerplate over the active template
- The Jira card body (already in hand from step 2, or the re-read after a step 3a write)

### 6. Gather repo context (codebase-first)

**First: confirm the card's component actually lives in this repo.** Search the working repo for the component/service/class the card names. If it isn't found here, say so and stop — name the likely owning repo if you can (check candidates from the remote, as `SHARED-AGENT-GUIDANCE.md` § Reading other repositories describes) and let the user re-run `spec-draft` there. Cards are routinely opened from the wrong repo; drafting against the wrong codebase wastes the whole run.

Then briefly explore the working repo for clues that inform the spec:

- Check `AGENTS.md` / `CLAUDE.md` for repo purpose and conventions
- Skim `docs/context-pack/overview.md` if present
- Note any files mentioned in the Jira card body and check they exist

Ground the proposal in evidence without making the human read an investigation log:

- **A claim about how the current code behaves cites `path:line`** (or path plus symbol). Without
  one it is not a fact the spec may rely on: verify it now and cite it in the grill record or
  beside the claim where essential, tag it `ASSUMED`, or make it an `[ESCALATE]` fact item.
  A consequential decision cannot be settled by an unverified assumption. Author confidence is
  not a citation. Keep investigation detail in the record; the spec states the relevant consequence.
- **Two requirements that cannot both hold say which wins.** Record the precedence and why, or
  carry the conflict as one `[ESCALATE]` for the grill; never leave both standing as if compatible.

**Check that this is still one card before writing.** If the emerging scope contains multiple independently deliverable outcomes, needs materially different owners/specs, or has a dependency tree too large to describe coherently as one implementation card, stop before drafting and say: `This appears too big for a single card because <evidence>.` Ask the human whether to continue, split the work, or rethink the scope. Do not prescribe a particular tool or workflow, and do not hide the mismatch inside a mega-spec.

**Multi-repo cards — read before guessing.** If the card's scope spans a repo that is not in this session (e.g. an API+GUI change, but only the API repo is checked out), read it from the remote as `SHARED-AGENT-GUIDANCE.md` § Reading other repositories describes (`gh repo read-file` / `gh repo read-dir`) and ground the spec in its actual code. Only if that read fails, do **not** invent its details: mark every claim about the unseen repo with `[ESCALATE: unverified — <repo> not readable during drafting]` so `spec-grill` resolves them once it can be read. List all touched repos in `related_repos`.

### 7. Draft the spec

Write to `../nub_specs/specs/<year>/<key-slug>/spec.md`:

- `<year>` is the **current** year (the year the spec is drafted, from today's date) — not the Jira `created` year. This keeps recently-drafted specs clustered in the current-year folder, which is how people browse them. `branch-from-jira` and `spec-grill` glob across all years, so locating a spec never depends on which year folder it landed in.
- `<key-slug>` is `<key-lowercased>-<kebab-summary>` (same slug rules as `branch-from-jira`)

Use the active template, deleting its authoring comments and inapplicable sections. Fill Intent
by copying the card's INTENT or exemption word for word. Put the overall change and its material
consequences near the top, in language the requester can review without opening source code.
Apply `card-intent.md`'s attribution and scope rules to the whole card, not just its INTENT:
agent-authored approach text is not automatically an agreed requirement. Draft the smallest
change that meets the INTENT: carry a card's Proposed items only where the INTENT needs them, and
say which you left out.

- **Expose consequential proposals.** A choice not already requested or explicitly agreed gets
  a clear **Proposed** label and an Open Question, even if you are confident it is useful. Say
  what it changes, why, and what leaving it out would mean. Do not turn a necessary constraint
  into permission to pick a new policy; present the trade-off. Reuse recorded human decisions
  without making the human answer them again.

- **Complexity budget.** Every new component, state, configuration option, retry, background
  process or extension point must be needed for the agreed behaviour or an evidenced system
  constraint; otherwise omit it. The same holds for a new rule, clause or record in a prompt or
  standard: prefer a principle an agent can apply over enumerated edge cases, and do not restate
  what the target already says. A justification explains the proposal, not its approval.
- **Tool claims are FACT items.** Any statement about a CLI's flags, behaviour or limits is
  verified (`--help`, source) and cited before it is written.
- **A manual verification step names an owner and a gate.** Any verification item only a human can
  run states who runs it and what it blocks until it has run (a status transition, the ready flip,
  a release). An ungated manual step is a permanent review finding that no review can close.

Useful investigation notes and mechanics that surface go to the existing `grill-record.md`, not
a second specification. The template draws the boundary; the file's convention lives in
`spec-grill`. The agreed behaviour and important constraints must stand in the spec itself.

Frontmatter:

```yaml
---
status: draft
owner: <Jira assignee displayName, or "TBD" if unassigned>
last_reviewed: <today, YYYY-MM-DD>
next_review: <today + 14 days>
jira_key: <KEY>
epic: <parent epic key, or N/A>
github_issue: N/A
prd: N/A
related_repos: []
linked_adrs: []
release_note_tier: TBD
release_note_type: TBD
breaking_change: TBD
consumers: []
---
```

For `epic`, read the parent from the card already in hand (step 2): if `fields.parent` exists and is an Epic, write its key (e.g. `NUB-1383`); otherwise write `N/A`. This is a deterministic backlink, not a guess — it gives "show me every spec under this epic" via a grep on `epic:` without nesting specs in the directory tree (specs stay flat at `specs/<year>/<key-slug>/spec.md`, which is what the dup-check, `spec-grill`, and `branch-from-jira` globs depend on). Do not nest the spec under the epic's folder.

Most frontmatter fields will need updating during review — set them with conservative defaults rather than hallucinating.

For `release_note_tier` / `release_note_type`, **`TBD` is the conservative default, not `None`** — `None`/`N/A` is a positive assertion that no release note is needed, which is a real decision, not an "unsure" state. So:
- If the card clearly has no external impact (internal tooling, refactor, test-only), write `None` / `N/A`.
- If the card clearly is customer- or dev-facing (a behaviour users see, an API change), infer the likely value (e.g. `Customer` / `Fixed`) **and** add an `[ESCALATE: ...]` or Open Question for release-management sign-off — don't silently commit to it.
- Otherwise leave both `TBD`.

Read and follow `.agents/shared/spec-contract-impact.md` § Draft classification before filling
`breaking_change`, `consumers`, and Contract Impact.

### 8. Surface scope mismatch

If the Jira summary doesn't accurately describe the spec scope that emerges from the card body + your synthesis, **flag this at the top of the spec** with a quoted note:

> **Scope note (LLM-flagged)**: the original `<KEY>` summary is "..." but this draft proposes ... Confirm the scope before renaming the card.

Do not silently rename. Surface the mismatch and let the human decide.

**Don't assert what you're escalating.** When the framing itself is in question (e.g. "is this a regression or new enablement?"), keep the **title and overview neutral and descriptive** — name the user-visible outcome (e.g. `Column reordering in Dashboard grids`), not the disputed verb (`Restore` vs `Enable`). The same rule applies everywhere: never state a confident value — in the title, the overview, or a frontmatter field — for something you simultaneously flag as uncertain. Carry each uncertainty in exactly one place (an `[ESCALATE]` or an Open Question) so the human resolves it once in `spec-grill`, rather than reconciling contradictions scattered through the draft.

### 9. Expose decisions; research facts

Where human input is needed, use one `[ESCALATE: <question>]` marker or an Open Question with a
stable ID. Link to that item instead of repeating it in several places. Confidence in a proposal
does not remove the need for a scope decision.

Do not use the human as a search engine. Before adding a marker, classify the unknown:

- **Fact / research** — if an objective answer should exist in the accessible code, docs, Jira card, tools, or a real example, investigate it now and cite the evidence. If the authoritative source is inaccessible, mark the verification prerequisite explicitly rather than turning the fact into a preference question.
- **Decision / human input** — desired behaviour, policy, scope, risk acceptance, or a genuine trade-off belongs in `[ESCALATE]` even when the current implementation points one way. Existing code establishes the present state; it does not silently choose the intended future state.

Examples of `[ESCALATE]`-worthy moments:
- Disputable scope boundaries ("does this include X?")
- Open technology choices ("Azure Function or Logic App?")
- Behavioural defaults the card doesn't specify ("what happens on timeout?")
- Domain language conflicts ("the card says 'tenant' but the codebase uses 'workspace'")

### 10. Keep unresolved work visible

Keep Open Questions while anything is unresolved: stable ID, decision or missing evidence, and
owner/needed-by when meaningful. A proposed addition awaiting acceptance is unresolved. If there
are no such items, omit the empty section; the walkthrough still needs to happen.

### 11. Set status: draft

The dev (or `spec-grill`) flips it to `review` / `approved` later.

### 12. Readability pass, then report back

Read the draft as the requester. Remove repeated framing, empty sections and implementation
instructions. Preserve INTENT, the decisions, meaningful acceptance examples and unresolved work.
Do not make sentences denser to hit a line count. Report the proposed change in a few plain
sentences, explicitly naming consequential additions, then:

```
✓ Spec drafted: <path>
  - <N> [ESCALATE] markers
  - <M> open questions
  - <K> consequential proposals needing agreement

⮕ Next step: run `spec-grill <KEY>` to walk through the proposed change and settle its decisions.
```

**Offer the walkthrough even when there are no open questions.** If the user already asked for
draft and grill, continue using `.agents/skills/spec-grill/SKILL.md`; otherwise offer to start it.
Respect a request to review the draft first. A finished draft is not evidence of human agreement.

Do **not** offer to commit the file or post to Jira. Both are downstream concerns. Do say, in one
line, that the draft is an unpublished local file in the `nub_specs` checkout: it is published when
committed and pushed to `nub_specs` `main` (no branch, no PR), normally once the grill has resolved
it, and `spec-grill`'s summary owns that handoff and the approved SHA.

## Scope

- Single-card invocation. No bulk drafting.
- Never overwrites an existing spec.
- Never commits or posts external messages. The INTENT or exemption write at step 3a is the one Jira edit.
- Repo context exploration should be brief and targeted — this is not the place to run a full RepoMap. Use the context pack if present; otherwise sample.
