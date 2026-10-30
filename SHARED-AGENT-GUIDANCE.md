# Shared Agent Guidance

Engineering guidance shared by every coding agent working in a Noetica `nub_*` repository —
Codex, Claude Code, Copilot and Cursor alike. Each client's normal entry point points here, so
this is the one home for the rules below; none of them are restated in a client-specific file.

Repo-specific conventions live in that repository's own `AGENTS.md`, which is never overwritten
by the sync. Where the two disagree, the repo's `AGENTS.md` wins.

**For code review**, follow `.github/copilot-codereview.md`. That standard is not duplicated
here — it is the single home for review calibration and the platform and governance facts
reviewers need, whichever client is reviewing.

## Product & docs orientation

Synthesys is Noetica's outbound dialling platform — predictive dialler + recycling core, the NVP
telephony engine, management web apps, and runtime APIs; per-tenant Azure SQL. It is
**mid-migration**: current = per-tenant VMs with Spider (TCP/IP RPC) + WCF; planned = Azure
Container Apps behind YARP with NATS/JetStream replacing Spider/WCF (NVP stays on a shared VM).
When an answer differs between the two states, say which one it applies to.

Canonical cross-repo docs live in the sibling repos `nub_documents` (C4 diagrams in
`architecture/puml/`, DB schema in `database/schema-reference.md`, engineering guidance in
`engineering/`, cross-repo ownership/data-flow map in `engineering/repo-map.md`) and `nub_specs`
(specs + ADRs). Respect the schema's relationship-confidence labels, and read `repo-map.md`
before searching sibling repos for who-owns-what.

For access and editing conventions, follow [Reading other repositories](#reading-other-repositories).

## The golden path, card to merge

The route most work takes. Each stage names a skill; the detailed rules live in that skill's own
body, not here.

| Stage | Entry and handoff |
|---|---|
| Draft | `spec-draft` proposes a concise change from the card; `spec-grill` walks the human through its scope, additions and open decisions |
| Start implementation | `implement` works from the resolved spec, and chains `branch-from-jira` when you are not already on the card's branch |
| Review locally | `review-code` runs independent review and repairs; `create-pr` revalidates its handoff. `pre-pr-review` remains an explicit-choice fallback |
| Open a PR | `create-pr` opens a **draft** PR, does its Jira grooming, then asks whether to mark it ready for review when the full-suite result allows it (its step 19) |
| Respond | `respond-to-pr-feedback` handles all PR comments from humans and tools, plus failed checks; available feedback can also be handled on drafts |
| Finish | `respond-to-pr-feedback` offers to squash-merge an approved PR with explicit human confirmation; verification stays with people |

Delivery through a draft PR is the normal offer of an `implement` run. Its step 7a owns the
single delivery question, reuse of authority and narrower instructions; `review-code`'s
**Invocation and scope** owns reviewer-sharing consent. An unanswered question is not consent.
Marking the draft ready is a later human decision. Review response starts when requested;
`respond-to-pr-feedback` owns the approved-PR merge offer and its separate human confirmation.

**Between stages, compact rather than restart.** The spec, card, branch and plan file carry the
handover, so at a task boundary compact the conversation where the client supports it (`/compact`
in Claude Code and Codex) or start a fresh session. A step that needs a reader who did not write
the text says so itself; an ordinary spec-grill can finish in the same session.

**Make every handoff actionable.** State what is complete, what happens next, and whether the agent
is continuing or waiting. If the human must act, give one copyable next command in their client's
syntax, with the actual card/PR identifier where known. Explain what that command authorises.
For the review invocation and provider-consent wording, use `review-code`'s **Invocation and scope**
section; for draft/ready/feedback transitions, follow `create-pr`. Reuse existing authorisation as
`implement` step 7a and that section define it.

**One push per round to a ready PR, and no unrequested Copilot review.** Once a PR is ready for
review, push once per feedback round or local review loop, not per fix or per pass, and never
request a Copilot review without the developer's go-ahead. `respond-to-pr-feedback` asks which
local review each round's fixes get and names the routes that start a Copilot review;
`review-code`'s **ready** action says when that single push happens.

**Automated review.** GitHub Copilot and the replacement in
[noe_pr_shepherd](https://github.com/Noetica/noe_pr_shepherd#readme) provide the current review path.
The replacement runs locally on a best-effort basis and skips drafts; it is not an always-on
service. It approves only when its completed review and required checks support a clean result on
the reviewed commit. Where Copilot approval is required, approval also needs Copilot review or
second-model arbitration; the runner README owns that policy and its exemptions. PRs authored by
the account it publishes as get an advisory comment, never a counting approval. The replacement
may push small fixes to a ready PR, which the author pulls before continuing local work. People do
not push to a colleague's PR and then approve it. A PR-body or card edit alone does not trigger
another run. Keep the description, card and test claims accurate; never present an older review as
covering changed requirements or an incomplete run as approval.

The author retains a brief completion check within implementation: inspect the final diff for
accidental changes, compare it with the agreed requirement, and verify that test claims describe
the final work. Independent local review then follows `review-code`; `create-pr` step 2
owns evidence acceptance, prerequisite failures and the explicit legacy fallback. The
[Jira-to-merge walkthrough](https://github.com/Noetica/nub_documents/blob/main/engineering/Claude/jira-to-merge-workflow.md)
and [PR guidance](https://github.com/Noetica/nub_documents/blob/main/engineering/pull-requests.md)
go into more depth; where they disagree with the canonical skills here, the skills win.

**Not every change needs a spec.** `branch-from-jira` stands alone for work that just needs a
branch, and `implement` has a minor-work path for small changes with no spec. Use the lightest
route that fits: simple bugfix → direct change; minor feature → a short plan first; major feature
→ spec-led.

**Invoking a skill.** Codex, Copilot and Cursor discover these skills from `.agents/skills/`
directly; Claude Code discovers them through thin adapters under `.claude/skills/`, which forward
to the same canonical bodies. Each client has its own explicit form — Codex uses `$name`, Claude
Code, Copilot and Cursor use `/name`. All of them also select a skill from an unambiguous
natural-language request, so "open a PR for this" or "grill the spec for ENG-23" reaches the same
workflow with the same arguments. If a client cannot discover them, reading
`.agents/skills/<name>/SKILL.md` directly still works — that is a backup, not the normal route.

Hub assets are synced by default; hub-only exceptions must be stated and reasoned. The rule and
its file-level enforcement live in the hub
[README's synced-files inventory](https://github.com/Noetica/nub_model_repository/blob/main/README.md#synced-files-inventory).

Use these skills from the repository checkout so downstream work uses the versions delivered by
the approved standards sync. Do not copy, link or junction repository skills into user-level skill
directories. If discovery fails, use the direct-read fallback above.

## Prefer the simplest solution that satisfies the request (YAGNI)

Deliver what the human asked for, within the scope they agreed. If a better approach requires a
materially different change, explain it and obtain the human's decision before adopting it. `.agents/shared/card-intent.md` §
Working to it owns the boundary between consequential decisions and routine implementation,
including additions proposed during review.

Before writing code:

1. Does this need to exist at all?
2. Does the standard library or platform already provide it?
3. Does existing code or a published shared package already provide it?
4. If bespoke code is still needed, keep it local and small; introduce an abstraction only for
   demonstrated reuse.

Do not add speculative abstractions, dependencies, configuration, or unrelated cleanup. YAGNI does
not override explicit requirements, established layering, required test seams, input validation at
trust boundaries, data-loss prevention, security, accessibility, or red/green/refactor.

**Shared .NET code:** before implementing a utility or helper, check the shared-package catalogue —
`engineering/shared-dotnet-packages.md` in `nub_documents` (follow
[Reading other repositories](#reading-other-repositories)). Reuse a suitable published `nub_utils_extensions` package; don't use packages marked
`Legacy/frozen` or `Under review` in new code, and prefer a BCL/platform feature over a thin wrapper.

## Write sufficient documentation

Document the purpose and what the code and tests do not make obvious. Do not narrate the code or
enumerate every case the tests already cover. Keep only what helps a reader make a decision.

## A comment that promises behaviour needs a test that proves it

When a docstring or comment asserts a *guarantee* — "X never happens", "Y blocks Z", "this has no
access to W", "the caller must always …" — first remove it if the code and tests already say
the same thing. Otherwise write the test that names that property, or soften the wording to
describe intent rather than a guarantee. Prose is not enforcement, and a
stale guarantee is worse than no comment: the next reader, human or agent, treats it as a
specification. This usually breaks **later**: a subsequent edit invalidates a comment nobody
re-read. So before declaring work done, re-read every comment and docstring the change touched
against the *final* code. Defects of this class, a contract between components or between a
comment and its code, routinely pass the tests and the review, which is why the obligation sits
with the author.

When fixing a boundary condition, test the neighbouring outcomes that determine the decision—not
only the reported failure. For example, distinguish missing, unreadable and valid state, or
different inputs that could produce the same identifier. Check both that invalid cases are
rejected and that legitimate cases still work. Prefer extending an existing behavioural test over
adding a separate test that exercises only the new condition.

**Where the prose *is* the implementation** — the skill bodies under `.agents/skills/`, this file,
the synced standards — there is no code for a claim to drift from, so drift is prose against other
prose, and its dominant cause is **restatement**: a fact written in more than one place goes stale
everywhere but one. Prefer a single source and a pointer over repeating a fact (a count, an output
string, another document's behaviour, a file's contents). Where restatement is unavoidable and
load-bearing, add a lockstep-style check rather than an instruction to be careful. Re-read the
neighbours after each fix, not just at the end, because the fix for one restatement often
introduces the next. No check catches **contradiction between two documents**, so when a change
makes a claim, open the other files that claim touches. In `nub_model_repository`, where the shared
assets are authored, `scripts/inventory_lockstep` and `scripts/prompt_xref` are those checks, and
`scripts/README.md` is the home for what they cover. Downstream copies are read-only, so there is
nothing for them to check there.

## Tool use

Optimize for a correct, reviewable result and the developer's time and attention. Extra research,
tests or a useful second opinion can be worth their cost; avoid round trips that add no evidence
or decision. Fewer tokens or tool calls alone are not a measure of better work.

### Reliable calls and focused retrieval

- Use the simplest suitable tool and its actual schema. Prefer the client's edit/patch tool for
  ordinary file changes and existing commands or scripts for operations they already support.
  When a new script needs complex quoting, write it with the file tool, then execute it. A quoted
  heredoc is not inherently broken: shell quoting, tool-argument encoding and the script language's
  own string literals are separate concerns. Keep data out of generated command text where a
  structured argument or input file will do.
- Search for the relevant files or symbols first; request the fields and output needed for the
  question. Reuse evidence already in hand while it remains current. Read full documents or
  surrounding code when the task requires that context; a truncated result is not complete evidence.
- Batch independent reads when supported and inspect every result. Apply related, already-understood
  edits as a coherent patch, rather than one call per line. Keep dependent operations, approvals and
  test-driven feedback in order; later evidence legitimately creates another edit.
- On failure, inspect the arguments and error before retrying. Distinguish transport/quoting errors
  from invalid source or a failed operation; simplify the method when it is the cause. Do not keep
  varying escapes blindly or suppress failures to make a batch appear successful.

### Questions and decisions

Look up discoverable facts; research delays only questions that need its result. Default to small
rounds of related, independent questions that fit one comfortable read, usually two or three. Ask
one when its answer could change the other questions, or the decision needs sustained attention.
Honour a request for one-at-a-time discussion or a larger ready-to-answer set; do not add a pacing
question by default.

Give each question a stable label, the decision needed, a brief recommendation and its main
trade-off. Use a native picker for short choices, or concise chat and linked detail/answer sheets
for evidence-dense questions. Do not require a custom form for an ordinary conversation. A
recommendation, preselected option, blank answer or silence is not consent. Do not impose an
automatic answer timeout; if a picker expires, preserve the unanswered question and offer it in
plain text. Continue only work that does not depend on the missing answer.

### Delegation and second opinions

Delegate bounded, independent work when the additional perspective or parallel progress justifies
the setup and coordination. A handful of direct calls rarely needs a subagent. Give each helper
an explicit scope and stop condition; retain responsibility for design decisions, interpretation
and integrating its output. Helpers do not continue into commits, pushes, PR creation or Jira
transitions. Their checks do not replace the author's verification or a required independent
review. Consult an available advisor when a consequential ambiguity would benefit from another
view; otherwise decide in the main loop and explain the trade-off. Model choice follows
[Models](#models).

### Reading other repositories

**Reading any repo you're not working in**: don't assume a local `../<repo>` checkout — read from
the remote with `gh repo read-file <path> --repo Noetica/<repo>` (browse with
`gh repo read-dir [<path>] --repo Noetica/<repo>`). No clone needed and it returns current `main`,
so prefer it for cross-repo lookups even when a possibly-stale local copy exists. (Needs `gh` ≥ 2.95;
`brew upgrade gh` if missing.)

**Reading a repo is not the same as being able to change it.** The remote read above covers
lookups only. Writing a spec or an ADR needs an accessible, writable `nub_specs` checkout in the
session — a workflow that must write one says so and stops when it is missing. Another client's
permissions are not evidence that this session has them: check the session you are in.
Once you have that checkout, `nub_specs` takes every change **directly on `main`**. Its ruleset
rejects branch creation outright, so do not create a branch or open a PR there. This is the rule's
one home: branch/PR workflows stop first in `nub_specs`, before creating or pushing a non-main
branch, opening a PR or moving a card for PR review. Direct publication to `main` follows the rule
below. A repository is `nub_specs` when the owner and name at the
end of any of its remote URLs are `Noetica/nub_specs`, whatever the URL form (HTTPS with or without
credentials or `.git`, `git@host:` or `ssh://`, including a host alias), or when its root holds
`templates/spec-template.md` beside a `specs/` directory. A spec or ADR is published when it is
committed and pushed to `main`; that pushed commit is its approved SHA, the revision a pinned link
should name. Code repositories keep their normal branch and PR workflow.

### Checking schema and data against UAT

`scripts/uat-db-query.ps1` queries the Fabrikam UAT database through a read-only login. Use it to
confirm that a table, column or key really exists, or to see realistic data, rather than guessing.
Before your first query, read `nub_documents/database/uat-readonly-access.md`: what the login can and
cannot see, and how to treat the data. Testers share the database and some tables are very large,
so shape queries and choose a timeout to suit. Never put row data into a PR, card, spec, commit,
comment or test fixture; describe its shape instead. `schema-reference.md` stays the canonical
schema: UAT confirms a name exists, it does not define the schema. If the firewall blocks you, ask
the developer before running the script's `-AddFirewallRule`.

### Writing rich text through the Atlassian MCP

Before writing any Jira description or comment (`editJiraIssue`, `createJiraIssue`,
`addCommentToJiraIssue`), read and follow `.agents/shared/jira-rich-text.md`: the format to send,
the escaping traps the schema does not show, and how to verify what rendered.

## Jira

For description and comment formatting, follow
[Writing rich text through the Atlassian MCP](#writing-rich-text-through-the-atlassian-mcp).

### Conventions

- Default to the **ENG board** ("Engineering", key `ENG`). Use a different board only when
  explicitly asked. **Never create new cards in NUB** — engineering work moved NUB→ENG on
  20 Jul 2026 (one-time cutover). Old `NUB-nnnn` references still resolve in Jira (URL redirect and
  search both work; the numeric issue ID never changes on a move — prefer it for mutations); the
  canonical old→new key mapping is `nub_specs/jira-migrations/`. Cards still **draining** in NUB
  (in-flight at cutover) keep their NUB keys and the old NUB workflow until done — transitioning
  those is fine, creating new ones is not.
- Propose a card (title + one-line summary) and get an explicit go-ahead before creating it or
  editing its content. Reuse explicit permission already given for that card and content; do not
  ask again merely to satisfy the proposal step. Status transitions and sprint membership are mechanical side effects of the
  skills that apply them (`.agents/shared/jira-transition.md`, `.agents/shared/jira-sprint.md`), not
  card edits that need their own go-ahead.
- Placement: new cards land in **Discovery** (ENG's intake status — the workflow default; no
  sprint). A groomed, agreed card moves to **Ready** and gets ranked — sprint planning pulls from
  the top of the Ready list. Don't pre-assign cards to future sprints, and don't put Discovery
  cards in the live sprint (both were NUB-era workarounds; ENG's ranked backlog + Intake board
  replace them).
- Keep a new card small: the human's `## INTENT` and only context needed to understand or
  investigate it. A Bug can use a short problem statement, expected versus observed behaviour and
  useful evidence instead. Do not invent a design, acceptance checklist or approach section to
  fill space. `.agents/shared/card-intent.md` owns early-card content, exemptions, honest attribution
  of proposals and decisions, and carrying the INTENT to the PR. Read it before proposing a card.
- Every new ENG Task, Story or Bug sets **Release audience** (`customfield_10532`): `Customer facing`
  when customers will notice the change, otherwise `Internal`. Put your choice in the card proposal
  so the human confirms it, then send it on create as
  `additional_fields: {"customfield_10532": {"value": "Internal"}}`. Don't set the
  `customer-facing` / `internal` labels yourself — a Jira rule syncs them from the field, and the
  release notes (ENG-828) read the field. Epics don't take it. End the new card's description with
  an empty `## Release notes` heading; `.agents/shared/release-notes.md` says who fills it, and when.
- Don't pre-assign ADR numbers in card titles or text — the number is allocated when the ADR lands.
- Don't spawn follow-up cards while working a card. If we find a spec's design missing the requester's 
  intent, propose amending the spec in the current card rather than opening a sibling card. Open a 
  new card only for work the spec's Non-Goals explicitly exclude, and only after the requester agrees.

## Models

Model choice belongs to the developer and their client's configuration. No skill in this set
prescribes a model for itself, its subagents, or an advisor consult. Where a workflow suggests
delegating bounded work to a subagent, it describes *when* that pays, not *which* model to use.

The lens loop’s committed reviewer selection configures external review subprocesses; it does not
prescribe the model running a skill, subagent or advisor. Its team default and personal override
are documented in `scripts/pre_pr_lens_review/README.md`.
