# Draft PR delivery

## Contents

- [Create and verify the draft](#create-and-verify-the-draft)
- [Decide whether to mark ready](#decide-whether-to-mark-ready)

## Create and verify the draft

- **Always `--draft`.** Never mark it ready in this step — `create-pr` step 19 is the only place in this
  prompt that may flip it, and only on the developer's say-so. Finish Jira grooming inside
  this draft window, then let the developer read the PR, re-review locally, push fixes and mark
  it ready when happy. The replacement reviewer skips drafts.
- Review the prepared body against `.github/pull_request_template.md`: preserve the quoted INTENT,
  include the seven normal sections, accurate linked documentation and actual test evidence, and
  omit empty placeholders. Include rollout notes only when exceptional handling is needed.
- **Create it with `gh pr create --draft`**, in preference to the dedicated GitHub PR creation tool:
  `gh pr create --draft --base <base-branch> --head <current-branch> --title "<final-title>" --body-file <prepared-body-file>`
  That tool's `draft` field is *optional* and the API default is a **ready** PR, so a dropped
  optional field bypasses the agreed draft checkpoint. Use it only when you
  can confirm the call set `draft: true`.
- **If creation is rejected because drafts are unavailable on this repo or plan, stop and report
  it.** Do not retry without `--draft`: that bypasses the developer's ready decision.
- **Then assert the draft — do not assume it.** Read it back with
  `gh pr view <pr-number> --json isDraft` (or the equivalent API call). **Proceed to `create-pr` step 18 only
  while `isDraft` is observably `true`**. `create-pr` step 17's Jira transition and sprint bookkeeping
  may still proceed. An errored, skipped or unparseable read means draft state is unconfirmed.
  - **`false`** → convert it now with `gh pr ready <pr-number> --undo`, then read `isDraft` again.
    Report that it was opened ready and automated review may already have started; conversion
    does not undo that work.
  - **Still not observably `true`, or unreadable → stop before step 18** and report the observed
    state. Do not groom under an unconfirmed draft or offer a ready flip.
- Do not stop after printing `Suggested title:` and the PR body. The prompt should end with an actual open draft PR or a concrete blocking reason.
- **For lens evidence, verify the actual PR head before delivery is complete.** Successfully
  `git fetch origin pull/<pr-number>/head`, then repeat
  `python scripts/pre-pr-lens-review.py compare-pr-head --state <run-dir>`. Require fresh
  `action: ready` and `pr_head_matches: true`. Record the fetched head commit/tree and result in
  the PR body's `Testing` section using a prepared body file, then check that the body still follows the template.
  Publish that reviewed file with `gh pr edit <pr-number> --body-file <prepared-body-file>`.
  Read the remote body back with `gh pr view <pr-number> --json body` and confirm `Testing`
  contains this run's fetched commit/tree and successful comparison. An upload or read-back
  failure stops delivery before grooming or the ready offer; a local file alone is not evidence
  that the already-open PR was updated.
  On a fetch failure or mismatching head, record the failed handoff, leave the PR a draft and
  stop before `create-pr` steps 17–19: report the draft URL and failed check, and say that Jira transition
  and grooming were not attempted by this invocation. Do not offer to mark it ready. Apply
  this same reporting rule to an evidence upload/read-back failure above. Any content edits
  since acceptance return to `create-pr` step 2.
- **Once the PR exists, back-link it on each companion found in `create-pr` step 6.** Post a comment on the
  companion rather than editing its body — rewriting a PR body mid-review is intrusive, and a
  comment is additive and just as visible:
  `gh pr comment <companion-url> --body "Companion PR for <KEY>: <new-pr-url>"`
  Skip a companion whose comments already link this PR (a re-run must not stack duplicates), and
  treat any failure the same way as the search: one line in the report, never a block, never a
  reason to retract the PR that has already been opened.

## Decide whether to mark ready

**On a confirmed draft with every required handoff check passed**, report it and then **offer to mark it ready** — never mark it ready
silently, and never finish without either asking or saying why the full-suite result below withholds
the offer. This is the prompt's last decision point and it belongs
to the developer, because marking ready makes it eligible for the local replacement reviewer, which requests
Copilot's review once it finds the head clean. Those reviews consume the configured subscriptions or credits.
- **Read this condition first, and key it on the LATEST observation of `isDraft`, not `create-pr` step 16's.**
  Use `create-pr` step 18's re-read immediately before grooming when it ran; otherwise use
  step 16's assertion after creation. If the latest read is `false`, report that the PR is ready
  and grooming was skipped; a review may already be in flight. If the read failed or could not
  be parsed, report draft state as unconfirmed, identify the read failure and report any skipped
  grooming. Neither outcome confirms a draft or allows a ready offer. An earlier successful
  observation does not override either result. A failed `create-pr` step 16
  handoff or evidence upload/read-back also suppresses the offer, even if the PR is a draft.
  Everything below applies only to a confirmed draft whose required handoff checks passed.
- State plainly that the PR is a **draft** and that **the replacement reviewer skips drafts**. Give that its own line in the
  report rather than folding it into a summary, and say that Copilot is asked only once the
  replacement finds the ready head clean.
- Say what the draft window is for: read the diff on the PR, re-run the accepted review form if the
  branch content moved, and push any fixes. The replacement skips drafts; local lens reviews still
  use the developer's CLI subscriptions, and CI/CodeQL still use Actions minutes.
- **State the full-suite result for the current head, and let it decide whether the flip is
  offered.** Find the repository's CI job that runs its full test suite (in the standards hub,
  the `Local review runner tests` workflow). Read that job's result for the PR's current head
  SHA at the moment you offer, and report exactly one of:
  - **passed** — every matrix leg of the job completed successfully on that head;
  - **not affected** — the job's own path filter skipped that head. With a workflow-level
    `paths` filter there is then no run at all, so check that none of the PR's changed files
    match the list before reporting it. The filter is the suite's declared input list, so this
    counts as passed;
  - **pending** — any leg is still queued or running;
  - **failed** — any leg failed or was cancelled;
  - **not run** — there is no result for that head and the path filter does not explain it.

  Offer the flip only on **passed** or **not affected**. On **pending**, say CI is still
  running, give `gh pr ready <pr-number>` to run once it passes, and continue as **Leave as
  draft** below without asking. On **failed**, do not offer it: say the failure needs fixing on
  the draft, or a cancelled leg re-running on the same head, then continue as **Leave as
  draft**. On **not run**, do not offer it either: say no full-suite result exists for this
  head, so the job needs running (re-run it, or push), then continue as **Leave as draft**. A result belongs to one head. Each
  push produces a new head and a new run, and a failed or interrupted run may be re-run on the
  same head. Any later ready request made through an agent re-reads the current head's result
  before flipping. Whatever the result, the draft-window requirements in `create-pr` step 19
  still apply; only the ready question itself is withheld.

  Where the repository has no CI job that runs its full suite, run the full suite once locally
  on the settled tree now, unless a `full` pass is already recorded for this exact tree. Repeat
  only a failed or interrupted run, record it as `full` in the form the runner README's
  *Command flow* checks step defines, and report that result in place of the CI result.
- Then, when the result above allows it, ask plainly: **mark it ready for review now, or leave it as a draft?**
  The sub-bullets up to **Ready now** apply on every outcome, asked or not.
  Explain that PRs authored by the account the replacement publishes as get an advisory comment,
  never a counting approval.
  - **Only ask once `create-pr` steps 17 and 18 have actually finished.** The card must have stopped changing
    before the developer makes the ready decision. If either step is still
    outstanding, finish it first.
  - **If the branch carries no Jira key, `create-pr` step 18 was skipped and none of this applies.** There
    is no card to groom: say the PR has no linked card and give no grooming warning or offer. This is the
    ordinary case for chore and docs PRs, not a degraded one.
  - Apply the grooming handoff interpretation selected by `create-pr` step 19 before deciding whether to flip.
  - **Ready now** → run `gh pr ready <pr-number>`, confirm it, and continue to `create-pr` step 20. The
    PR is eligible for the replacement's local best-effort review from here; a run is not guaranteed.
  - **Leave as draft** → end with the exact command for later, `gh pr ready <pr-number>` (or the
    *Ready for review* button), and **stop at `create-pr` step 20's pointer without inviting the feedback loop
    yet** — see `create-pr` step 20.
