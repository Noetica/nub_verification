---
name: create-pr
description: Create a pull request from the current branch, as a draft, with the required body sections and Jira grooming. Use when asked to open, raise or create a pull request.
---


# Create Pull Request Description

Prepare the PR title and body, establish skeptical review evidence, then open an actual **draft**
PR from the current branch. Use the seven-section template below and read
`.agents/shared/pr-standards.md` for approved title prefixes and release-note classifications.
The canonical standard is `DevOps/pr-shepherd/10-pr-standards.md` in `nub_specs`.

Keep the card-content write inside the confirmed draft window: finish the Jira transition and
grooming before offering the ready flip. Only offer when the full-suite result allows it, and
only flip with the developer's go-ahead. Review arrives asynchronously; the normal feedback
handoff follows the flip, while an explicit request can handle feedback already on a draft.

## Goals

- Produce a concise, reviewable PR with traceable scope, testing and risk.
- Use explicit `N/A` and `spec not required` values where appropriate, without invented approvals.
- Cross-link companion PRs and finish Jira writes before the first automated review.
- Leave a reviewable draft and an actionable next step, not just body text.

## Standards Context

- follow `.github/pull_request_template.md` on every PR creation path: `Intent`, `Summary`,
  `Linked Work`, `Linked Documentation`, `Risk Signal`, `Release Note`, and `Testing`.
  Put what changed and why in `Summary`, and affected areas, QA focus and verification in
  `Testing`. Add `Rollout / Rollback / Monitoring` only for an exceptional rollout. These sections
  organise the human review.
- treat `.agents/shared/pr-standards.md` as the source for the approved title prefixes and the release-note tier/type values; treat `10-pr-standards.md` (located above) as the source for documentation rules, risky-change handling, and the rationale behind the standard
- for the suggested PR title, use the approved-prefix table in that partial
- omit the GitHub Issue line when no issue exists; keep Jira when it is the tracking reference
- prefer stable, automation-friendly values over prose where possible: `N/A`, `required - pending`, `not required - [reason]`, `None`
- do not infer approvals, linked issues, linked documents, or testing evidence that are not present in the available context

## Instructions

Using the available diff, changed files, branch name, commits, and any linked issue context:

1. Determine the pull request target details before drafting the body.
   - **Refuse in `nub_specs` first.** If this repository is `nub_specs` (identified as
     `SHARED-AGENT-GUIDANCE.md` § Reading other repositories defines), stop before any commit, push, PR or
     Jira transition: that repository takes every change directly on `main` and its ruleset rejects
     branch creation. Say so, and that the spec or ADR is published by committing and pushing to
     `main`.
   - **Honour a standing exclusion next.** If the developer's explicit exclusion of committing,
     pushing or opening a PR still stands (`implement` step 7a, *Apply exclusions throughout*), name
     it and stop before any commit, push or PR; earlier delivery authority does not override it.
   - Use the current branch as the PR head branch.
   - **Read the card before any push or review.** When the branch names a Jira key (the key every
     later step uses), read that card with `getJiraIssue` now, and for a Subtask its parent too: the
     parent supplies only the INTENT text, as `.agents/shared/card-intent.md` describes. If either
     read fails, stop before any push or PR with the same Jira-unreachable refusal `spec-draft` step
     2 uses, and re-run once Jira is back: the PR's `Intent` section needs the card. When the card
     that holds the INTENT (the parent, for a Subtask) needs one and has neither an INTENT nor an
     exemption, stop before any push or PR as well: say so and give `card-intent.md`'s recovery on
     that card (the human writes it there, or runs `implement <KEY>`, which asks and records it
     there), and that review should run again once it is on the card.
   - Use the repository default branch unless the user explicitly asks for a different base branch.
   - If the branch has not been pushed yet, push it before trying to create the PR. Always push with an explicit refspec and set the upstream to the branch's own remote ref — `git push -u origin <current-branch>` — never a bare `git push`. If the branch's upstream is currently `origin/main` (legacy branches created before `--no-track` in `branch-from-jira`), a bare push can land directly on `main` and bypass review.
   - If there are uncommitted changes that are meant to be included, ask whether to commit them first unless the current run already authorises commits (for example, a PR-authorised `implement` run). Stage only intended files. Apply this same rule to any repairs made by step 2, and push those commits too.
2. Establish review evidence for the intended PR head. Before any runner README, module or
   command, apply the prerequisite gate in `.agents/shared/create-pr-review-evidence.md`.
   - Prefer a saved `review-code` handoff only after freshly validating readiness, the intended
     commit tree and the pushed branch. Read that resource's handoff and remote-comparison rules.
   - An explicitly chosen same-session `pre-pr-review` is eligible only for its matching reviewed
     state. Read the legacy acceptance and cleanup rules in the same resource; never fall back
     automatically.
   - If neither form is verifiable, follow `.agents/skills/review-code/SKILL.md`, including its
     **Invocation and scope** reviewer-sharing consent, and the recovery/stop rules in
     `.agents/shared/create-pr-review-evidence.md`. Correct only demonstrably pre-initialisation
     input-format errors under existing authority; other prerequisite/start/preflight/probe
     failures stop with the choice to fix and retry or explicitly use `pre-pr-review`.
   - Record the accepted form and its evidence in `Testing` as that resource specifies; step 16
     completes the actual PR-head comparison for review-code evidence.
3. Draft the PR title using `Component: meaningful description` where the component is clear. **When the branch names a Jira key, the title must carry that key** — either ahead of the component (`ENG-123 User Management: scope agents to a tenant`) or in a trailing parenthesis (`User Management: scope agents to a tenant (ENG-123)`) — so every PR on a card is findable by its key alone. The key must not be the only meaningful content.
   - Use only title segments from the approved-prefix table in `.agents/shared/pr-standards.md`, following its prefix-selection rules: the full name by default, an alias row (e.g. `NVP`) only where established, never an invented abbreviation (`PD`, `CM`, `UM`, `TSDK`).
   - If the change genuinely spans two approved areas, `Primary Area / Secondary Area: description` is acceptable; if no narrower approved prefix fits because the change is cross-cutting, prefer `Synthesys`.
4. Fill the seven normal sections from `.github/pull_request_template.md`; include the rollout section only when exceptional rollout details are needed.
5. In `Intent`, copy the card's INTENT section from step 1's read word for word as a blockquote, or
   its exemption, as `.agents/shared/card-intent.md` describes. With no Jira key on the branch,
   write `N/A: no card`. If you know the INTENT changed after the accepted review captured it, say
   so in `Testing` and in your report, do not present that review as covering the new text, and ask
   the developer whether to review again before opening the PR. Keep the `Summary` short and
   factual: tell a reviewer who has the diff, card and spec what changed and why, not a tour of the
   changes. State any gap against the Intent — never the aspiration as if it shipped. The same holds for the
   release-note summary in step 9.
   - **Dependency updates.** Read and follow `.agents/shared/dependabot-ride.md` **Record it in
     the PR** for the `Summary` lines on included bumps, deferrals and Deferred majors. Its
     advisory for a ride candidate not brought in is given before step 16 opens the PR, and its
     **Comment once the feature PR exists** follows step 16. Nothing brought in and no
     open Dependabot PRs: no lines.
6. In `Linked Work`, include a GitHub Issue reference when one is available. Do not invent issue IDs.
   - If no GitHub Issue exists, omit that line.
   - In that case, keep the Jira field populated when a Jira key exists.
   - **Companion PRs (multi-repo cards).** A card that spans repos is one card with one branch and
     one PR per repo, so this PR probably has siblings. When the branch names a Jira key,
     look for them and link them here:
     - Search the org for other open PRs mentioning the key, then confirm each one's branch names it
       too (search cannot filter on the branch name directly). Step 3's rule that every PR title
       carries its card key is what makes this search dependable rather than best-effort:

       ```
       gh search prs --owner Noetica --state open --match title,body "<KEY>" \
         --json number,title,url,repository --limit 20
       gh pr view <url> --json headRefName,url,title   # keep hits whose branch contains <KEY>
       ```

     - Any that survive go on one line, comma-separated:
       `Companion PRs: Noetica/nub_web_usermanagement#146`
     - No Jira key on the branch, or no companion found → **omit the line entirely.** Do not write
       `Companion PRs: N/A` and do not add a heading for it — the line lives inside `Linked Work`
       precisely so the template's section contract is untouched.
     - Search failure (rate limit, no access) → **one line in the report**
       (`⚠ Companion search failed — <reason>`) and carry on. Same handling as a back-link failure in
       step 16: this is a convenience, never a gate on opening the PR, but a silent skip leaves no way
       to tell "no companions exist" apart from "the search never ran".
7. In `Linked Documentation`:
   - include a path or link to the relevant `nub_specs` spec when the change clearly needs one
   - otherwise use `Spec: not required - [reason]` with a concise reason such as routine maintenance, test-only verification work, typo fix, CI-only change, or a small bug fix with no design impact
   - prefer class-of-change reasons such as `small bug fix with no design impact`, `routine maintenance`, or `test-only change`; only mention a specific downstream repo, contract, or service when that extra detail materially helps the reviewer
   - do not treat branch names such as `e2e/*` or `testing/*` as sufficient evidence on their own; if the diff touches product code, contracts, auth, data shape, or production config, use the normal spec-required path
   - include links to a test plan or product documentation when those documents are needed and available
   - use `Test plan: required - pending` for risky, cross-cutting, hard-to-verify, or operationally sensitive changes when a test plan is needed but not linked yet
   - use `Product documentation: required - pending` for user-visible behaviour, configuration changes, support workflows, or operational procedures when product documentation is needed but not linked yet
   - use `not required - [reason]` when a test plan or product documentation is not needed
   - do not invent approvers or approval text
8. In `Risk Signal`, prefer `None` unless the diff clearly touches infra, auth or permissions,
   schema or data migration, production config, or another cross-cutting area. For a consequential
   change, even when path risk is `None`, state whether it was agreed in the spec/card or added
   since, including review fixes; name the later human decision when there is one. If agreement
   is missing, stop before PR creation: explain the addition, its reason and simpler alternative,
   and wait for the human's decision under `card-intent.md`. Make the implementation and recorded
   requirement match that decision before continuing; a rejected addition still in the diff blocks
   PR creation. If either changes, return to step 2 for review evidence covering the updated state.
   Describing an addition here does not approve it. Use this existing section, without a checklist
   of absent risks. Name each consequential addition or decision in a line; keep its evidence in
   `Testing` instead of repeating it here.
9. In `Release Note`, choose a single tier and type from the template's allowed values, guided by the release-note tier and type tables in `.agents/shared/pr-standards.md`.
   - use `Tier: None`, `Type: N/A`, and `Summary: N/A` only when the change should not feed release notes
   - the most commonly confused calls: tier `Development` is for internal-only development, testing, or tooling changes; tier `Partner` is for API or integration-facing changes that are not directly customer-visible; type `Housekeeping` is for routine maintenance that does not change product behaviour
10. In `Testing`, include affected areas, QA focus and anything explicitly out of scope when useful to verification.
11. In `Testing`, name the suites or manual checks, their results and any gaps; do not list every
    behaviour the tests check. Keep review evidence in the form required by
    `.agents/shared/create-pr-review-evidence.md` § Record the chosen form in `Testing`.
12. In `Testing`, only describe coverage as directly proving the changed behaviour when the available context shows that the asserted value or behaviour is actually checked.
   - If the automated coverage is indirect, say that explicitly.
   - If manual verification is planned but not yet performed, move it to `QA focus` or `Not run / reason` rather than wording it as completed verification.
13. In `Testing`, include only relevant test categories and `Not run / reason` when expected verification was not run or cannot be verified from the available context; omit empty placeholders.
14. Include `Rollout / Rollback / Monitoring` only for an exceptional rollout, such as an unusual ordering constraint, rollback concern or monitoring requirement.
   - Do not restate the standard CI/CD path or add an `N/A` rollout section for routine changes.
15. Record documentation links and not-required reasons only in `Linked Documentation`; do not add a separate documentation or not-required section.
16. After drafting the title and body, create the PR **as a draft**. Read and follow
   `.agents/shared/create-pr-draft-delivery.md` **Create and verify the draft** for body review,
   the creation command, state assertion and failure recovery.
   - Use `--draft`; if drafts are unavailable, stop rather than creating a ready PR. Confirm
     `isDraft` after creation. A false result requires conversion and a re-read; an unconfirmed
     draft blocks grooming. Report the observed state and any possible review already in flight.
   - For review-code evidence, verify the actual PR head, publish the comparison in `Testing`,
     review and read back the remote body, following that resource. A failed fetch, mismatch or
     evidence upload/read-back stops before steps 17–19, leaves the draft and suppresses a ready
     offer. Content changes return to step 2.
   - Back-link companions found in step 6 with the resource's additive, duplicate-safe comment
     procedure; failures are advisory.
   - Once the draft is confirmed, comment on included Dependabot PRs as
     `.agents/shared/dependabot-ride.md` **Comment once the feature PR exists** describes; failures
     are advisory. End with an actual PR or the concrete blocking reason.
17. After the PR has been created, transition the linked Jira card forward.
   - Derive the Jira key from the branch name (first match of `[A-Z]+-\d+`). If the branch contains no Jira key, skip this step entirely.
   - Apply the shared transition logic: see `.agents/shared/jira-transition.md`.
   - Target status name: `Peer Review` (the PR-equivalent state; the partial matches it by name on the card's own workflow).
   - This step is advisory per the partial: a transition failure logs a one-line note and does not retract the PR or block reporting. Failures here must not be treated as PR creation failures.
   - Then apply `.agents/shared/jira-sprint.md` against the same key. It skips `offsprint`
     cards and is idempotent and fail-soft. This backstop covers work that reached a PR without
     the earlier `branch-from-jira` or `implement` sprint step.
18. After the Jira transition has been attempted, groom the card for verification.
   - **Re-read `gh pr view <pr-number> --json isDraft` immediately before invoking the groom, and
     abort this step if it is not `true`.** Step 16's assertion was minutes and several Jira calls
     ago, and the developer is watching the PR appear — they can mark it ready in the UI in that
     window. Keep this handoff inside the agreed draft window. On an abort, report that the card
     was not groomed: an observed `false` means the PR is already ready; a failed or unparseable
     read means draft state is unconfirmed, so identify the read failure. Offer the standalone
     grooming command for a later explicit choice.
   - Follow `.agents/skills/groom-card-for-verification/SKILL.md` against the linked card (chained mode): it distils the spec into a verification-readable card (what changed & why, a short how-to-verify, build/version, and a spec link), and fills an empty `## Release notes` section (`groom-card-for-verification` step 4a).
   - Use the same Jira key derived in step 17. If there is no Jira key, skip this step entirely.
   - If that prompt is unavailable, skip this step with a one-line note.
   - This step is advisory and fail-soft, exactly like the Jira transition: a grooming failure logs a one-line note and must not retract the PR or be treated as a PR creation failure.
19. Decide whether to offer **mark ready for review now, or leave as a draft**. Read and follow
   `.agents/shared/create-pr-draft-delivery.md` **Decide whether to mark ready**.
   - Use the **latest** `isDraft` observation (step 18 supersedes step 16). An unconfirmed draft or
     failed required handoff check suppresses the offer; report the observed state and any skipped
     grooming. Only a confirmed draft with passed handoff checks reaches the ready decision.
   - Report draft state on its own line: the replacement skips drafts; once the PR is ready it
     requests Copilot's review only when it finds the head clean. Explain the draft window and its
     costs.
   - Read the current head's full-suite result using that resource's exact classification. Offer
     the flip only for **passed** or **not affected**; **pending**, **failed** or **not run** leave
     the PR as a draft with the reason and next command. If there is no full-suite CI job, use the
     specified full local run on the settled tree. A later ready request rechecks the current head.
   - Finish steps 17 and 18 before a ready question. On a confirmed draft with passed handoff
     checks and a Jira key, read `.agents/shared/grooming-handoff.md` **Interpretation before the
     ready decision**, even if the full-suite result withholds the offer. Evaluate
     Description and Components independently, including unknown values and a missing block;
     give its warnings and recovery offers. For a local-spec decision, read
     `.agents/shared/locate-spec.md` directly. With no key, say there is no linked card and give no
     grooming warning or offer.
   - On the developer's **Ready now**, run `gh pr ready <pr-number>` and confirm it. Otherwise
     leave the draft and give that exact command for later. Never flip silently. Continue to
     step 20 with the actual result.
20. Do **not** wait for an automated review unless the developer has requested it — reviews arrive asynchronously, and on a draft the replacement
   skips review, and Copilot is asked only once the replacement finds a ready head clean.
   Which handoff you give depends on the answer to step 19:
   - **Marked ready** → offer to run `respond-to-pr-feedback`
     (`.agents/skills/respond-to-pr-feedback/SKILL.md`) now: "Want me to wait for automated
     reviews, verify the feedback, fix small issues, ask which local review the fixes get, and push
     them once?" On acceptance,
     invoke that skill for this PR; it owns the bounded wait and single feedback cycle. If the
     developer already requested this, continue without asking again. Otherwise, wait for their
     answer; if they decline, give one copyable invocation with the actual PR URL, in the client's
     syntax, e.g. `$respond-to-pr-feedback <PR-URL>`, for later use.
     Keep the description, card and test claims accurate after delivery. Never claim an older
     review covers changed requirements; card or body edits alone do not trigger another run.
   - **Left as a draft** → the next step is the flip, **not** the feedback loop. Do not offer
     `respond-to-pr-feedback` as the next action here: the replacement skips drafts,
     so it would most likely poll and time out for nothing. Say: mark ready, then run
     `respond-to-pr-feedback` if review feedback arrives. Marking ready grants eligibility;
     review arrival and a counting approval are not guaranteed. The publishing-account limit
     is explained in the draft-delivery resource.

## Output Rules

- open the pull request as a draft instead of only returning body text when the environment allows it
- follow the selected review workflow: `review-code` verifies all findings and fixes clear in-scope defects of any severity without per-finding approval, then re-reviews within its limits; unverified findings, queued fixes and human decisions block PR creation. Minor advisories may remain with evidence and an explicit reason no change is required. The explicit legacy workflow retains its own fix/exception rules
- if the pull request is created successfully, report the PR number and URL and include the final title/body you used
- **on a confirmed draft**, always report the draft state on its own line — that the PR is a draft and that the replacement reviewer skips drafts — and always end either by offering the flip or by stating the full-suite result that withholds it (step 19). Never report a draft PR as simply "created" and stop: a draft nobody marks ready receives no replacement review, and the staleness sweep excludes drafts by default. Where the latest `isDraft` observation (step 18's re-read, else step 16's assertion) did not confirm a draft, report the observed state instead and offer no flip
- when the user declines the flip, leave them the `gh pr ready <pr-number>` command and the order the remaining steps run in; do not offer `respond-to-pr-feedback` as the next action while the PR is still a draft
- report companion cross-linking in one line when it happened (`✓ Companions linked: <urls>`) and stay silent when there were none; a failed companion search or back-link is its own one-line `⚠` (steps 6 and 16), never a silent skip
- if the pull request cannot be created, say exactly what blocked it (for example uncommitted changes, unpushed branch, or missing GitHub access)
- once the PR is ready for review, offer to run `respond-to-pr-feedback` as described in step 20; start only when authorised, reusing any existing request
- after the initial `Suggested title:` line, use the template's seven normal headings in order when showing the drafted body
- add a visible `Rollout / Rollback / Monitoring` section only for an exceptional rollout; do not add other extra sections
- do not fabricate links, issue numbers, approvals, or testing evidence
- prefer short bullets over long prose inside sections

## Scope Note

This prompt is intended for normal human-authored PRs.
It is not intended for bot-created maintenance or repo-sync PRs unless a human is promoting them into the normal review flow.
