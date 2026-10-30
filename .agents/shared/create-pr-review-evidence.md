# PR review evidence

## Contents

- [Gate lens inspection first](#gate-lens-inspection-first)
- [Prefer a lens handoff](#prefer-a-lens-handoff)
- [Validate the pushed content before accepting the lens result](#validate-the-pushed-content-before-accepting-the-lens-result)
- [Legacy review remains available](#legacy-review-remains-available)
- [Start review when neither form is verifiable](#start-review-when-neither-form-is-verifiable)
- [Correct author input-format errors before a run starts](#correct-author-input-format-errors-before-a-run-starts)
- [Other prerequisite, start, preflight or probe failures stop this attempt](#other-prerequisite-start-preflight-or-probe-failures-stop-this-attempt)
- [Explicit legacy choice, including up front: no preflight is required](#explicit-legacy-choice-including-up-front-no-preflight-is-required)
- [Record the chosen form in `Testing`](#record-the-chosen-form-in-testing)

Read for `create-pr` step 2. Apply the prerequisite gate before any runner README, module or command.

## Gate lens inspection first

Before reading the runner README, importing its discovery
helper or invoking any runner command, check Python is 3.12+, Git is available, and the checkout
contains `.agents/skills/review-code/SKILL.md`,
`.claude/skills/review-code/SKILL.md`, `scripts/pre-pr-lens-review.py` and the package
`scripts/pre_pr_lens_review/`. The package needs `__init__.py`, `__main__.py`, `activity.py`,
`cycle.py`, `cursor_output.py`, `observe.py`, `process_lock.py`, `progress.py`, `providers.py`, `snapshot.py`,
`reviewer.md`, `review.schema.json`, `diagnostic-handoff.md`, `README.md` and
`reviewer-models.json`.
Missing prerequisites mean **no discovery, handoff or comparison command**. An explicitly
chosen same-session legacy review remains eligible under its matching-state rule below;
otherwise name the missing items and stop with the two choices: fix the cause and re-run,
or knowingly choose `pre-pr-review`. For missing sync files, explain that skills and runner
files may not have arrived together. Repair a failed sync first, then wait for the complete sync
and pull `main` again. This check must precede saved-run inspection, not only new-run creation.

## Prefer a lens handoff

A saved run can survive a session/editor restart, but a recorded
`ready` or matching tree alone is insufficient. Locate the repository's saved run using the
runner README's discovery procedure and call `python scripts/pre-pr-lens-review.py handoff
--state <run-dir>` **now**. Require a successful, non-historical `action: ready` result:
the runner revalidates ownership, retained evidence, current inputs and readiness. Its handed-off
`tree` (the reviewed tree, or the `unreviewed_delta` tree when minor fixes followed the final
pass) must equal `git rev-parse HEAD^{tree}` for the commit that will be pushed. If repairs are
still uncommitted, commit them under `create-pr` step 1's rule, push, then repeat this validation.

## Validate the pushed content before accepting the lens result

Push the reviewed repairs
with the explicit branch refspec, then successfully `git fetch origin <current-branch>` and
call `python scripts/pre-pr-lens-review.py compare-pr-head --state <run-dir>`. Require
`pr_head_matches: true` and `action: ready`. A failed fetch or mismatch stops handoff; never
compare an old `FETCH_HEAD` after a failed fetch. Retain this summary for `Testing`. `create-pr` step 16
repeats the comparison against the actual draft PR head. Any later content change invalidates
this evidence and re-enters the review ladder below; committing unchanged content does not.

## Legacy review remains available

A `pre-pr-review` completed earlier in this session can
be reused when recomputed `git rev-parse --short HEAD` and
`git diff HEAD | git hash-object --stdin` match its `Reviewed State`. Missing or different
values require a fresh review. Reused material findings still block unless the developer explicitly
authorises proceeding despite them. Legacy results do not survive sessions. Prefer the lens form
when both are valid. A same-session legacy review counts as the explicit legacy choice only when
the developer chose `pre-pr-review` in their own words, not because a run happened in the
session; otherwise treat it as neither form.

## Start review when neither form is verifiable

Use `review-code` by default, with the reviewer-sharing consent its **Invocation and scope** defines.

After the early lens
prerequisite gate passes, check all three configured CLI commands resolve. Honour the selected
config's runtime overrides rather than requiring default executable names as well.
Then read and follow `.agents/skills/review-code/SKILL.md` in the main authoring loop.
Follow the dispatcher's discovery and recovery rules. Saved JSON is evidence discovery,
not proof of an active process; live command locks and reviewer guardians block concurrent
work across the repository and its worktrees. Supply all fresh inputs to `run` so it checks
compatibility: valid compatible evidence retains passes, attempts and frozen configuration;
missing, damaged or incompatible evidence recovers automatically under the existing review
authorisation. Use the returned `root`, which may be a fresh system-temporary directory.
State-only recovery that lacks evidence needs fresh author inputs, not a permission question.
An interrupted fix requires inspection of the current diff and fresh checks with a nonempty
`inspection` string before a fresh review; never replay uncertain edits or recover its token.
Explicit human stops and exhausted retry/review capacity remain stops. Both
`preflight` and the authenticated fixture `probe` need a started run; both must succeed before
caller review. The dispatcher owns the review/fix cycle; only a converged, freshly validated
handoff can satisfy the lens form above.

## Correct author input-format errors before a run starts

A malformed checks/intent JSON
input may be corrected under the existing review authorisation, without another permission
question, only when the failure is demonstrably before run initialisation: no saved run state,
no ownership claimed or existing run reused, and no provider invocation. Confirm the source
tree and intended requirement are unchanged; preserve the failed artifacts and use a fresh
outside directory for the corrected start. Explain the correction. Missing state alone is
not proof: if the command's failure stage or prior execution is uncertain, stop as below.
This input-format correction does not cover failed checks, authentication, permissions or
provider failures. Recovery of saved evidence follows the dispatcher policy above and never
bypasses handoff validation; historical or superseded evidence cannot authorise the PR.

## Other prerequisite, start, preflight or probe failures stop this attempt

Name the failed
step, provider (when applicable), and concrete reason. Offer exactly two ways forward: fix
the cause and re-run, or knowingly choose `pre-pr-review`. Never fall back automatically.
Other loop stops and human decisions follow the dispatcher; do not describe them as clean.

## Explicit legacy choice, including up front: no preflight is required

If this attempt
created or reused a run, including one discovered after a restart, end it using the runner's
`answer` command with `kind: stop` and the developer's actual choice as `text`; confirm its
saved phase is `stopped`, preserving its evidence and releasing the active claim. Do not
delete its state or registry. If cleanup cannot be confirmed, report that and stop until
resolved; do not leave an active attempt behind. With no run created/reused, nothing needs
stopping. Then run `.agents/skills/pre-pr-review/SKILL.md` (or apply
`.github/copilot-codereview.md` with the same review bar if that skill is unavailable).
Material legacy findings stop PR creation with its offer to fix, unless the developer
explicitly instructs proceeding despite them. Fixes require a clean re-review.

## Record the chosen form in `Testing`

For lens review retain the fresh summary's run/snapshot identity, reviewers and passes, recorded
human decisions and check evidence in full, plus both remote comparisons once `create-pr` step 16
completes. List fixes, refutations and minor advisories left unchanged by ID only, for example
`Fixed: F-001, F-002. Refuted: F-003. Advisory: F-004.` Their detail, and reviewer notes that
carry no ID, stay in the local run; the post-push reviewer may raise a refuted finding again
without that context.
When the summary has an
`unreviewed_delta`, list its finding IDs as fixed after the final pass and not re-reviewed, with
their check evidence. For legacy review name
`pre-pr-review`, record that the lens loop was declined or unavailable, and its failure reason
when there was one. Never label an author-session review as independent lens review.

For each accepted limitation in the handoff, copy its finding ID and complete recorded evidence
into `Testing`, preserving all three parts required by
[Accepted minor limitations](../skills/review-code/SKILL.md#accepted-minor-limitations).
Do not reduce these entries to a count or a generic list of minor advisories.
