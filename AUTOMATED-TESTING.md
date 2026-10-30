# Automated Testing

See [Walkthrough](#walkthrough) below for instructions. This first section explains what's going to happen.

This workflow is for unit tests and in-process API integration tests only. Do not use it for true end-to-end or deployed-environment testing. For browser-level E2E testing of GUI applications, see `docs/context-pack/e2e-testing-guidance.md`.

The canonical testing rules live in `docs/context-pack/testing-patterns.md`.

By default, keep both unit tests and in-process API integration tests in one shared test project. Separate them by folders and fixtures, not by creating two different test projects, unless the repository already has a deliberate split that the team wants to preserve.

The preferred execution path is **autopilot mode** using `/automated-testing-autopilot`.

You can run this prompt two ways:

- **Copilot CLI** — pass the prompt into `copilot` with `--autopilot` (see [How to run](#how-to-run) below)
- **VS Code** — enable **Autopilot** mode in Copilot Chat, then run `/automated-testing-autopilot`

Use autopilot by default when you want to move through a plan with less human coordination overhead. The bounded batch model is intended to save human time and reduce premium-request usage compared with fully manual step-by-step execution.

## Walkthrough

1. Run `/automated-testing-plan` to create or update a plan artifact at `plans/automated-testing/<Plan ID>.md`. Review and approve the first step before implementation.
2. Run `/automated-testing-autopilot` to implement the next bounded batch from that plan. You can run this via Copilot CLI or VS Code with Autopilot mode (see [How to run](#how-to-run) below).
3. Run `/automated-testing-review` to review the new or changed tests against the same plan.
4. Run `dotnet test`. This is the primary verification path and should be part of the build when the work is done.
5. Use VS Code Test Explorer to run tests to provide visual summary of code coverage.
6. **Review the tests** and any production seams that were introduced. If the AI starts adding broad shims, DI rewrites, or unrelated production changes, stop and correct course.
7. If all looks good, commit the changes and go back to 2 to introduce more tests until the plan is complete.
8. For background on test selection and coverage targets, see [Automated Testing Guidance](AUTOMATED-TESTING-GUIDANCE.md), especially "Starting point (0% -> first pass)".

## How to Run

### Option 1: VS Code with Autopilot mode

1. Open Copilot Chat and enable **Autopilot** mode.
2. Run `/automated-testing-autopilot`.

This is the simplest path if you are already working in VS Code. You might want to start a new conversation though, to clear the context window after a few runs, since that will keep response quality high. Option 2 uses Copilot CLI with a new conversation for every run. 

### Option 2: Copilot CLI

```powershell
$prompt = Get-Content -Raw '.agents/skills/automated-testing-autopilot/SKILL.md'
copilot -i $prompt --autopilot
```

```bash
copilot -i "$(cat .agents/skills/automated-testing-autopilot/SKILL.md)" --autopilot
```

Use the planner first so the autopilot executor has a current plan artifact to work from.

The current CLI accepts prompt text, so these commands pass the prompt file contents into interactive autopilot mode.

## Advanced usage

Autopilot can continue working across multiple turns, but it still respects the CLI permission model.

- `--allow-tool` pre-approves specific tool use that would otherwise prompt.
- `--allow-url` pre-approves outbound web access to specific domains.
- `--deny-tool` and `--deny-url` override any allow rules.
- `--available-tools` and `--excluded-tools` are different: they control which tools the model can use at all, not just whether approval is required.

For this testing workflow, a reasonable safe default is to pre-approve only what the executor usually needs:

- file writes
- `dotnet` shell commands
- `git` shell commands
- the bounded continuation count

Example:

```bash
copilot \
  -i "$(cat .agents/skills/automated-testing-autopilot/SKILL.md)" \
  --autopilot \
  --max-autopilot-continues 10 \
  --allow-tool write \
  --allow-tool 'shell(dotnet:*)' \
  --allow-tool 'shell(git:*)'
```

That is a narrower alternative to `--allow-all-tools`, which removes tool approval prompts for everything. For automated test work, `--allow-all-tools` is usually broader than necessary.

If you want a wider trust setup, consider denying obviously unnecessary commands even when broad approval is enabled. For example, automated test batches should not need to push:

```bash
copilot \
  -i "$(cat .agents/skills/automated-testing-autopilot/SKILL.md)" \
  --autopilot \
  --max-autopilot-continues 10 \
  --allow-all-tools \
  --deny-tool 'shell(git push)'
```

URL allowlisting is optional for this workflow. Most batches should be able to work from repository context plus local `dotnet test` execution without any web access.

If you do want to let the agent consult documentation without prompting, sensible allowlists are:

- `docs.github.com` for Copilot CLI and GitHub workflow documentation
- `learn.microsoft.com` for .NET, ASP.NET Core, xUnit, and general Microsoft platform documentation

Example:

```bash
copilot \
  -i "$(cat .agents/skills/automated-testing-autopilot/SKILL.md)" \
  --autopilot \
  --max-autopilot-continues 10 \
  --allow-tool write \
  --allow-tool 'shell(dotnet:*)' \
  --allow-tool 'shell(git:*)' \
  --allow-url docs.github.com \
  --allow-url learn.microsoft.com
```

Only add `--allow-tool 'shell(copilot:*)'` if you explicitly want the agent to invoke the Copilot CLI from inside its own session. That is not a normal requirement for this testing workflow.

Path approval is separate from tool approval. By default, the CLI allows access to the current working directory and its subdirectories. If you want it to read or write state outside the repository, pre-allow that path explicitly. For example:

```bash
copilot \
  -i "$(cat .agents/skills/automated-testing-autopilot/SKILL.md)" \
  --autopilot \
  --max-autopilot-continues 10 \
  --allow-tool write \
  --allow-tool 'shell(dotnet:*)' \
  --allow-tool 'shell(git:*)' \
  --add-dir ~/.copilot/session-state
```

Use `--allow-all` or `--yolo` only when you intentionally want to disable tool, path, and URL prompts together.
