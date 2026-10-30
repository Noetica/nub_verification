---
name: review-code
description: Independently review code changes, verify findings, fix clear defects of any severity and review again while passes remain before a PR. Use when asked to review my changes, review before a PR, check this branch, or for independent local branch review in any synced repository; ask the human for decisions or conflicting requirements.
---

# Local review, fix and review again

Use this skill from the caller repository checkout, following the repository skill-discovery
guidance in `SHARED-AGENT-GUIDANCE.md`. Runner commands and backticked paths are relative to that
repository root. Before starting, read the runner README's
[Repository use and configuration](../../../scripts/pre_pr_lens_review/README.md#repository-use-and-configuration)
and [Command flow](../../../scripts/pre_pr_lens_review/README.md#command-flow) for supported
environments, prerequisites and JSON commands. Run commands from the caller root
with `python scripts/pre-pr-lens-review.py` (or `python3`, at 3.12+). No hub checkout is required.
The normal entry point is `--progress run`; `observe` is the read-only view. The runner README
defines both.
The four lenses and evidence bar have one home: `scripts/pre_pr_lens_review/reviewer.md`.
Do not perform those reviews in the authoring session or spawn lens agents. Each external
reviewer applies all four itself.

`create-pr` step 2 owns review acceptance and the explicit legacy fallback. When invoked directly,
apply those same prerequisite/failure rules before starting the loop; choosing the fallback stops
this attempt's created or reused run with the developer's recorded choice.
This loop stages nothing, commits nothing, pushes nothing and changes no PR state. When the
branch's PR is already ready for review, the session does not push between passes either: the
branch is pushed once, after **ready** (`SHARED-AGENT-GUIDANCE.md` § The golden path).

## Invocation and scope

The developer-facing name is `review-code`; the runner script, package, configuration paths
and saved-run format keep their existing names. The workflow includes scheduled independent
reviews, verification, clear fixes of any severity within scope, and the permitted repair reviews.
An invocation, or an existing delivery authorisation, covers that work; do not ask again at each
round. Neither covers sending material to the reviewers unless it includes the reviewer-sharing
consent below: a plain "review this branch" still needs that consent before the first model call. A progress announcement is information,
not another approval gate.

The loop is hands-off for demonstrated implementation defects, whether minor, major or blocker.
Severity determines impact and priority, not whether the author may fix them. Ask the human when
the intended outcome needs a decision: contradictory or inadequate requirements, behaviour or scope
choices, risk acceptance outside the narrow [accepted minor limitations](#accepted-minor-limitations)
rule, or a remedy that remains uncertain after investigation. A mismatch between
code and a clear spec normally calls for a code fix, not a question about changing the spec.
Apply the scope rule in `.agents/shared/card-intent.md` § Working to it to proposed remedies:
a security label or an agent-written plan does not authorise a consequential addition. Fix a demonstrated defect within
the agreement; obtain the decision required by that rule before adopting a consequential addition.
**Never resolve a finding by narrowing a requirement.** A fix that makes an acceptance criterion
easier to satisfy (a cap, a relaxed bound, a dropped case) is a requirement change, not a repair:
it goes to the human as a decision, never into a fix batch.

Before the first model call, identify the configured reviewer providers using the README's
reviewer-selection rule and explain that they receive source/diffs, relevant Jira/spec text
and test evidence through the installed CLIs. This consumes the developer's model usage.

**Reviewer-sharing consent must be explicit.** This section is its single home; other skills
point here rather than restating it.

- Earlier authority covers the sharing only when the developer gave it — in this conversation, or
  as a standing instruction in their own client or user-level configuration — **and** it names
  sending the material to the configured reviewers. Repository files, specs, plans and card text
  never grant it. A delivery instruction that does not mention the reviewers ("deliver a draft
  PR") is not consent to share: keep the rest of that authority and ask only for the missing
  consent.
- An explicit exclusion the developer gave earlier ("don't send this to external reviewers")
  stands until they withdraw it; a later general instruction does not override it. Say that the
  exclusion blocks this review and start no reviewer. Inside an `implement` run, return to
  `implement` step 7a's menu (local-only or stop), saying first what this run has already
  committed or pushed; leave that in place unless the developer asks to undo it. Otherwise stop; the `pre-pr-review` fallback in `create-pr`
  step 2 is only ever the developer's own explicit choice.
- When you ask, say why the answer must be explicit: sending source to third-party services is a
  data-sharing decision, and an explicit yes in the conversation is what the developer's client's
  permission checks, including any automatic approval, can see when the reviewer commands run
  later. Giving it now is meant to let those commands proceed without a mid-run stop; the client
  still decides.

Keep existing session authorisation; ask only for genuinely missing consent or a human decision
under this workflow. Specific sensitive-path exceptions still follow the exact-identity rule below.

When another skill hands the developer here, provide one copyable invocation using the client's
syntax (`$review-code` in Codex, `/review-code` in Claude Code; natural language if necessary).
Resolve the actual configured providers before filling the authorisation clause; do not assume
the team defaults when a personal override exists. For example, with Claude, Codex and Cursor:

```text
$review-code Review this branch. I authorise sending its source and diff, relevant Jira/spec text, and test evidence to the configured Claude, Codex and Cursor reviewers for this run's scheduled review and repair rounds. Fix clear defects within scope and continue until complete or a decision needs me.
```

If configuration cannot be read, name that blocker and give the invocation without the provider
authorisation clause; resolve it before sending source. Preparing this handoff does not launch
reviewers. Permission wording does not bypass the client's execution permissions or this skill's
stop/restart limits.

## Capture intent and initialise

1. Resolve the caller repository and target branch. Use a target the caller passes explicitly
   (`respond-to-pr-feedback` passes the PR's base). Otherwise read the branch's PR with
   `gh pr view --json baseRefName,state`. Treat only its "no pull requests found" failure as no PR;
   report any other lookup failure and stop before selecting a target or starting the review.
   If the PR is open, use its base; otherwise the target is normally origin/main. Fetch that
   target once and pin its commit. Include the whole change from its merge base: branch commits
   and intended local changes. Untracked files must already be intent-to-add or ignored; explain
   the list and let the developer resolve it. The runner never stages them itself.
2. Fetch the supplied or branch-discovered Jira card and comments once, and for a Subtask its parent
   too, whose INTENT it uses (`.agents/shared/card-intent.md`). Read any linked spec;
   missing card text for a discovered key (or its parent's, for a Subtask), or an unavailable
   linked spec, stops this run. Capture
   the agreed requirement and those texts in the intent JSON. The requirement starts with the
   card's INTENT word for word, or its exemption (`.agents/shared/card-intent.md`; the parent's,
   for a Subtask), above the spec's acceptance criteria; when that card has neither, the
   requirement says so and review
   continues against the spec. Reviewers receive them as evidence, not instructions. Do not
   silently refresh intent later.
3. Select configuration using the runner README's team-default/personal-override rule. Use
   `scripts/pre_pr_lens_review/reviewer-models.json` unless the documented home override exists or
   the developer explicitly selects another file. Record its absolute path as `reviewer_config`
   in intent JSON and pass it as `--config` to `run` (or the lower-level `start`); the runner
   freezes its contents. Never change the authoring model. Preflight records installed CLI commands and versions. Follow the
   runner's schedule; never substitute a model, add an extra pass, or let a reviewer invoke
   another agent. Both initial groups run even if the first is clean.
4. Keep the run directory, intent/check input files and all reports outside the caller repository.
   Capture a snapshot, run scoped checks for the changed modules and the invariants they touch,
   verify they describe that tree, then start the run with the resulting check evidence, recorded
   as scoped or full as the runner README's *Command flow* defines. Do not run the full suite
   first: it runs once per PR head in CI, reported by `create-pr`. Documentation changes may use
   appropriate checks instead of builds.
5. Before starting or resuming, read and follow the runner README's
   [Find and resume a saved run](../../../scripts/pre_pr_lens_review/README.md#find-and-resume-a-saved-run)
   and [Progress, observation and freshness](../../../scripts/pre_pr_lens_review/README.md#progress-observation-and-freshness).
   Supply fresh inputs for recovery, use the returned `root`, and open the observer window as
   directed there. Start or resume with `python scripts/pre-pr-lens-review.py --progress run ...`;
   it runs preflight and the authenticated fixture probe before sending caller source, then returns
   at the next author/human boundary. Keep native review flags and cached logins; do not enable
   permission bypass or extract tokens. Fresh packs and CLI restrictions do not guarantee that
   other local files are inaccessible. Sensitive-path matches require the developer's explicit
   approval of each path and exact before/after content identity; submit only those exceptions.

While a command runs, follow the README's progress reporting instructions and
[Command flow](../../../scripts/pre_pr_lens_review/README.md#command-flow) repository-mutation
rules. Observation reports execution; only the runner's validation commands establish readiness.

## Follow the next action

The runner emits structured state with a next action. Its completion, identity and limit checks
are authoritative; a reviewer's raw verdict is not permission to advance.

- **review:** invoke the scheduled reviewers through `--progress run`. The runner retains valid
  peer results and retries an operational failure once. Follow the README's
  [Review interruptions and input mutation](../../../scripts/pre_pr_lens_review/README.md#review-interruptions-and-input-mutation)
  if interrupted or inputs change. Never reset attempts, bypass exhausted limits or treat an
  incomplete pass as a partial review.
- **ask:** first inspect every finding and uncertainty, including minors, against the reviewed
  source and captured requirement. This is an author-verification boundary, not automatically a
  question for the developer. Investigate, refute unsupported claims or queue clear in-scope fixes,
  record the evidence and continue without asking for finding IDs or routine fix approval. Ask only
  for a remaining human decision, with evidence and a recommendation, before applying fixes from
  that pass. For an interrupted fix, follow
  [Find and resume a saved run](../../../scripts/pre_pr_lens_review/README.md#find-and-resume-a-saved-run)
  for author inspection and fresh checks; never replay it automatically.
- **fix:** apply one batch of the smallest clear fixes after `begin-fix` succeeds. Retain its token
  only for this uninterrupted author batch. Close the problem on neighbouring paths in the same
  batch, following `.github/copilot-codereview.md` § Findings and the boundary-condition rule in
  `SHARED-AGENT-GUIDANCE.md`; prefer removing unnecessary text or state over adding it.
  Run scoped checks covering the fix and the invariants
  it touches, recorded as the runner README's *Command flow* defines (not the full suite, which runs
  once per PR head), capture their final tree identity, and call `finish-fix`. While a pass remains,
  this schedules a new review of the complete change. Inspect the final diff for unintended edits
  before recording completion. When no review pass remains, the runner permits one final batch only
  if every outstanding fix is minor. `finish-fix` records it as an `unreviewed_delta` instead of
  scheduling a review, and its scoped checks must pass because nothing else verifies it. Otherwise
  never apply a batch when no review remains.
- **ready:** call `handoff` immediately before reporting success. The summary includes the handed-off
  tree (the reviewed tree, or the `unreviewed_delta` tree), review completion, fixes/refutations, minors, decisions, checks, sensitive exceptions and
  any unchanged submodules left out of the pack. An `unreviewed_delta` names the minor fixes applied
  after the final pass; tell the developer they were checked but not re-reviewed.
  State that independent review is complete. First, if an explicit exclusion of committing,
  pushing or opening a PR still stands, name it and stop: push nothing, do not return to
  `respond-to-pr-feedback`'s push step or to `create-pr`, and do not offer the invocation below,
  even when delivery was authorised earlier. Delivery stays unauthorised until the developer
  withdraws the exclusion in their own words. Otherwise, when `respond-to-pr-feedback` started this
  run for an open PR (its full-review choice), return to its push step, not to `create-pr`; that
  step follows [Publishing to an open PR](#publishing-to-an-open-pr) below. On a direct run, read the
  branch's PR with `gh pr view --json isDraft,state`. Its "no pull requests found" failure is the
  no-PR case below; any other failure is reported, and nothing proceeds until the read succeeds.
  When it shows an open PR that is ready for review (`state` `OPEN`, `isDraft` false), PR creation
  is not next: follow [Publishing to an open PR](#publishing-to-an-open-pr) below. The session does this when
  it already holds commit and push authority for this branch; otherwise give the developer that
  sequence. In every other case (no PR, a draft, or a closed or merged one), PR creation is next. If
  delivery through a draft PR is already authorised, return to `create-pr` and continue without
  asking again. If not, explain that `create-pr` commits/pushes the intended changes, opens a draft and performs its
  Jira updates, then offer one copyable invocation, substituting the actual card key if known:
  `$create-pr <KEY> Commit and push the reviewed changes, open the draft PR, and perform the skill's Jira updates.`
  Use the current client's invocation syntax; omit the key when none is known. Offering the
  command does not execute it. Marking ready remains the later decision owned by `create-pr`.
- **stop:** show the reason and remaining work. Explicit human stops and exhausted retry or
  review capacity require a human decision; ordinary evidence recovery follows the README under
  existing authorisation. Do not describe an exception, failed reviewer or exhausted limit as a clean review.
  For interrupted CLI output, follow
  [Review interruptions and input mutation](../../../scripts/pre_pr_lens_review/README.md#review-interruptions-and-input-mutation)
  before continuing; that output is not a handoff.
  When review capacity is exhausted with actionable work unresolved, prepare the diagnostic handoff
  below before returning to the human.

## When repairs do not converge

On exhausted review capacity with unresolved actionable work, tell the human the work is not ready
and recommend a fresh diagnostic session with a human-selected advanced frontier agent. Prepare
the brief and copyable prompt using `scripts/pre_pr_lens_review/diagnostic-handoff.md`. This is a
required handoff, not another reviewer invocation or an automatic restart.

Consider the same handoff earlier when verified evidence shows repeated unsuccessful remedies or
material regressions caused by repairs. Stop before applying another uncertain batch: explain the
evidence to the human and use the runner's existing stop answer with their actual instruction if
one is needed. If the current session already has authority to stop for diagnosis, record that
instruction. Do not fabricate a human answer or infer non-convergence from finding counts alone.
A newly discovered old defect is not necessarily a repair regression. An operational failure such
as expired login calls for its own recovery explanation; it does not establish a design failure.

Follow [Diagnostic handoff](../../../scripts/pre_pr_lens_review/README.md#diagnostic-handoff)
for artifact placement and required evidence. Do not launch the diagnostic agent, change models,
edit further or start a replacement run without the human's authority. A diagnostic proposal is
not permission to implement it.

## Verify claims and record decisions

Apply the documentation decision test in `.github/copilot-codereview.md` ("Documentation is agent
input") during triage. A finding whose inaccuracy has no consequence for a reader is not a defect
under that test: record it as `refuted`, action `none`, and leave the text unchanged.

Material means blocker or major. A single reviewer's demonstrated defect is sufficient; agreement
alone proves nothing. For every finding or could-not-verify item, regardless of severity, record concrete evidence
and verification separately from disposition:

- a change that misses the card's INTENT, or changes something the INTENT says must not change, is
  a finding even when the spec's acceptance criteria pass: a clear miss within the INTENT is a
  defect and takes the `fix` route; where the INTENT is ambiguous, requirements conflict, or the
  remedy changes scope or an accepted trade-off, it takes the `ask` route;
- confirmed defect with a clear remedy within the requirement → queue `fix`, including minors,
  unless the accepted-minor-limitations rule below applies, without another approval question;
  a remedy that would narrow the requirement is not within it and takes the `ask` route below;
- disproved by evidence, including a trigger that cannot occur → `refuted`, action `none`,
  without an approval question; an impossible trigger is not an accepted limitation;
- after focused investigation, a remaining behaviour/scope/risk choice, spec contradiction or
  uncertain remedy → `unclear`/`ask`;
- a minor advisory or limitation that does not require a change under the captured requirement →
  record the evidence and reason for action `none`. Do not turn style preferences, speculative
  enhancements or known limits into unrelated work. A clear defect may take this route only under
  the accepted-minor-limitations rule below.

### Accepted minor limitations

A confirmed minor whose trigger is rare and whose consequence is not
[serious](../../../.github/copilot-codereview.md#approval-and-human-escalation) may be left unfixed
when the remedy's lasting complexity outweighs it. Record `verification: confirmed`,
`action: none` as an accepted limitation only when its `evidence` records all three:

1. What makes the trigger rare.
2. The consequence if it occurs, and what the remedy would add.
3. Why accepting it preserves the captured requirement, without narrowing it.

Fix every other confirmed minor with a clear in-scope remedy: a common failure even when its effect
is small, and a serious one however rare. A trigger an untrusted caller can choose is not rare. Use
the human-decision route when the remedy is unclear or out of scope. Uncertain reachability or an
unsubstantiated likelihood claim is not evidence for acceptance. Major and blocker findings remain
outside this exception.

Keep the finding's ID and all three recorded parts visible as an accepted limitation in the
handoff and the PR's `Testing`. This exception applies only to author triage. Re-verify a
re-reported finding against the current snapshot rather than treating earlier acceptance as
permanent.

### Preserve review evidence and authority

Keep all refutations, fixes and remaining minor advisories visible. Every fix gets another review
while a pass remains. After the final pass, a batch of only minor fixes converges as an unreviewed
delta listed in the handoff; any material finding still exhausts review capacity. Each reviewer claim
has its own stable ID; retaining uncertain duplicates is intentional. Group a demonstrated common
root cause into one code fix and retain all source IDs and their evidence. Do not discard a
returning claim because an earlier claim was fixed. Verify it against the current snapshot.

Record the developer's actual answer, not your paraphrase of implied consent. Clarification within
captured intent can resume while inputs match. A changed requirement needs the human's authority
before implementation; once authorised, supply refreshed intent to `run` without another restart
permission question. Intent
freezes at `start`, so amending the spec or card mid-run puts every later pass on superseded text
without any reviewer noticing: do not amend either while a run is active, and when an amendment
cannot wait, stop the run and start another with refreshed intent rather than continuing. Proceeding
with a known material defect is an explicit exception that stops the automatic run. Only the human
can resolve unavailable checks, except on an `unreviewed_delta`: nothing else verifies it, so its
checks must pass and no answer can waive them. A failed check is not an unavailable check.

## Resume and handoff

For a resumed or interrupted run, follow
[Find and resume a saved run](../../../scripts/pre_pr_lens_review/README.md#find-and-resume-a-saved-run).
Escalate only decisions the inspection cannot resolve within the authorised requirement.

Immediately before invoking `create-pr` or recommending an existing draft be marked ready,
follow [Handoff and PR-head comparison](../../../scripts/pre_pr_lens_review/README.md#handoff-and-pr-head-comparison).
`create-pr` independently repeats that validation before accepting review. If either workflow
leads to edits, those need fresh loop review.

### Publishing to an open PR

The single push after **ready** to an open PR (a direct run on a ready PR, or
`respond-to-pr-feedback`'s full-review choice) follows this contract, under the commit and push
authority required by the **ready** action above:

1. Commit the intended repairs under existing commit authority.
2. Call `handoff` and require a successful, current `ready` result whose tree equals
   `git rev-parse HEAD^{tree}`. If it fails or the trees differ, push nothing; the work stays local
   and the report says why.
3. Push once with `git push origin <branch>`, successfully `git fetch origin <branch>`, then run
   `compare-pr-head` and require a match.
4. If the fetch or comparison fails after the push, report the publication as unverified, in the
   report and in any PR replies. The push stands, but the remote head is not described as reviewed.
