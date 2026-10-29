---
name: scenario
description: "Test ENG-nnn please, Claude" — the plain-English entry point for verification. Reads a card, finds the journeys and feature maps it touches, and runs them. Use for "Test ENG-645 please, Claude" or when Kim/Sandra describe a scenario.
---

# Scenario: Test ENG-nnn

This is how Sandra and Kim hand a card to Claude. The agent reads the card's "How to
verify" section, finds the journeys and feature maps it touches, runs Doctor, drives the
checks, and writes a result page a human can open. The agent never moves the card's
Jira status — that stays human.

## How to invoke

```bash
claude -p 'Test ENG-645 please, Claude' --allowedTools 'Bash,Read,Write,WebFetch' --max-turns 30
```

Or in the Claude Code interactive session:
```
/test ENG-645
```
(Defined as a slash command in `.claude/commands/test.md` — see below.)

## What the agent does

1. **Fetch the card.** Read ENG-645 from Jira (How to verify section). If it has no spec
   link, ask the user to run `groom-card-for-verification` first.

2. **Find the maps and journeys.** The "How to verify" section names journeys (e.g.
   "campaign lifecycle") and feature map entries (e.g. "Daily Outbound Interval View").
   Find each in `journeys/` and `maps/`. If a journey or feature is not mapped, report
   it as blocked: "no map entry for X, cannot verify."

3. **Run Doctor.** Follow the verification skill at `AGENTS.md` section 2. Check builds,
   environment, auth, reserved data, secrets. If Doctor fails, stop and report why.

4. **Set up test data** through the product, never through SQL:
   - Campaign Manager import (for journey data) — use Sarah's website write tests.
   - Report Manager pre-agreed data ranges (from `TestData/report-inputs.<env>.json`).
   - Do not fabricate results in the database.

5. **Drive the checks** per the journeys and feature maps:
   - Browser actions: `dotnet test` against the Playwright E2E harness in
     `nub_web_reportmanager/tests/ReportManager.E2E/` (`ReportManager.E2E.csproj`),
     using the test methods named in each feature map entry (e.g.
     `Export_DailyOutboundInterval_ExcelDownloads`).
   - Database reads: named queries in `tools/db/` (read-only).
   - TEFT calls: only through the `teft` skill (`.claude/skills/teft/SKILL.md`). It places the
     call, returns its verdict and checks, reads the API key at run time (ENG-825), and refuses
     any tenant that isn't on its test-tenant allowlist. Don't call the runner API directly: that
     path has no allowlist. If `teft` isn't installed, install it as the skill says, or report the
     TEFT checks as blocked.
   - Each step captures a trace and screenshot via `PageObservation.RunAsync`.
     Video recording is not yet wired into the harness (see
     `tools/fix-escalation-gap.md` Part A).

6. **Write the result page** (see `results/README.md`). State pass, fail, blocked, or
   not-run for each check. Include: deployed build identities, run ID, links to evidence
   (traces, videos, screenshots, database rows, call timelines, workbook), and a cleanup
   status reported separately from the checks.

7. **Propose a verdict.** Post a Jira comment with the summary and proposed verdict.
   A human decides and moves the card. The agent never transitions the card.

## Lines the agent never crosses

From `verification/reference/journeys-and-evidence.md`:

- Never edits product code while verifying.
- Never changes an expected value to make a result pass.
- Never moves a Jira card or transitions it.
- Expected values don't drift to match the build. A changed expected value is a change
  in what the product should do — record it with the reason and ask.
- Check before driving: the deployed builds are the ones the card names, every linked
  change is deployed, the environment is healthy. Wrong build = stop and report.
- Test the checker: one deliberately failing case per journey, so green means something.
- Non-production tenants and synthetic data only. No secrets in any repo.

## Two modes

| Mode | How | Who uses it |
|------|-----|-------------|
| **Scenario** | Kim describes what to test in plain English. The agent finds or writes the maps/journeys on the fly. | Kim, Sandra (exploratory) |
| **Card-driven** | "Test ENG-645 please, Claude." The agent reads the card's How to verify and runs the named journeys. | Kim, Sandra (card verification) |

Both feed the same evidence format. The difference is whether the journey exists already
(scenario) or is named by the card (card-driven).

## Slash command

`.claude/commands/test.md`:

```markdown
# .claude/commands/test.md
Test the card the user names. Reads its How to verify section from Jira, finds the
journeys and feature maps it touches in `nub_verification`, runs Doctor, drives the
checks, and writes a result page at `results/<run-id>/`.

Usage: `/test ENG-645` — `$ARGUMENTS` is the card key.
```
