---
name: dotnet-cleanup-execute
description: Execute one step from the current .NET cleanup plan. Use when asked to run, continue or apply the next cleanup step.
---

# .NET Code Cleanup Executor (Single Step)

Execute exactly **one step** from the latest cleanup plan.

Do not execute additional steps beyond the one selected.

Plan artifacts live in:

`plans/dotnet-cleanup/<Plan ID>.md`

If no cleanup plan artifact exists there, stop and tell the human to run the planner first.

---

# Workflow

1. Locate the **latest cleanup plan artifact** (not the prompt template) in `plans/dotnet-cleanup/`.

If multiple plan artifacts exist and the human has not named one:

- prefer the one referenced by the current branch or PR
- otherwise choose the most recently modified file

2. Read the plan and extract its **Plan ID**.

3. Select the **first incomplete execution step**.

4. Execute **only that step**.

5. Run verification after each change.

6. Iterate up to **3 fix attempts**:

- run the smallest relevant verification command
- fix the smallest issue
- re-run verification

If still failing after 3 attempts, stop and report blockers.

7. Before stopping, do a short self-review against the selected plan step, the existing repository conventions, and the mechanical-only cleanup boundary. Fix any clear in-scope issue you find.

---

# Phase 0: Bootstrap

If the selected step is bootstrap:

1. Check for an existing `.editorconfig`. If missing, create one with the standard rules below. If present, merge missing rules without overwriting repository-specific customisations.
2. Check for `Directory.Build.props`. If missing, create one. If present, add missing analyzer properties.

Required `.editorconfig` baseline:

- `root = true`
- UTF-8, LF line endings, final newline, trim trailing whitespace
- 4-space indent for most files, 2-space indent for YAML, JSON, XML, props, and csproj files
- C# sections: sorted usings, naming conventions, and style preferences

Required `Directory.Build.props` baseline:

```xml
<Project>
  <PropertyGroup>
    <EnableNETAnalyzers>true</EnableNETAnalyzers>
    <AnalysisLevel>latest-recommended</AnalysisLevel>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
  </PropertyGroup>
</Project>
```

3. Verify the solution still builds:

```bash
dotnet build <solution>
```

---

# Phase 1: Fast Mechanical Pass

Execute formatting commands in this order:

```bash
# 1. Whitespace only
dotnet format whitespace <solution>

# 2. Code style
dotnet format style <solution> --severity info

# 3. Analyzer fixes
dotnet format analyzers <solution> --severity info
```

After each command:

- review the diff for unexpected changes
- verify the solution builds
- run tests if available

Commit each sub-step separately with a descriptive message.

Example commit messages:

```text
chore: dotnet format whitespace
chore: dotnet format style fixes
chore: dotnet format analyzer fixes
```

---

# Phase 2: String Formatting Standardisation

### Fix Rules (in priority order)

1. **`string.Format($"...")`** is always wrong. Remove `string.Format` and keep the interpolated string.

Before:

```csharp
string.Format($"Hello {name}")
```

After:

```csharp
$"Hello {name}"
```

2. **`string.Format("X {0}", value)`** should be converted to interpolation where safe.

Before:

```csharp
string.Format("Order {0} placed at {1}", orderId, timestamp)
```

After:

```csharp
$"Order {orderId} placed at {timestamp}"
```

3. **Preserve explicit culture** when the format string is used for:

- invariant text or protocol payloads
- localised user-facing strings
- logging frameworks that handle formatting themselves

4. **Keep `StringBuilder`** for:

- repeated appends in loops
- measured or obvious allocation hotspots

5. **Simple concatenation** can be converted to interpolation when readability improves.

Before:

```csharp
"Hello " + name + "!"
```

After:

```csharp
$"Hello {name}!"
```

### Verification

After changes:

- build the solution
- run all tests
- search for remaining `string.Format` usage and confirm each remaining instance is justified
- check for serialisation-, logging-, or protocol-sensitive strings that may have changed behaviour

---

# Phase 3: Naming and API-Safe Cleanup

Rules:

- Rename **private fields** to `_camelCase` using `dotnet format` or manual refactoring
- Rename **private/internal methods and locals** to comply with `.editorconfig` naming rules
- Do not rename **public API members** unless the plan explicitly approves it
- Batch changes by project or module to keep diffs reviewable

After changes:

- build the solution
- run all tests
- verify no public API surface has changed

---

# Phase 4: Manual Review and Risk Control

This phase requires human judgement. Flag the following for review:

- non-trivial string transformations, especially in logging, SQL, or serialisation
- reflection-sensitive naming changes
- format strings used in protocol payloads
- any change where behaviour correctness is uncertain

Do not auto-fix items in this phase. Instead, produce a **review checklist** listing:

- file path
- line number
- what was found
- recommended action
- risk level (`low`, `medium`, or `high`)

---

# Production Code Limits

All changes must stay **mechanical and style-only**.

Do not:

- change public API signatures
- alter control flow or business logic
- add or remove dependencies
- refactor architecture
- change exception-handling behaviour

If a fix requires semantic changes, flag it and skip it.

---

# CI Gate Verification

After completing any phase, verify the style gate passes:

```bash
dotnet format <solution> --verify-no-changes --severity info
```

If this command is not yet in CI, note it as a remaining task.

---

# Plan Status Update

After completing the step:

If the plan uses checkboxes:

```text
- [ ] step description
```

change to:

```text
- [x] step description
```

Add a short completion note if useful.

If the plan does not use checkboxes, output a **plan status update snippet** instead of editing the file.

---

# Output Format

Produce the following sections.

---

## Plan Selected

Path to the plan file and the **Plan ID**.

---

## Phase Executed

Describe which phase and step was executed.

---

## Commands Run

List each command and its outcome.

Example:

```text
dotnet format whitespace RepoMap.sln - 14 files changed
dotnet build RepoMap.sln - success
dotnet test - all tests passed (8 tests)
```

---

## Files Changed

List all modified or created files.

---

## Remaining Issues

List anything that was skipped or flagged for manual review.

---

## Plan Status Update

Show the updated checklist or snippet.

---

## Next Step

Indicate the next incomplete step from the plan.
