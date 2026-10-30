---
name: review-triage
description: Use when the user brings code-review findings from an external reviewer — pasted from GPT, Codex, Copilot, a colleague, or another Claude session, or fetched from a PR — that need handling, or when a PR/branch is being reviewed again in a later session. Not for generating a fresh review.
---

# Review Triage

## Overview

External review findings are **claims, not facts** — even from a strong model, even when it retracts under pushback. Verify every claim against repo ground truth, let the user pick what gets fixed by stable ID, then land each fix as its own commit on a topic branch and push, so the next reviewer reads the real PR rather than a stale SHA.

**Not in `nub_specs`.** If this repository is `nub_specs` (identified as `SHARED-AGENT-GUIDANCE.md` § Reading other repositories defines), stop: this workflow commits on a topic branch and pushes, and `nub_specs` takes every change directly on `main`. Triage spec findings with `spec-grill`, which owns external-findings triage for specs and ends with the publication handoff.

## When to Use

- User pastes review output from another AI or a colleague ("GPT reviewed this PR and said…", "Codex found…")
- User asks to check/triage review comments on a PR for standalone selection rather than closing out its feedback
- A branch/PR that already has a review ledger gets a new batch of findings

**When NOT to use:** generating your own review of a diff → `review-code`. Handling PR comments, review threads and failed checks from any source → `respond-to-pr-feedback`.

## Workflow

1. **Be on the branch that will carry the fixes.** The ledger is keyed by the full branch ref, so settle this first: if on `main`, create a topic branch now. Fixes are never committed to `main`. A detached HEAD needs a branch before triage.
2. **Open the ledger.** Use `.claude/review-ledger-<sha256>.md` under the repo root. The suffix is the full lowercase SHA-256 of the exact UTF-8 ref returned by `git symbolic-ref --quiet HEAD`, excluding the trailing newline (for example, hash `refs/heads/feature/x`). Record that full ref in a `Branch ref:` line at the top of the ledger and verify it before reading entries. Do not replace slashes with hyphens for identity: `feature/a-b` and `feature/a/b` must have different ledgers.

   **Existing ledgers:** when the hashed path is absent, check the old `.claude/review-ledger-<branch>.md` path (slashes replaced by hyphens). Reuse its entries and permanent IDs only when its recorded branch identity or provenance establishes that they belong to this exact ref. Copy verified history into the new ledger, adding `Branch ref:`, and leave the old file intact. An ambiguous legacy ledger, or a mismatching ref in an existing hashed ledger, requires human clarification before ingesting findings; never silently start over, merge histories or renumber IDs. If neither ledger exists, create the hashed ledger. Leave it untracked and read all existing entries before ingesting anything.

   **Keep it out of commits.** The ledger is agent scratch, not a deliverable — durable tracking of findings belongs in the issue tracker (e.g. Jira), not the repo. "Untracked" alone doesn't protect it: a `git add -A` or an IDE's commit-all button will sweep it into a PR (this has happened). The durable guard is a gitignore rule: if the repo already ignores `.claude/review-ledger-*.md`, rely on that; if it doesn't, **offer to add it** (and if a ledger has already been committed, offer to `git rm --cached` it). Until it's ignored, stage explicit paths only — never `git add -A`/`.` while a ledger is present. Still don't gitignore or commit it silently — surface the choice.
3. **Ingest findings** from the pasted text (or `gh pr view --comments` / `gh api` if the user points at a PR). Split into atomic findings; record each finding's source (reviewer + date).
4. **Dedupe.** A finding matching an existing ledger entry (same root cause, any wording) gets recorded as `duplicate-of F-nnn` on the existing entry — no new ID. Fresh findings get the next `F-nnn`. **IDs are permanent: never renumber, reuse, or restart numbering in a later session.**
5. **Verify each fresh finding against the repo.** Read the actual code, schema, config — whatever the claim is about. Verdicts:
   - `CONFIRMED` — with evidence (`file:line` or schema object)
   - `REFUTED` — with evidence proving it wrong
   - `UNCLEAR` — say exactly what's needed to decide (e.g. production DB check)

   Reviewer confidence, model reputation, or a mid-thread retraction is not evidence in either direction. If a claim concerns the database, check `schema-reference.md` / migration files and respect its confidence labels.
   Apply `.agents/shared/card-intent.md` § Working to it to the proposed remedy before recommending
   it. Selecting a finding to fix does not approve an unexplained consequential addition. Expose
   any such choice in the recommendation and obtain the human's decision before adopting it;
   reuse an explicit acceptance of that explained choice rather than asking again. Routine
   repairs within the agreed scope need no additional decision.
6. **Report and stop.** Output a table — ID, finding (one line), verdict, evidence, recommended action — then wait for the user to select IDs. Do not change any file before the selection (or an explicit prior instruction to fix).
7. **Fix, commit, push — one commit per selected ID.** First apply step 5's scope rule to each selected remedy: it must be within the agreed scope, or its explained consequential choice must have explicit human acceptance. If that decision is missing, leave the finding unfixed and ask for it. A selection that explicitly accepts the explained remedy is sufficient; do not ask twice. Apply the smallest fix for that ID only; don't fold style nits into bug fixes; no opportunistic refactoring. Commit it with the `F-nnn` in the message, staging explicit paths. When the batch is done, push the branch. Separate commits mean one finding can be reverted alone, and the push means the reviewer's next pass sees the fix instead of re-reporting it. **Still ask before** force-pushing, pushing to `main`, merging, or deleting a branch.
8. **Update the ledger** before finishing: status per entry, and append new sources to existing entries that were re-reported.

   Statuses: `open` (unresolved, includes "not now" deferrals — annotate why) / `fixed-pushed <sha>` / `declined` (user rejected the finding itself) / `refuted` (set immediately when verification disproves the claim — needs no user decision) / `duplicate-of F-nnn`. Older ledgers use `fixed-unstaged`; leave those entries as they are.

## Ledger Entry Format (required fields)

```markdown
## F-003 — orders on final day of range excluded
- source: GPT 5.5 (2026-07-02); Codex (2026-07-03)
- claim: docstring says inclusive but endTs is midnight of end date with `<`
- verdict: CONFIRMED — report.py:14, endTs not advanced one day
- status: fixed-pushed 4e1c9a2 (2026-07-02)
```

## Red Flags — stop and re-read the workflow

- About to edit a file and the user hasn't picked IDs yet
- About to commit on `main`, or the ledger is named for `main`
- Fixes applied but nothing committed or pushed "to keep it simple" — the next reviewer will re-report every one of them
- Several IDs folded into one commit
- About to `git add -A` / commit-all while an un-gitignored ledger is present (it'll land in the PR) — stage explicit paths, and offer to add the gitignore rule
- Accepting or dropping a finding because of who said it, not what the code shows
- Presenting findings numbered 1..N instead of ledger IDs
- Ledger not read (or not written) this session
