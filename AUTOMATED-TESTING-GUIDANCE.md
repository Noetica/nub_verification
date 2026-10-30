## Automated Testing Guidance

This guidance supports the automated testing workflow in this repository, which currently covers unit tests and **in-process** API integration tests.

Coverage percentage by itself is a **blunt instrument**. It’s useful for tracking progress, but it’s a poor proxy for quality. A project can have **90% coverage and still be badly tested**, or **40% coverage with excellent tests** if they target the right areas.

A better way to think about it is **coverage maturity stages**.

---

# 1. Starting point (0% → first pass)

Typical situation: no tests at all.

**Reasonable target:** **20–30%**

Focus on:

* Core business logic
* Pure functions / services
* Areas that break often
* Areas where refactoring risk is high

Avoid:

* Controllers
* Thin wrappers
* Generated code
* trivial DTOs

Goal here is **not coverage**, it's:

* proving tests run in CI
* establishing patterns
* getting the team / copilot comfortable writing tests

Example improvements:

* test domain services
* test pricing logic
* test calculation code
* test rule engines

Coverage rises quickly once you hit these.

---

# 2. Second pass (team is comfortable with tests)

**Reasonable target:** **40–60%**

At this stage you should:

* cover most **business logic**
* cover **branch-heavy code**
* cover **error paths**
* start testing **integration boundaries**

Add tests for:

* service orchestration
* validation logic
* business workflows
* tricky edge cases

You should also start:

* excluding irrelevant code from coverage

Example exclusions:

```
Migrations
Program.cs
Startup
DTOs
EF entities
Auto-generated code
```

This prevents coverage from being artificially low.

---

# 3. Mature project

**Typical good range:** **60–80%**

Most strong teams land here.

Why not higher?

Because some code **should not be unit tested**, for example:

* ASP.NET controllers
* EF plumbing
* simple mapping
* logging wrappers

Instead those are usually better validated via **in-process API integration tests**.

---

# 4. The danger zone: chasing 90%+

When teams chase **90–100%**, they often end up testing things like:

```
getters
simple constructors
logging
pass-through wrappers
```

That creates:

* brittle tests
* low value
* slow pipelines

High coverage ≠ good tests.

---

# 5. Better metrics than coverage

Strong teams track additional indicators:

### 1️⃣ Critical path coverage

Is the **core business logic fully tested**?

Example:

```
pricing engine
payment logic
eligibility rules
discount calculations
```

These should be **near 100% tested**.

---

### 2️⃣ Mutation testing

Tools modify code to see if tests fail.

Example tool:

* **Stryker.NET**

This measures **test effectiveness**, not just coverage.

---

### 3️⃣ Change coverage

Track:

> "Is every new feature accompanied by tests?"

A good rule:

```
New code must include tests.
```

---

# 6. Practical targets for a legacy project

If you're starting with **0% coverage**, a pragmatic roadmap:

| Phase   | Target | Focus                     |
| ------- | ------ | ------------------------- |
| Phase 1 | 20–30% | Core services             |
| Phase 2 | 40–50% | Branch logic + edge cases |
| Phase 3 | 60–70% | Integration + workflows   |
| Mature  | 70–80% | Maintain via CI           |

---

# 7. A rule many senior teams follow

> **"Test behaviour, not lines."**

Good tests target:

* decisions
* edge cases
* failure modes
* business rules

Not:

* trivial plumbing.

When choosing between the two supported test types in this repository:

* prefer unit tests for domain logic and application services
* use in-process API integration tests when routing, middleware, model binding, serialization, DI wiring, or controller behaviour is the thing being validated
* keep tests in-process and independent from deployed Azure infrastructure or shared environments

---

# 8. My rule of thumb for .NET projects

For typical enterprise APIs:

```
<20%   → effectively untested
30–40% → early adoption
50–65% → healthy project
70–80% → very solid
90%+   → probably gaming the metric
```

---

💡 **One very effective strategy for legacy systems**

Add a rule:

```
Coverage must not decrease.
```

This avoids massive retrofitting while gradually improving the codebase.

---
# Strangler Pattern
The Strangler pattern improves a legacy system gradually by wrapping existing behaviour with tests before changing it. Instead of rewriting code, you first write characterisation tests that capture what the current code actually does (even if it’s messy or imperfect). Once that behaviour is locked in by tests, you refactor or replace small pieces of the implementation behind the same interface while keeping the tests green. Over time, more of the old code is replaced or cleaned up, and the new tested code effectively “strangles” the legacy implementation without requiring a risky big-bang rewrite.
[Strangler Pattern](https://en.wikipedia.org/wiki/Strangler_fig_pattern)

