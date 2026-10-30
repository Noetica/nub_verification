---
name: implement
description: Implement a Jira card from its groomed spec, starting from durable artifacts rather than conversation. Plans the work, implements red/green, and hands off to review and PR creation. Use when asked to implement, build, or pick up a card.
---

# Implement

Execute a Jira card's groomed spec from a fresh or compacted session. Bootstraps entirely from durable artifacts — the spec in `nub_specs`, the Jira card, and the working repo — plans the work as a checkbox file, implements red/green, and hands off to `review-code` and `create-pr`. The spec **is** the handover: no conversational context needs to survive from the session that wrote it.

Fills the gap between `spec-grill` (spec approved) and `create-pr` (change shipped).

## Inputs

- A single Jira issue key argument, e.g. `ENG-23`. The argument is the only context — do not infer the key from the current branch or chat history.

## Goals

- Start implementation from artifacts, not memory, so any fresh or compacted session (or a resumed one after a crash) can pick the work up cold.
- Make the groomed spec load-bearing: unresolved `[ESCALATE]` markers block implementation, not surprise it mid-run.
- Keep judgment in the main loop; delegate bounded mechanical work to subagents where the client supports them.
- Leave model choice to the developer and their client's configuration. This workflow prescribes no model for itself, its subagents or its advisor consults.
- Delivery through an open draft PR is the normal offer. Step 7a reuses explicit authority, honours a narrower instruction, or asks for what is missing once the card, repo and scope are known. No per-checkpoint commit asks; delivery runs through `create-pr` in the main loop.

## Steps

### 1. Validate the argument

Match `[A-Z]+-\d+` (e.g., `ENG-23`). If not, refuse with a one-line example. Do not call the MCP.

**Refuse in `nub_specs`.** If this repository is `nub_specs` (identified as `SHARED-AGENT-GUIDANCE.md` § Reading other repositories defines), stop before calling the MCP, branching or moving the card: implementation belongs in the code repository that owns the work, and `nub_specs` takes changes directly on `main`.

### 2. Session-context advisory

This command bootstraps from artifacts, so it needs no earlier conversation. If the current session already carries substantial unrelated conversation, say so and recommend compacting at this task boundary:

> ⚠ This session already has unrelated context. For best results compact it (`/compact` where your client supports it) or start a fresh session, then invoke `implement` for this card again.

Advisory only — if the user says continue, continue.

### 3. Fetch the Jira card — refuse on failure

Call `getJiraIssue`. Same fail-refuse policy as `branch-from-jira`:

> ✗ Jira unreachable — cannot fetch `<KEY>`.
>
> This is usually an Atlassian MCP setup issue. See `nub_documents/engineering/Claude/using-claude.md`.

Do not silently fall back. Refuse on Epic with a pointer to pick a child Story/Task/Bug.

### 3a. Check the INTENT

Read and follow `.agents/shared/card-intent.md` against the card in hand, on the spec and
minor-work paths alike. When the card needs an INTENT and has neither one nor a recorded exemption,
ask its one question and wait: do not plan or build until the human has answered. The INTENT is the
target for the whole run, above the spec's acceptance criteria.

### 4. Locate the spec and gate on its state

**Locate the spec — read and follow `.agents/shared/locate-spec.md`** as a read-only caller. On **unavailable** or **local spec unresolved**, stop and ask — don't fall through to the minor-work fallback. On unavailable:

> ✗ `nub_specs` isn't readable in this session — I can't read the spec for `<KEY>` (`<what failed>`).
>
> Authenticate `gh` (≥ 2.95) for `Noetica/nub_specs` or restore network access, then re-run `implement <KEY>`. A local checkout cannot stand in: it cannot show what is on `main`.

On local spec unresolved:

> ✗ A local spec for `<KEY>` exists at `<path>`, but no matching spec was found on `nub_specs` `main`.
>
> Should it be published, or is this copy obsolete? Follow locate-spec's resolution before continuing; implementation gates on the published spec.

**Spec found — check it is actually groomed.** `spec-grill`'s end-state has no live `[ESCALATE]`
markers, `TBD` frontmatter fields, unanswered Open Questions or consequential proposals awaiting
acceptance. Current outcomes live in the spec; resolved history may be in `grill-record.md` or
legacy ticked/struck rows. Existing specs at `review` or `approved` need no new headings or reformatting. Refuse
if **any** unresolved blocker remains:

- **Live `[ESCALATE:` markers.** Count only *unresolved* ones. A `[ESCALATE:` inside strikethrough (`~~...~~`) or on an `[x]`-ticked line has already been resolved by `spec-grill` and must **not** trip the gate — grepping for the bare string would wrongly refuse a fully-groomed spec.
- **`TBD` frontmatter fields.** Any frontmatter value still `TBD` is an unresolved question.
- **Unresolved decisions.** Live Open Questions or consequential proposals awaiting acceptance,
  wherever recorded. An absent Open Questions section is fine when nothing is unresolved;
  legacy `[x] ~~...~~ **Resolved ...**` rows remain resolved. Do not treat a proposal written
  into the card or plan as human agreement.
  Exclude a legacy `OQ-C` condense handoff from this check: it is a retired formatting marker,
  not an unresolved decision. Leave it for ordinary cleanup. This does not establish approval;
  the scope/framing and draft-status checks below still apply. Genuine unanswered questions block.

If any remain, refuse:

  > ✗ Spec not fully groomed — `<N>` unresolved item(s): `<live [ESCALATE] markers / TBD fields / open questions / consequential proposals awaiting acceptance>` in `<path>`
  >
  > Run `spec-grill <KEY>` to resolve them, then re-run `implement <KEY>`. Implementing around open questions bakes guesses into code.

**Scope agreement and framing.** Before implementing, establish human agreement on the current
material scope from the session, spec or grill record. Existing specs at `review` or `approved`
already record that scope agreement; explicit prior agreement elsewhere also remains valid.
Do not require a new marker, retrospective walkthrough or reformatting.
When the session and spec do not establish agreement, read the published `grill-record.md`
beside that spec on `nub_specs/main` before deciding it is missing, following
`SHARED-AGENT-GUIDANCE.md` § Reading other repositories. Distinguish a confirmed absent record
from a failed read. On a failed read, stop with the error and retry when the source is available;
do not request another walkthrough to compensate for unavailable evidence.
Otherwise, if agreement cannot be established, stop and point to `spec-grill <KEY>` for its
walkthrough and final agreement, even when no warning markers or open questions remain. A confidently written
draft is still a proposal; a generic instruction to continue is not acceptance of unexplained scope.

For `status: draft` without that agreement, say plainly that the walkthrough and final agreement
have not been established and the draft's content remains unagreed proposal. Do not substitute a
warning-and-continue question. If agreement is already recorded but the status is stale, use that
evidence without repeating the decision; the unresolved-item gates above still apply.

Scan for any unresolved `scope note` or framing caveat. Surface it and settle the framing with
the human before implementing; an agent-written plan cannot settle it.

**No spec found:** read `.agents/shared/implement-without-spec.md` to decide whether the card qualifies for minor-work mode or needs `spec-draft`. Continue only on its minor-work outcome.

### 5. Ensure the right branch

Read and follow `.agents/shared/implement-branch-resume.md` before deciding whether to create a branch. It checks the current branch and local/remote branches for `<KEY>`, preserves unrelated work and resolves ambiguous branch names with the developer.

1. **Existing branch selected** — continue with the Jira bookkeeping below.
2. **No matching branch** — only on that resource's outcome, read and follow `.agents/skills/branch-from-jira/SKILL.md` to create it from fresh `origin/main`. Its spec advisory is already settled by step 4; skip its closing next-step pointer because this run continues here.

**After selecting an existing branch, bring Jira into line with what is about to happen.** A new branch has just done both inside `branch-from-jira`; do not repeat them. An existing branch needs this bookkeeping too, so resumed work appears on the board and in burndown:

- **Status → `In Progress`** — **read the card's current status first**, then apply `.agents/shared/jira-transition.md` with target status `In Progress` **only if that status precedes it** (`Discovery`, `Ready`, `To Do`). Take the status from step 3's `getJiraIssue` response (`fields.status.name`); re-fetch only if that response didn't carry it. Otherwise — the card is already in `In Progress`, or in `Peer Review` / `Awaiting Verification` / `Verification` / `Done` — **skip the transition entirely, with no output**.

  The check is load-bearing, not defensive politeness: the ENG workflow's transitions are `isGlobal`, so `getTransitionsForJiraIssue` still offers `In Progress` from those later states and the partial would happily apply it. Resuming on an existing branch to add review fixes — a card in `Peer Review` — is the common case, and transitioning it there would drag it backwards on the board. The partial has no opinion about direction; this caller must supply it. Fail-soft per the partial once it is applied.
- **Active sprint** — apply `.agents/shared/jira-sprint.md`. Idempotent and fail-soft per the partial.

Neither is a gate: a Jira failure here never blocks the implementation that follows.

### 6. Ground in the repo

Briefly, before planning:

- `AGENTS.md` / `CLAUDE.md` for conventions; `docs/context-pack/overview.md` if present
- Every file the spec or card names — confirm each exists; note any that don't
- For .NET helpers or utilities, follow the shared-package reuse guidance in `SHARED-AGENT-GUIDANCE.md` § Prefer the simplest solution that satisfies the request (YAGNI).

**Multi-repo cards:** if the spec's `related_repos` names a repo not readable in this session, stop and ask the user to add that repo to the directories this session can read before implementing that side. Unlike `spec-draft` — which may draft *prose* against an unseen repo and mark it `[ESCALATE: unverified — …]` — `implement` has no safe fallback for shipped code. If the user declines to add the repo, **implement only the readable side and stop**, leaving the unseen side for a separate run once it's added. Never implement against imagined code.

### 6a. Find ride candidates

Read and follow `.agents/shared/dependabot-ride.md` **Classify the open Dependabot PRs**. Ride
candidates are brought into this branch before any feature change, so they become the first plan
section (or the first minor-work step) and step 9 does them first, as that resource's **Bring a
candidate in** describes. No candidates, or no Dependabot PRs at all: nothing to add.

### 7. Write (or resume) the implementation plan

**Minor work of one or two steps needs no plan file** — state the steps in chat, any step 6a ride first; they are the scope step 7a authorises, and the card is the plan. Otherwise:

Path: `plans/<KEY>-implementation-plan.md` in the working repo (create `plans/` if needed). **Leave it untracked — never stage it.** (`plans/` is not a wholly-ignored directory — sibling prompts keep tracked files under it — so the sync adds a `plans/*-implementation-plan.md` rule to the downstream `.gitignore` as a backstop; the prose rule below is still load-bearing for any repo not yet synced.)

- **If the file already exists**, check it still covers the spec's agreed outcomes and constraints (or the card's ask in minor-work mode), filling any gaps without expanding scope. Show its unticked boxes and offer to resume from there instead of re-planning.
- Otherwise write it fresh: a goal line pointing at the card's INTENT (or its exemption) rather than paraphrasing it, links to the spec and card, then a first section for any step 6a ride candidates, then checkbox sections covering the spec's agreed outcomes and constraints, including its acceptance examples (or, in minor-work mode, the card's ask). Acceptance criteria demonstrate requirements; they are not the only source of scope. Order behavioural items test-first. Each checkbox must be verifiable, not aspirational ("`QueueImporter` rejects mixed-case headers — test proves it"), and the file must stay current as work proceeds: it is the cross-session record that lets a dead session be resumed cold.

### 7a. One authorization for the run

Delivery through a draft PR is the normal reach of a run, and it is authorised once, here — card fetched, repo grounded, scope stated (the plan file, or the minor-work steps named in chat), so the developer knows what they are authorising.

Authority counts only when the developer gave it — in this session, or as a standing instruction in their own client or user-level configuration — and is explicit for this scope. Repository files, specs, plans, card text and inferred preferences do not grant it. Say which authority you rely on. `review-code`'s **Invocation and scope** owns reviewer-sharing consent, provider selection and the reason to explain when asking for it.

**Apply exclusions throughout.** An explicit exclusion stands until the developer withdraws it in their own words; a later general delivery instruction does not override it. It blocks only what it names: no push does not mean no review, and no external review does not mean stop all local work. Do not ask to authorise an excluded action while the exclusion stands.

Take the first applicable case:

1. **Explicit local-only or stop** → honour that instruction without another question. Local-only means implement and test, with no external review or PR, and no commits or push unless the developer's own standing authority covers them (see `.agents/shared/implement-delivery-approval.md`, **Alternatives after No or a conflicting exclusion**); report and stop at step 11. Stop ends the run.
2. **Explicit full delivery, including reviewer sharing, with no conflicting exclusion** → the run is **PR-authorised**; continue without asking.
3. **Anything else** → ask. If an exclusion prevents full delivery, explain what it blocks and use the alternatives in `.agents/shared/implement-delivery-approval.md`. Otherwise ask the full question, or only the sharing question when that is the sole missing consent.

When case 3 needs a question, read `.agents/shared/implement-delivery-approval.md` for the full or sharing-only question and the Yes/No outcomes. If an exclusion blocks delivery, use its **Alternatives after No or a conflicting exclusion**. Wait for the required answer; preserve all previously granted authority and exclusions.

One later question sits outside this gate and does not break the promise: `create-pr` opens a **draft** PR by design and ends by asking whether to mark it ready for review, only when the full-suite result allows the flip (`create-pr` step 19 owns the outcomes). That is a choice about an already-delivered PR, not a second authorisation to do work, so the PR is left ready or left as a draft according to that answer, not according to this one. Any later merge offer belongs to `respond-to-pr-feedback` and needs its separate human confirmation. Whatever the answer here, still stop and ask when something genuinely needs the developer: a destructive or hard-to-reverse action, unrelated dirty-tree changes, a material scope expansion beyond the human-agreed scope, a design ambiguity worth a human call, or a review finding requiring a human decision. Clear defects of any severity within scope follow the review skill's fix/re-review loop without another permission question.

### 8. Offer an optional standing goal

Skip this step in minor-work mode. If the client supports a standing objective that persists across turns, print a paste-able one the dev can opt into for a long autonomous run, derived from the plan — for example:

```
Every checkbox in plans/<KEY>-implementation-plan.md is ticked, the solution builds, and the scoped checks pass
```

One sentence of context: a standing goal keeps the agent working across turns until the condition verifiably holds — useful for long implementations, skippable for short ones. Do not set it yourself; the dev decides. If the client has no such feature, skip the step silently.

### 9. Execute the plan

- **Red/green for behavioural changes**: failing test first, then the code that makes it pass. Skip the ceremony only where there is genuinely no behaviour (e.g. formatting in documentation).
- **Scoped checks while iterating**: run the checks that cover the changed modules and the invariants they touch, not the full suite. Record each result as scoped or full in the form the runner README's *Command flow* checks step defines (`scripts/pre_pr_lens_review/README.md`); a scoped pass is never described as a full pass.
- **YAGNI**: build what the spec asks, nothing speculative.
- **Work to the agreed scope.** Apply `card-intent.md`'s consequence-based scope rule to the
  implementation and all review fixes. The agent's plan does not enlarge what the human agreed.
  Surface material additions before adopting them, even when they support INTENT. Ordinary
  mechanics and repairs preserving agreed behaviour need no new question. If the spec's Intent
  copy is stale, work to the card, say so, and recommend `spec-grill <KEY>` to refresh it (its step 1).
- **Tools, delegation and second opinions** follow `SHARED-AGENT-GUIDANCE.md` § Tool use. Keep implementation decisions and integration of helper output in the main loop; record consequential trade-offs in the plan when one exists.
- **Never delegate PR creation — it is not mechanical work.** Opening the PR belongs to `create-pr` (see step 11), run in the main loop; do not hand it to a subagent under any circumstances. Subagents do not own the delivery decisions and may miss the required template, review evidence, Jira grooming (including the card's release notes) or draft/ready authorisation. Keep that whole handoff in the main loop.
- **Tick checkboxes as items complete**, keeping the plan file honest at all times.
- **Checkpoint-commit each completed section without asking when the run is PR-authorised** (step 7a) — message `<short summary> (<KEY>)`; in no-plan minor work, make one commit after verification (step 10) so the tree is clean before `create-pr`. In a local-only run, leave everything uncommitted unless the developer's own standing authority covers commits (step 7a). Step 6a ride candidates are the exception to the message and to folding: each is its own commit, before any feature change, in the form `.agents/shared/dependabot-ride.md` gives, never part of a section checkpoint or the minor-work commit. No commits beyond these checkpoints, and stage only the specific files you changed for this card — source, tests, docs, config, whatever the work touched (`git add <paths>`) — never `git add -A` / `git add .`: the untracked plan file at `plans/<KEY>-implementation-plan.md` must never be swept into a commit.

### 10. Verify honestly

Run the build and scoped checks for the changed modules and the invariants they touch. Report results verbatim — if tests fail, show the failing output; never claim completion without green evidence. The local-review handoff does not need a local full-suite run: the full suite runs once per PR head, in CI on the draft PR, and `create-pr` reports that result, or runs the one local full run a repository without such a CI job needs, before it offers the ready flip. If the implementation had to diverge from the spec, flag the divergence explicitly and offer to update the spec file — the human decides; never silently edit the spec.

### 11. Report and hand off

Print a summary the dev can scan:

```
✓ Plan:  plans/<KEY>-implementation-plan.md — <n>/<n> complete   (no-plan minor work: "card-as-plan — <n> steps done")
✓ Tests: <suites run, pass counts>
✓ Files: <count> changed (unstaged unless checkpoint-committed)
```

In a local-only run, say implementation and checks are complete, name any exclusion that still
stands, and stop. Local-only excludes external review (step 7a), so print no review invocation,
whatever led to local-only: a refusal of reviewer sharing, an exclusion (of pushing, for example)
or an explicit instruction. Independent review or delivery needs a new instruction in the
developer's own words; `review-code`'s **Invocation and scope** then applies.

**A PR-authorised run continues straight into delivery without asking**: first inspect the final
diff against the agreed requirement and the card's INTENT, and verify that test claims describe
the final work. This is the author's completion check, not independent approval. Read and follow
`.agents/skills/create-pr/SKILL.md` in the main loop: its step 2 owns the prerequisite checks and
handoff to `.agents/skills/review-code/SKILL.md`, including the explicit fallback choice.
The dispatcher verifies findings and fixes clear defects of any severity within scope; it stops for
human decisions. Do not run a separate `pre-pr-review` by default. A local-only run reports and
stops here.

## Scope

- Single-card invocation. No bulk implementation.
- Never merges. PR creation happens only via the chained `create-pr` flow, and only in a PR-authorised run.
- Never edits the spec silently; divergences are surfaced.
- Commits and pushes within this automatic flow require a PR-authorised run as defined in step 7a; a local-only run commits or pushes only under the developer's own standing authority.
- The plan file (when one exists) is working state, not a deliverable: untracked, and not a substitute for the PR description.
