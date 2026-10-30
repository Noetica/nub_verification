---
name: automated-testing-autopilot
description: Execute the next bounded batch of work from the current automated-testing plan. Use when asked to continue, execute or work through that plan.
---

# Test Executor (Autopilot Batch)

Use this prompt as the **default executor** when you want to move through a testing plan with lower human coordination overhead: it completes one bounded vertical slice per run instead of requiring review after every single plan step.

Implement a **bounded, coherent batch** from the latest automated-testing plan.

Plan artifacts live in:

`plans/automated-testing/<Plan ID>.md`

Follow the canonical testing guidance in:

`docs/context-pack/testing-patterns.md`

If `docs/context-pack/testing-patterns.md` doesn't exist, stop and tell the human.

Treat that document as the source of truth for supported test types, out-of-scope work, harness and fake patterns, `HttpClient` disposable ownership, and when to preserve an existing repository test-support layout.

---

# Execution Model

This prompt is intended for low-supervision autonomous runs (Claude Code, Copilot CLI autopilot).

The goal is not "exactly one step" — it is the **next small vertical slice, finished**: typically 1 to 3 consecutive incomplete plan steps that belong to the same component or feature slice, use the same test type, and can be implemented and validated in one run. A seam plus the tests that require it is one slice; unrelated controllers, or two components that need separate design decisions, are not.

Optimize for one finished slice per run, not for the number of boxes ticked. A seam-only, helper-only, or scaffold-only change is **not** a finished slice unless a real blocker prevents adding the dependent tests immediately. Do not execute unrelated plan steps just because they are available.

---

# Workflow

1. Locate the **latest automated-testing plan artifact** (not the prompt template) in `plans/automated-testing/`. If none exists there, stop and tell the human to run the planner first. If multiple exist and the human has not named one, choose the most recently modified.

2. Read the plan, extract its **Plan ID**, and select the next 1 to 3 compatible incomplete steps that form one coherent slice. State briefly which steps you selected, why they belong together, and what "done" looks like for the batch — then continue straight into implementation; this status message is not a review checkpoint.

3. Implement the slice **red → green → refactor** where realistic. If legacy structure blocks a meaningful failing test, make the smallest justified testability seam first, then add the failing test immediately after the seam exists — never land production changes with the tests deferred to a later batch.

4. Run tests using the repository's standard command (if none is documented, use `dotnet test`). Iterate up to 3 cycles of run → fix the smallest issue → re-run; if still failing after 3 attempts, stop and report the blocker.

5. Self-review the result against `docs/context-pack/testing-patterns.md`, the selected plan step wording, and the repository's existing test-support patterns. Fix any clear in-scope issue in the same run.

6. Update the plan file: change each completed step from `- [ ]` to `- [x]`, subject to the evidence bar below. Only the steps you selected for this batch — never unrelated future steps, and never a preparatory step whose support the finished slice does not actually use.

7. Stop the batch when the next incomplete step belongs to a different component or test type, the change would exceed the production-edit bounds below, tests are still failing after 3 fix cycles, or the remaining work needs a design decision from the human.

---

# Evidence Discipline

Before marking a plan step complete or reporting the run done, audit each claim against something you can point to from this session: the file on disk (check the working tree, including untracked files) and the test run that exercised it. Only tick a checkbox you can back with a named file and a passing test run — a step whose intended outcome is scaffolded but not validated stays unchecked, with a one-line note underneath naming the blocker. One exception: a step the plan explicitly frames as non-test preparatory work (a new test project, a CI job, a scaffold) is evidenced by the named file alone. Be conservative with those — if the finished slice does not actually use the support, leave the step unchecked.

Report outcomes faithfully: failing output verbatim, deferred work and known quality gaps stated plainly, facts rather than intent.

A run is complete only when code or test files were changed and the relevant tests were run, or you are stopping on a concrete, named blocker.

---

# Production Code Limits

Follow the minimal-production-change guidance in `docs/context-pack/testing-patterns.md`.

Production edits in a batch are the seams the selected tests require — constructor injection, interface extraction, test-only service registration — and nothing more: no architectural refactors, DI rewrites, public API redesign, or package changes beyond already-approved testing packages. Before editing production code, name the failing or blocked test scenario that requires it, and keep the seam as narrow as possible.

A slice that needs more than ~4 production files or ~150 changed lines is too big for one autopilot batch — stop and report instead. When choosing between "more steps" and "a more complete slice", prefer the more complete slice.

---

# Output Expectations

End every run with a short evidence summary:

- the selected plan file and Plan ID
- which steps were completed, and the exact checklist lines updated
- changed and untracked files, or a clear statement that no files were changed
- tests run and their results
- whether any production seam was added
- the exact blocker, if the batch stopped early

If the run did not achieve the "done" you declared at the start, say so explicitly and treat the batch as incomplete.
