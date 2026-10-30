---
name: dotnet-cleanup-plan
description: Plan a phased .NET hygiene sweep covering whitespace, style, formatting and naming. Use when asked to plan a .NET cleanup or tidy-up.
---

# .NET Code Cleanup Planner

Create a structured cleanup plan for this .NET repository.

Do not make any code changes in this step.

Create or update the plan as a Markdown artifact at:

`plans/dotnet-cleanup/<Plan ID>.md`

If `plans/dotnet-cleanup/` does not exist, create it.

---

# Read First

Review the following context before planning:

- `docs/context-pack/overview.md`
- `docs/context-pack/repo-map.compact.md`
- `.editorconfig` (if present)
- `Directory.Build.props` (if present)

Only read `docs/context-pack/repo-map.deep.md` if the compact map is insufficient.

Also inspect:

- solution structure
- project types (SDK-style vs legacy)
- existing analyzer configuration
- CI workflows for existing style gates

---

# Planning Goals

The goal is to produce a **repeatable, phased cleanup plan** that:

- enforces consistent coding standards
- automates as much cleanup as possible
- minimises behaviour changes and API breaks
- is incremental and can be implemented one PR at a time

Focus on **mechanical, low-risk fixes first**, deferring anything that changes semantics or public API.

---

# Standards Baseline

The cleanup must be anchored to:

1. `.editorconfig` as the single source of truth for style and naming.
2. Roslyn analyzers (`Microsoft.CodeAnalysis.NetAnalyzers`) enabled via `Directory.Build.props`.
3. Optional style analyzers (`StyleCop.Analyzers`, `Roslynator.Analyzers`) for broader coverage; recommend them, but do not mandate them.
4. String formatting policy: prefer interpolation; keep `StringBuilder` only where clearly justified (loops, repeated appends, or obvious hotspots).

If `.editorconfig` or `Directory.Build.props` do not exist, the plan must include a bootstrap step to create them. Use the model files from `nub_model_repository` as a reference when helpful.

---

# Scope Rules

In scope:

- formatting, naming, and style fixes
- string formatting cleanup (prefer interpolation)
- analyzer-based guardrails and CI checks
- small seams for testability if requested alongside a test plan

Out of scope:

- large refactors that change public API contracts
- functional redesign or performance rewrites
- package upgrades or framework migrations
- DI container refactors

If a larger change is required, flag it as a risk instead of normal plan work.

---

# Detection Commands

When assessing the repo, run these to quantify the cleanup surface:

```bash
# Count current analyzer warnings from a build
dotnet build <solution> --no-restore -warnaserror- 2>&1 | rg -c '\bwarning\b'

# Mixed interpolation + Format (always wrong)
rg -n 'string\.Format\(\s*\$"|string\.Format\(\s*\$@"|string\.Format\(\s*@\$"' -g '*.cs'

# General Format usage (bulk conversion candidates)
rg -n 'string\.Format\(' -g '*.cs'

# Concatenation candidates
rg -n '"\s*\+\s*[A-Za-z_][A-Za-z0-9_]*|[A-Za-z_][A-Za-z0-9_]*\s*\+\s*"' -g '*.cs'
```

Record the counts in the plan as a baseline.

---

# Tooling Awareness

### Modern SDK-style projects (.NET 6/8/10+)

- Primary: `dotnet format` + Roslyn analyzers + `.editorconfig`
- Runs on Windows, Linux, and macOS

### Legacy .NET Framework projects (`net4x`, old csproj)

- `dotnet format` may require Windows for full solution load
- Run authoritative checks on Windows CI
- Note any legacy projects explicitly in the plan

---

# Output Sections (Required)

## 1. Plan ID

Start with:

```text
Plan ID: <UTC timestamp in YYYY-MM-DDTHH-mmZ>-<scope-kebab-case>
```

Example:

```text
Plan ID: 2026-03-05T14-30Z-fullsolution-cleanup
```

Use the `Plan ID` value as the filename stem and save the plan to:

```text
plans/dotnet-cleanup/<Plan ID>.md
```

---

## 2. Repository Summary

Brief summary of:

- solution and project structure
- project types (SDK-style vs legacy)
- current analyzer/editorconfig state
- existing CI style gates (if any)

---

## 3. Current State Assessment

Report:

- number of analyzer warnings (by category if practical)
- `string.Format` usage count
- concatenation candidate count
- mixed interpolation + Format anti-patterns
- naming violations observed
- any generated or excluded file patterns

---

## 4. Cleanup Phases

Structure the plan into these phases. Each phase should be executable as one or more small PRs.

### Phase 0: Bootstrap (one-time)

- Add or standardise `.editorconfig`
- Add or update `Directory.Build.props` with analyzer settings
- Add analyzer packages if not centrally managed
- Define severity policy (error / warn / info by rule group)
- Define exclusion policy (generated files, migrations, snapshots)
- Add a CI style gate: `dotnet format <solution> --verify-no-changes --severity info`

### Phase 1: Fast Mechanical Pass

- `dotnet format whitespace` for indentation, line endings, and trailing whitespace
- `dotnet format style --severity info` for code-style fixes
- `dotnet format analyzers --severity info` for analyzer-driven fixes

### Phase 2: String Formatting Standardisation

- Fix `string.Format($"...")` anti-patterns (remove `string.Format`, keep interpolation)
- Convert `string.Format("X {0}", value)` to `$"X {value}"` where safe
- Preserve explicit culture where required (invariant text, protocol payloads, localised strings)
- Keep `StringBuilder` for repeated append scenarios or clear allocation-sensitive paths
- Enable or enforce `CA2241` (format item / argument mismatch)

### Phase 3: Naming and API-Safe Cleanup

- Auto-rename private or internal symbols to policy-compliant names
- Defer public API renames unless compatibility impact is explicitly accepted
- Batch changes by module to keep PRs reviewable

### Phase 4: Manual Review and Risk Control

- Review all non-trivial string transformations
- Validate logging, SQL text composition, and protocol payload formats
- Run tests and smoke checks for serialisation- or reflection-sensitive code

---

## 5. Incremental Execution Steps

Provide an ordered checklist using markdown checkboxes.

Each step must be small and self-contained.

Example:

```text
- [ ] Add .editorconfig and Directory.Build.props
- [ ] Add CI style gate workflow
- [ ] Run dotnet format whitespace, commit
- [ ] Run dotnet format style, commit
- [ ] Run dotnet format analyzers, commit
- [ ] Fix string.Format($"...") anti-patterns
- [ ] Convert remaining string.Format to interpolation
- [ ] Rename private fields to _camelCase
```

Step 1 must be fully executable without additional planning.

---

## 6. CI Enforcement

Recommend a CI gate command:

```bash
dotnet format <solution-or-project> --verify-no-changes --severity info
```

Specify:

- where in the CI pipeline it should run
- whether it applies to all OS targets or is Windows-only (for legacy projects)

---

## 7. Risks and Assumptions

Document uncertainties.

Mark unknown items as:

`ASSUMED`

Examples:

- string formatting that affects serialisation or logging
- reflection-sensitive naming
- generated code that should be excluded
- legacy projects that may not load cleanly with `dotnet format`

---

# Constraints

The plan must:

- prioritise mechanical, automatable fixes first
- keep each phase reviewable and repeatable
- avoid behaviour changes or public API breaks
- flag anything that requires human judgement
- be reusable across other .NET repos with minimal customisation
