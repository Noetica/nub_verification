---
name: spec-grill
description: Walk through a spec's proposed change with the human, expose agent additions and settle decisions through research and discussion. Use when asked to grill, review, resolve, harden or finish a spec, including written answers.
---

# Spec Grill

Collaborative review of the whole proposed change, including choices the draft states confidently.
Explain what it means for users and the system, expose consequential agent additions, and resolve
the decisions with the human. Keep the name `spec-grill`; its outcome is an understood agreement.

## Inputs

A single argument, either:
- A Jira key (e.g. `ENG-23`) — locate the spec at the conventional path
- A path to an existing `spec.md` — use directly

## Primary directive

Walk through the material change section by section in plain language, then confirm the resulting
agreement. An empty uncertainty queue alone is not completion. Research discoverable facts, ask
for decisions in manageable rounds, and save settled outcomes before continuing.

## Rules

- **Adaptive rounds.** Follow `SHARED-AGENT-GUIDANCE.md` § Tool use for pacing, question presentation and tool handling. The Question rounds section below applies that policy to the spec's dependency queue.
- **The queue is dynamic, not a frozen checklist.** Build an initial view of the unresolved space, then reassess dependencies as answers arrive and select a fresh round after integrating them. An answer may unblock a new precise question, invalidate a queued question, or expose that an apparently separate question was the same decision. Prioritize the highest-impact unblocked decisions; never march through a stale queue for the sake of completing it.
- **Classify before resolving.** Give every queued item one resolution mode:
  - `FACT / RESEARCH` — an objective answer should be discoverable in code, docs, tools, telemetry, a real example, or another authoritative source. The agent investigates; the human is not asked to guess.
  - `DECISION / HITL` — desired behaviour, policy, scope, risk acceptance, or a trade-off. The human decides after seeing evidence and a recommendation.
  - `PROTOTYPE / HITL` — discussion needs a concrete throwaway example, mock-up, or behavioural spike before the human can decide. Record what the prototype must answer; do not substitute imagined results.
  - `PREREQUISITE` — access, data, setup, or another manual fact-gathering step must happen before the question is answerable. Record the owner and completion condition.

  The classification is working state, not extra ceremony in the finished spec. If the grill pauses on a `PROTOTYPE` or `PREREQUISITE`, preserve the mode and next action in the unresolved Open Question so a later session can resume cold.
- **Verify value-class rules against ground truth before recording them.** When a decision distinguishes concrete input classes (omitted vs null vs empty string, zero vs missing, trailing suffix vs stripped), do not accept a reasoned collapse of two classes ("these are indistinguishable") without checking: write out the full input→output triple table and test it against existing code behaviour or a real example. A wrong collapse here ships straight into implementation.
- **Facts are discovered; decisions belong to the human.** Use the repo and other authoritative sources to answer `FACT / RESEARCH` items. For a `DECISION / HITL`, the codebase is evidence about current behaviour and constraints, not authority for desired future behaviour. Present what it shows and your recommendation, but always put the decision to the human and wait; never let an existing implementation silently make a product, policy, scope, or risk-acceptance decision.
- **INTENT, provenance and scope.** Follow `.agents/shared/card-intent.md`: a consequential
  proposal is not approved merely because it supports INTENT or appears in agent-written card
  text. Distinguish the human's request and recorded decisions from facts and your proposals.
  Reuse explicit prior answers; do not demand that already agreed decisions be made again.
- **Surface contradictions immediately.** If the user's answer conflicts with the existing spec text, with the codebase, or with an earlier answer in this session, name the contradiction and ask which is right.
- **Stress-test with concrete scenarios.** "Imagine X happens; what should the system do?" Specific scenarios force precision. Generic questions invite vague answers.
- **Contract impact is a required decision.** Read `.agents/shared/spec-contract-impact.md`
  when inspecting or resolving contract impact; it owns compatibility challenges, classification,
  consumer coordination, Jira-label propagation and breaking-change status eligibility.
- **Apply the ADR threshold after each decision.** All three must be true to create an ADR:
  - Hard to reverse (the cost of changing your mind later is meaningful)
  - Surprising without context (a future reader will wonder "why on earth?")
  - Result of a real trade-off (genuine alternatives existed, one chosen for specific reasons)

  If any of the three is missing, skip the ADR. Note the decision in the spec inline; do not promote every resolution to ADR-grade.

- **Tag confidence on derived facts.** When you record something the user said as an `ASSUMED` fact (without code/doc backing), tag it as such in the spec. The same convention as `context-2-interview`.
- **Ground current-behaviour claims.** Verify the evidence in the spec or grill record (`path:line`
  or path plus symbol). Missing support is a `FACT / RESEARCH` item. Keep investigation detail in
  the record and the relevant consequence in the spec. An `ASSUMED` tag cannot settle a decision
  that depends on the unverified fact.
- **A contradiction resolves to a winner.** Surfacing two requirements that cannot both hold is not enough: the spec must record which wins and why (the human's call where it is a decision), or the pair stays open. A conflict the spec merely notes is still unresolved.
- **Keep the agreement current.** Put the settled outcome in its spec home and record the
  question, human answer and date in the grill record. Then remove the resolved question from the
  spec; never remove an unanswered item. Existing ticked/struck resolutions remain valid and can
  be moved to the record during cleanup without reopening the decision.
- **Edit the home, then grep.** Search affected terms for stale paraphrases after editing a rule.
  Preserve superseded decisions in the record; the spec states what now applies.
- **Smallest change that resolves the finding.** Never generalise a fix beyond what the finding needs.
- **External findings go through triage first.** Before any edit, verify each claim against the spec, card, and codebase — reviewer confidence, model reputation, or a retraction is not evidence — and record a CONFIRMED / REFUTED / UNCLEAR verdict with its evidence in the grill record; then edit for confirmed findings only. The `review-triage` skill runs the same verify-first discipline where a session has it, with two deliberate differences: it edits nothing until the user selects finding IDs, and its working ledger is an untracked per-branch file — the verdicts must still land in the grill record. The text here stands alone.
- **The grill record.** `grill-record.md` in the spec folder holds investigation evidence,
  useful mechanics and decision history: committed, append-only, never normative. Keep its header
  "Append-only grill/triage log. Never normative — decisions live in spec.md; nothing owes this file consistency."
  Entries are dated; IDs, if any, are `G-nnn`. Required behaviour and constraints stay in the spec;
  the implementer must not need this log to discover a hidden requirement.
- **The template owns the authoring rules.** Follow `../nub_specs/templates/spec-template.md`.
  Existing approved specs remain usable without reformatting. On a resumed grill, review changed
  or previously unreviewed scope; do not restart settled discussion merely to adopt new headings.
- **Growth smell.** Challenge new components, states, settings, retries, rules and clauses against
  the draft's complexity budget. Before adding a clause to resolve a finding, check whether an
  existing rule already covers it; deleting or shortening text is often the better fix. Remove
  repeated framing and mechanics rather than compressing the language.
- **Stay in the session's scope.** If a question opens a much larger area, ask the user whether to expand scope or note as `Future / out of scope`.
- **Stop on a card-size mismatch.** If the evolving design contains multiple independently deliverable outcomes, needs materially different owners/specs, or has a dependency tree too large to resolve coherently as one card, say plainly: `This appears too big for a single card because <evidence>.` Save every resolution made so far into the draft, leave remaining items visibly unresolved, and ask the human whether to continue, split the work, or rethink the scope. Do not prescribe a particular tool or workflow, and do not force the remaining questions through a single-card grill.

## Question rounds

Start with a short read-back of the purpose and overall change. Walk through each meaningful
section, explaining consequences with a concrete example where useful. Include scope written as
settled, not just `[ESCALATE]` markers. Do not read every paragraph aloud or require a yes for
every sentence; group related behaviour into a comfortable review round.

For a consequential addition or assumption, say: **"I propose X because Y. Leaving it out means
Z. My recommendation is …"** Distinguish a confirmed constraint from your chosen solution.
Ask whether to keep, change or drop the proposal. Silence leaves it unresolved; do not adopt it
or silently discard something necessary to the request. Preserve prior explicit agreement.

Check the proposed change against `.agents/shared/card-intent.md` § Working to it, which owns
the consequence definition. Explain actual consequences near the top; do not create an all-N/A
checklist in the spec. This is a check for scope, not a prompt to invent hardening or a broader
design. Routine implementation choices stay with the implementer.

Select the highest-impact questions whose prerequisites
are already settled. Questions in a round must also be independent of one another: if one answer
could change another question's wording, options or relevance, ask the prerequisite first. Do not
fill a batch with speculative follow-ups. Research may proceed alongside unrelated questions.

Reuse existing Open Question IDs, or assign stable labels without renumbering earlier questions.
Link each question to its affected spec section and keep the options, recommendation and main
trade-off concise. A concrete example earns space when it exposes a meaningful difference between
options; a long explanation can stay in the linked spec. Follow the shared pacing policy rather
than treating the whole unresolved list as a questionnaire.

**Written answers.** When the user prefers a larger set or asynchronous answers, read
`.agents/shared/spec-question-formats.md` § Written answers before presenting the questions
and when integrating their submitted answers.

**Save at a meaningful checkpoint.** Before the next question round or any pause/handoff, apply
all settled facts and accepted decisions from this round to their normative homes and affected
sections in one coherent edit per file. Preserve the resolution history and append the detailed
chronology to the grill record. Save clear partial answers even if other questions remain open;
never mark the unanswered ones resolved. Check the resulting diff and affected sections for
contradictions, then rebuild the queue. If saving fails, report it and recover before claiming
the decisions are recorded or moving to the next round.

### Visual decisions

When seeing alternatives or trying an interaction would help answer a particular question, read
`.agents/shared/spec-question-formats.md` § Visual decisions before preparing the visual.

## Steps

### 1. Locate the spec

This command reads the spec from `../nub_specs` and **writes ADRs there** (step 4), so that sibling repo must be present in the session. Read and follow `.agents/shared/locate-spec.md` as an authoring caller — the writable checkout's availability check first, then (when the argument looks like a Jira key — `[A-Za-z][A-Za-z0-9]*-\d+`, so `ENG-91`, `eng-91`, and a digit-bearing project key like `ABC2-123` all qualify) the case-insensitive key-prefix glob. If `../nub_specs` isn't available, stop and ask:

> ✗ `nub_specs` isn't available in this session — I can't read the spec or write ADRs.
>
> Clone it beside this repo, or add it to the directories this session can read, then re-run `spec-grill <KEY-or-path>`.

If the argument is a path to a `spec.md`, skip the key search but not the authoring checks: the path must be inside the `../nub_specs` checkout that locate-spec step 1 confirmed is on `main` and fast-forwarded. If it's a key and no spec is found (but `../nub_specs` is present): refuse with a pointer to `spec-draft`. On **missing locally**, follow locate-spec's reconciliation guidance before re-running; do not point at `spec-draft`.

Then read the authoring-rules block in `../nub_specs/templates/spec-template.md`: the Rules above defer to it, and every resolution must keep the spec inside it.

Then get the Jira card in hand and keep it for the whole run. A chained caller (`spec-draft` continuing into the grill) already holds it — reuse that (its re-read, if it wrote an INTENT), don't re-fetch. Otherwise use the key argument, or — for a path argument — the spec frontmatter's `jira_key`, and call `getJiraIssue`. The card is the intent source for the walkthrough, triage and cleanup. If the spec's Intent is missing or stale, refresh it word for word under `card-intent.md` and note it in the record; for a Subtask, read its parent. A card without an INTENT or exemption has nothing to copy; follow that resource's recovery. Two failure shapes:

- **`jira_key: N/A`** — the spec declares it has no card. Supported: say so once up front and continue on the spec alone.
- **A real key the fetch cannot return** — a card-dependent triage verdict stays `UNCLEAR`,
  cleanup requiring the card waits, and no approval is offered. Do independent work, report the
  Jira blocker and preserve unanswered items; see `nub_documents/engineering/Claude/using-claude.md`.

### 2. Read the spec end-to-end

Before the first question, read the full spec. Note:
- The material change and which parts were requested, explicitly agreed, or merely proposed;
  include consequential choices that have no uncertainty marker. Read relevant decision evidence
  from the record; a card's attribution label alone does not establish approval.
- All `[ESCALATE: ...]` markers (locations + content)
- The Open Questions section
- Any internal contradictions or thin sections that beg for stress-testing — a contradiction is open until the spec says which requirement wins (see Rules)
- **Current-behaviour claims without supporting evidence** in the spec or record — queue research.
- **Manual verification commitments with no owner or gate** — queue who runs them and what they
  block. Execution stays for later; only the commitment is settled here (`spec-draft` owns the rule).
- **Frontmatter fields left as `TBD`** — each is an unresolved question; queue it.
- **Contract-impact state** — inspect it using `.agents/shared/spec-contract-impact.md` § Grill decisions and propagation.
- **`release_note_tier` / `release_note_type` set to `None` / `N/A` on a card that looks externally-facing** (customer- or dev-visible behaviour, an API change) — query whether that's a deliberate "no release note" decision or a guessed default. A genuinely internal card (refactor, test-only, tooling) stays quiet.
- **The title / summary framing**, if a scope note flagged it — the framing must be confirmed with the human, not left as whatever the draft guessed.

### 3. Build the initial dynamic queue

For each unresolved item, record its resolution mode, what it depends on, and which downstream questions it blocks. Do not queue a vague downstream concern as though it were already a precise question; keep it in the working unresolved set until an upstream answer makes it askable.

Order questions roughly by **what unblocks the most downstream design**:
1. Scope boundaries (what's in / out)
2. Architectural shape (which system owns what)
3. Contracts and integration points
4. Failure modes and operational behaviour
5. Polish (naming, conventions, doc location)

Within each layer, prioritise questions that affect code you'll write soon. Contract-impact classification is part of layer 3 and must be resolved before the spec can leave draft; do not postpone it as release polish. A legacy `OQ-C` row is handled by the coherence pass in step 6, never by asking the human.

### 4. Grill

For the next independent round selected under Question rounds, assess each item:

1. **Resolve according to mode**:
   - `FACT / RESEARCH`: do a focused investigation. Record the authoritative evidence and resulting fact; ask the human only if the sources genuinely conflict or authority is unclear, not merely for ritual confirmation.
   - `DECISION / HITL`: investigate current facts and constraints, then include a concrete question, recommendation and trade-offs in the round. Wait for the human's answer before adopting a decision.
   - `PROTOTYPE / HITL`: agree the smallest throwaway artifact and the exact decision it must inform. If it cannot be produced safely within this spec-only session, save the draft and pause with the next action recorded.
   - `PREREQUISITE`: record the owner and observable completion condition. Resolve it only when the prerequisite has actually happened.
2. **Contradiction check**: does the evidence or answer conflict with anything in the spec, codebase, card, contract-impact state, or an earlier resolution? If yes, surface it. A fact/decision conflict does not let the fact choose the desired behaviour; it makes the trade-off explicit for the human.
3. **Compatibility challenge where relevant**: follow `.agents/shared/spec-contract-impact.md`
   § Grill decisions and propagation before accepting a break.
4. **ADR check**: does this decision clear the ADR threshold? If yes, create an ADR in `../nub_specs/adr/` numbered after the highest existing.
5. **Integrate the settled round** at the checkpoint defined in Question rounds: put accepted
   outcomes in their spec homes, append the resolution history to the record, then remove resolved
   questions/markers. Keep unsettled items visibly open and update affected frontmatter.
6. **Recompute the queue**: remove invalidated or duplicate questions, add newly exposed precise questions, update dependencies and resolution modes, then select the next independent round. Run the card-size mismatch check before asking it.

### 5. Check review coverage

Finish the rounds only when the unresolved set is empty (apart from a legacy `OQ-C`, handled in
step 6) and the human has had the material change explained, including consequential additions.
If a section has not been covered, explain it now.
This is not another confirmation question; the final read-back and approval are step 7.

### 6. Coherence pass

Read `.agents/shared/spec-condense.md` and do its coherence/readability pass in this session.
Apply its card-read prerequisite before editing: a failed real-card read skips this pass, leaves
legacy `OQ-C` untouched, and goes directly to the blocked summary in step 8. `jira_key: N/A` is supported.
It also handles a legacy `OQ-C` row. Reopen genuine unresolved decisions; cleanup alone does not
require another session or another round of approval.
If this pass reopens a decision, return to steps 4–5 before the final read-back in step 7.

### 7. Final read-back and approval

Before offering, reusing or writing a status, apply `.agents/shared/spec-contract-impact.md`
§ Status eligibility. A breaking spec remains at `review` until the required independent review
accepts the break and consumer-coordination plan; the author's scope agreement cannot replace it.

Give a brief final read-back of what will change, meaningful boundaries and accepted trade-offs.
Name the consequential additions the human kept or changed. Ask whether that is the agreed change
and offer the appropriate `review` or `approved` status in the same question. Do not ask again
when existing evidence shows the human already explicitly approved this unchanged final scope,
in this session or earlier; retain or reference that approval.

Before offering approval, check there are no live `[ESCALATE]` markers, `TBD` frontmatter fields,
unanswered Open Questions or consequential proposals awaiting acceptance. Contract-impact state
must be coherent, required Jira labels propagated, and flagged framing confirmed. Resolved history
may be in the record or legacy ticked/struck rows. Record the final human approval and date in
the record and update only to an agreed, eligible status. Approval to publish alone does not settle
scope questions.

### 8. Summary

Print a wrap-up listing:
- Decisions resolved (one line each)
- Facts established and their evidence (only those material to the decisions)
- ADRs created (path + title) if any
- Breaking-change classification, named consumers, and Jira-label propagation result
- Anything explicitly deferred to a later iteration
- **Publication.** The spec edits, any ADRs and the grill record are local changes in the
  `nub_specs` checkout until they are committed and pushed to its `main` (`SHARED-AGENT-GUIDANCE.md`
  § Reading other repositories: no branch, no PR). If a real-card fetch failed, list the local
  files and blocker without inviting publication until that card has been read. Otherwise list
  the unpublished files. In that unblocked case, the developer publishes them, or asks you to
  under authority they have already given; this adds no approval
  step. Once pushed, the approved SHA for downstream links is that pushed commit
  (`git -C <nub_specs checkout> rev-parse HEAD`, confirmed present on `origin/main`). Until then,
  `implement`, card grooming and PR links read the published version, not these edits.

End the wrap-up with exactly one of these outcomes — evaluate in order, first match wins:

- **Blocked or unresolved** — the card fetch failed, an item remains unresolved, or final human
  agreement has not been given: report what is needed. Do not hand off to implementation.
- **Fully resolved and agreed** — otherwise:

  ```
  ⮕ Next step: publish the spec, then at this task boundary compact the session (`/compact` where your client supports it, or start a fresh one) and run  implement <KEY>  to plan and build it.
  ```

  A `jira_key: N/A` spec has no `implement` route (that command takes a Jira key): hand the implementer the spec path instead.

## What this skill is not

- Not a forum for new requirements. If the user wants to *add* scope, surface that and ask whether to expand or note as future work.
- Not a code editor. Spec-grill writes to the spec and (optionally) ADRs. Code changes happen in implementation skills.
- Not committing on the user's behalf unasked. The spec edits are local until published, as the summary's **Publication** line describes.
