---
name: pre-pr-review
description: Author-session review of the current branch diff, used only when the developer explicitly chooses it instead of review-code, for example as respond-to-pr-feedback's light review or because the local review runner is declined or unavailable. An ordinary request to review changes goes to review-code.
---


# Review Current Changes Before PR

Use this prompt to review the current branch changes before opening or updating a pull request.

The task is not to create a pull request.
The task is to inspect the current diff with a skeptical, evidence-based review mindset and surface the issues that are most likely to matter in production.
Fixes are applied only through the explicit offer-and-accept loop in the instructions below — never unprompted.

This prompt operationalises `.github/copilot-codereview.md`.

## Goals

- catch correctness, security, reliability, compatibility, performance, observability, and meaningful test gaps before push
- **find first, filter second**: while reading the diff, note every issue found — including ones you are uncertain about or consider low-severity. Severity filtering happens at the triage stage, never silently while reading; it is better to surface a candidate that triage later drops than to silently discard a real bug
- keep findings evidence-based: verify each candidate against the code before reporting it
- explicitly state when there are no material findings
- leave the developer one decision away from a clean diff: offer to fix material findings and re-review until none remain

## Standards Context

- treat `.github/copilot-codereview.md` as the source of truth for review priorities and what is worth raising
- focus mainly on the changed files and their direct consequences
- **documentation and code comments are reviewable too**: when a diff asserts technical claims (architecture, threading/concurrency, data flow, ownership, API contracts, behaviour, or file/symbol names), verify those claims against the code with the same rigour as code. "Docs-only" narrows the review to *are the claims accurate, current, and consistent with the code?* — it does not exempt the diff from review. An inaccurate technical doc misleads everyone who trusts it (including agents acting on `AGENTS.md` / context packs). Only genuinely non-technical prose — changelog wording, formatting, typo fixes — is low-risk.
- a second review agent or model may add a pass only with the reviewer-sharing consent `.agents/skills/review-code/SKILL.md` § Invocation and scope defines; do not block on it or lower the evidence bar
- **review fix commits as adversarially as new code.** A change to previously-shipped logic that adjusts a condition (match, count, gate, glob, parse) is the highest-risk diff in a review-only repo: verify **both** failure directions (false-positive *and* false-negative) and trace the normal/common case, not just the edge case being fixed — fixing one failure mode routinely introduces the opposite one. Likewise, when a change must stay in lockstep across several sites (an inventory and the code that enumerates it, mirrored copies, a value and its documented description), confirm **every** other site still agrees, not just the one nearest the edit. Where the changed logic is runnable (a shell snippet, a regex, a glob), execute it against the normal and edge case rather than reasoning about it.
- Feedback on the eventual PR from all reviewers and tools is handled by `.agents/skills/respond-to-pr-feedback/SKILL.md`, including offering gaps back to the shared review standard as that skill describes

## Instructions

Using the available diff, changed files, branch name, commits, and any linked issue or spec context:

1. Determine the review scope before commenting.
   - Use the current branch as the review head.
   - Use the repository default branch unless the user explicitly names a different base branch.
   - Include staged and unstaged tracked changes that are intended for the next PR.
   - If there are unrelated local changes that clearly should not be in scope, say so and limit the review to the intended slice when the context allows it.
2. Review the diff with your own engineering judgement, calibrated by `.github/copilot-codereview.md` and applying its platform and governance facts.
   - Note every candidate issue you find. Do not filter for importance or confidence while reading — that is triage's job, and self-filtering during the read silently drops real bugs.
   - Record a confidence level and an estimated severity for each candidate as you go.
3. Triage the candidates before reporting.
   - Verify each candidate against the code; drop only those the evidence disproves.
   - Drop, rather than demote, anything out of scope for this review: speculative design advice, broad refactors outside the diff, and preferences a linter or formatter would hold. `Minor` is for real defects that don't block — it is not an overflow bucket for scope creep.
   - Classify the survivors as **material** (worth fixing before this PR ships: bugs, security, data loss or corruption, compatibility breaks, misleading technical docs, meaningful test gaps) or **minor** (a real, evidenced defect that does not block: a correctness or robustness gap on a non-critical path, a doc claim that is incomplete rather than wrong, hardening this change does not require). Every minor finding still needs evidence from the diff — "minor" lowers the severity bar, never the evidence bar.
4. Report material findings in full and minor findings briefly.
   - Each material finding should identify the file or area, the concrete issue, why it matters, and the smallest acceptable fix.
   - Minor findings get one line each in their own section — visible to the developer, but outside the fix loop unless they ask.
   - Call out missing tests only when behaviour materially changes or an important failure path is uncovered.
5. If no material findings remain, say exactly `No material findings.` and briefly note any residual risk or verification gap.
   - Do not return `No material findings` for a documentation diff merely because it contains no code: a technical doc's claims are findings-worthy when they are wrong, stale, or contradict the code.
6. When material findings remain, offer to fix them in this session.
   - Do not change code before the human accepts the offer (or has already asked for the fixes).
   - Once accepted, apply the smallest acceptable fix for each accepted finding — no opportunistic refactoring beyond the findings.
   - Apply `.agents/shared/card-intent.md` § Working to it to remedies. Acceptance of a fix offer
     does not approve an unexplained consequential addition under that rule; explain the choice
     and obtain the decision before adopting it.
   - After applying fixes, re-run this review against the updated diff and report the result in the same format.
   - Repeat the fix and re-review loop until the review reports `No material findings.`, or the human stops the loop or defers the remaining findings.
7. Do not open or update a pull request from this prompt.
8. Do not make any code changes other than fixes accepted through step 6.

## Output Format

Provide the following sections in this order.

---

## Findings

- Material findings, ordered by severity, each with confidence noted.
- If there are none, write `No material findings.`

---

## Minor (non-blocking)

- One line per minor finding that survived triage.
- If none, write `None.`

---

## Open Questions / Assumptions

- Include only when needed to interpret the review.
- If none, write `N/A`.

---

## Recommended Next Step

- `Fix findings before opening the PR.` — when material findings remain; follow it with the step 6 offer to apply the fixes in this session.
- `Open the PR.` — when the review is clean (minor findings do not block).

---

## Reviewed State

Record the exact state this review covered, so a later `create-pr` run in the same session can verify nothing changed and reuse this review instead of re-running it.

- `HEAD:` followed by the output of `git rev-parse --short HEAD`
- `Diff hash:` followed by the output of `git diff HEAD | git hash-object --stdin`

After a fix and re-review loop, report only the final pass's values.
