---
name: automated-testing-plan
description: Plan unit and in-process API integration tests for a .NET repository. Use when asked to plan .NET unit or in-process API test coverage.
---

# Test Planner

Create a structured plan for adding tests to this repository.

Do not generate test code in this step.

Create or update the plan as a Markdown artifact at:

`plans/automated-testing/<Plan ID>.md`

Follow the canonical testing guidance in:
`docs/context-pack/testing-patterns.md`

If available, also refer to:
`docs/context-pack/repo-map.deep.md`

Use the deep map only when the compact map is insufficient for planning.

If `docs/context-pack/testing-patterns.md` doesn't exist, stop and tell the human.

Treat `docs/context-pack/testing-patterns.md` document as the source of truth for supported test types, test-level selection, harness and fake patterns, `HttpClient` test-support expectations, determinism, and minimal testability seams.

If the repository already contains test projects, follow their conventions first.

When the repository does not already have an established test-project split, plan for unit tests and in-process API integration tests to live in one shared test project rather than creating separate test projects for each level.

Create `plans/automated-testing/` if it does not already exist.

---

# Read First

Review the following context before planning:

- docs/context-pack/overview.md
- docs/context-pack/db-schema.md
- docs/context-pack/repo-map.compact.md

Only read:

docs/context-pack/repo-map.deep.md

if the compact map is insufficient.

Also inspect:

- existing test projects
- solution structure
- dependency boundaries

---

# Planning Goals

The goal is to introduce **high-value automated tests** that:

- verify observable behaviour
- avoid infrastructure dependencies
- follow the repository testing patterns
- are incremental and easy to implement

Focus on **behavioural risk and business value**, not code coverage.

---

# Planning Constraints

Use `docs/context-pack/testing-patterns.md` to decide which test type fits each target and which shared patterns the plan should preserve.

When planning:

- propose only the supported test types from the canonical guidance
- prefer unit tests whenever the behaviour can be validated without starting an ASP.NET host
- preserve existing shared test-support patterns when the repository already has them
- prefer one shared test project for both unit tests and in-process API integration tests unless the repository already has an established alternative
- keep any planned testability seams narrow and incremental
- if a target appears to require a broader seam, explain why a narrow seam is insufficient and treat human review as a prerequisite rather than a normal execution step
- flag broader design or infrastructure changes as risks instead of normal plan steps

---

# Output Sections (Required)

## 1. Plan ID

Start with:

```
Plan ID: <UTC timestamp in YYYY-MM-DDTHH-mmZ>-<scope-kebab-case>
```

Example:

```
Plan ID: 2026-03-04T14-30Z-orderservice-tests
```

Use the `Plan ID` value as the filename stem and save the plan to:

```
plans/automated-testing/<Plan ID>.md
```

---

## 2. Repository Summary

Brief summary of:

- key projects
- architecture layers
- major dependency boundaries.

---

## 3. Existing Test Coverage

Identify:

- existing test projects
- components already tested
- major gaps.

---

## 4. Prioritised Components

List components that should receive tests first.

For each include:

- purpose
- risk/business impact
- why testing is valuable.

---

## 5. Detailed Test Strategy Per Component

For each target component describe:

### Test Type

Specify exactly one:

- unit test
- in-process API integration test

Explain why this is the correct level.

### Responsibilities

What the component does.

### Dependencies

List collaborators.

### Test Double Strategy

For each dependency specify:

- NSubstitute mock
- hand-rolled fake
- real implementation

and explain why.

### Harness

Specify the test support pattern:

- **Test Harness** for unit tests
- shared fixture / `WebApplicationFactory` setup for in-process API integration tests

### Scenarios

Include:

- happy path
- edge cases
- failure behaviour
- boundary conditions
- async/concurrency behaviour if relevant.

### Refactors Needed

Minimal seams required for testability.

---

## 6. Incremental Execution Steps

Provide an ordered list of steps.

Each step must be small and self-contained.

Use markdown checkboxes.

Example:

```
- [ ] Create Application.Tests project
- [ ] Add base TestHarness or reuse the existing shared test support
- [ ] Add OrderServiceHarness
- [ ] Add happy-path tests for PlaceOrder
```

Step 1 must be fully executable without additional planning.

---

## 7. Risks and Assumptions

Document uncertainties.

Mark unknown items as:

ASSUMED

Examples:

- behaviour assumptions
- external dependency expectations
- undocumented domain rules.

If a target appears to require a true end-to-end or deployed-environment test, mark it as out of scope instead of planning it here.

---

# Constraints

The plan must:

- follow docs/context-pack/testing-patterns.md
- avoid unnecessary mocking
- favour behavioural tests
- be incremental
- keep production code changes minimal

Save the plan artifact under `plans/automated-testing/` and report the saved path in the response.
