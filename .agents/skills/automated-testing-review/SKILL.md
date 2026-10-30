---
name: automated-testing-review
description: Review newly added or modified unit and in-process API tests. Use when asked to review .NET unit or in-process API tests.
---

# Test Review

Review the tests that were recently added or modified.

Follow the canonical testing guidance in:

`docs/context-pack/testing-patterns.md`

The goal is to improve **test quality, reliability, and maintainability**.

Do not add new test scenarios unless they are critical omissions.

Avoid large refactors.

If `docs/context-pack/testing-patterns.md` doesn't exist, stop and tell the human.

Treat that document as the source of truth for test type selection, structure and naming, harness and fake patterns, `HttpClient` disposable ownership, determinism, and minimal production changes.

Review the plan artifact that matches the work from:

`plans/automated-testing/`

If no plan artifact exists there, stop and tell the human to run the planner first.

If multiple plan artifacts exist and the human has not named one, use the most recently modified file.

---

# Inputs

Review:

- newly created or modified test files
- any related harness or test double files
- minimal production code changes introduced for testing

Also review the selected automated-testing plan artifact.

---

# Review Goals

Verify that tests:

- follow the repository testing patterns
- use the correct test type for the thing being validated
- verify observable behaviour
- remain deterministic
- avoid unnecessary mocking
- are readable and maintainable.

Focus on **test design**, not formatting.

---

# Review Checklist

## 1. Test Type Selection

Review the chosen test level against `docs/context-pack/testing-patterns.md`.

Flag cases where:

- a host-based integration test was used for logic that should be a unit test
- a unit test is trying to assert routing, middleware, model binding, serialization, or DI wiring
- the tests drift into out-of-scope end-to-end or shared-environment territory

---

## 2. Test Structure

Review structure and naming against `docs/context-pack/testing-patterns.md`.

Flag tests that:

- mix multiple behaviours
- hide important setup in assertions
- depart from the repository's adopted naming pattern without a reason

---

## 3. Harness Usage

Review harnesses, fixtures, and shared setup against `docs/context-pack/testing-patterns.md` and the repository's existing test-support patterns.

Flag cases where:

- dependencies are recreated in every test
- the SUT is manually constructed repeatedly despite an existing shared setup pattern
- integration tests build ad hoc hosts instead of reusing a shared fixture where one already exists

---

## 4. Test Double Strategy

Review chosen doubles against `docs/context-pack/testing-patterns.md`, including `HttpClient` response ownership and shared helper usage when applicable.

Flag cases where:

- large interfaces were implemented as fakes unnecessarily
- mocks are verifying trivial behaviour
- `HttpResponseMessage` instances are created inline in ways that obscure ownership or disposal

For in-process API integration tests, flag any dependency on live external services or shared environment configuration.

---

## 5. Behaviour vs Interaction Testing

Review assertion style against `docs/context-pack/testing-patterns.md`.

Flag cases of:

- excessive `Received()` usage
- in-process API integration tests that assert only HTTP status code when the scenario's observable contract also includes response body, headers, content type, validation payloads, or persisted or emitted side effects
- verifying trivial calls.

---

## 6. Determinism and Scope Boundaries

Review determinism and scope boundaries against `docs/context-pack/testing-patterns.md`.

Flag any test that might be non-deterministic or environment-dependent.

---

## 7. Test Duplication

Look for:

- repeated setup code
- duplicate harnesses
- duplicated fakes.

Recommend extracting shared helpers if appropriate.

---

## 8. Fake Placement

Review fake placement against `docs/context-pack/testing-patterns.md` and the repository's existing shared test-support structure.

Flag fake classes defined inside multiple tests or scattered across inconsistent locations without a repository-level reason.

---

## 9. Production Code Changes

Review any production edits.

Confirm they follow the minimal-production-change guidance in `docs/context-pack/testing-patterns.md`.

Flag changes that appear unrelated to testing.

---

# Optional Improvements

Suggest improvements such as:

- introducing a harness
- converting mocks to fakes
- reducing duplicate setup
- simplifying assertions.

Only recommend changes that significantly improve clarity or maintainability.

---

# Output Format

Provide the following sections.

---

## Plan Reviewed

Plan path and Plan ID.

---

## Summary

Brief overall assessment of the test quality.

Example:

- Good
- Acceptable with improvements
- Needs revision.

---

## Findings

List issues grouped by category:

- Test type selection
- Structure
- Harness usage
- Test doubles
- Determinism
- Duplication
- Production code changes.

Each issue should include:

- file
- short explanation
- suggested fix.

---

## Suggested Improvements

Optional improvements that would strengthen the test suite.

Keep suggestions small and practical.

---

## Verdict

One of:

- ✅ Tests are ready
- ⚠ Improvements recommended
- ❌ Significant issues detected
