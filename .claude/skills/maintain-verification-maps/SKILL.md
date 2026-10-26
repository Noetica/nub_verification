---
name: maintain-verification-maps
description: Scheduled maintenance pass — drives every feature map entry, ends in clean/changed/blocked, fixes drift in the skill's own directory.
---

# Maintain verification maps

Adapted from pstack's `maintain-verification-skill` for the Hermes/cron context.

## When

Runs weekly (or daily for the active track). Set via the `cronjob` tool:

```bash
cronjob action=create name=mub-maintenance-run schedule="every sunday 3am" \
  skills=scenario model=default \
  script="cd /path/to/nub_verification && claude -p 'Run the maintenance pass on the Report Manager maps' --max-turns 30"
```

## Workflow

1. **Doctor first.** Confirm the target environment is worth driving.
2. **One subagent per feature file** (parallel). Each explains "how does this
   user-facing feature work?" from source, flags likely drift, and returns a
   concise live-verification recipe.
3. **Live pass.** Drive every feature at least once. Capture:
   - Trace, screenshot, console log per browser step.
   - Database rows for data checks.
   - Result page (pass/fail/blocked/not-run) per feature.
4. **Triage.** Wrong or missing user-POV description → doc drift, fix it.
   Working behavior the harness can't drive → harness gap, fix it.
   App behavior that's actually broken → product gap, report it.
5. **Ship or stop.** One PR of proven corrections (doc drift + harness fixes only,
   never product code). For clean or blocked: no PR, report the outcome.
6. **Evidence retention.** Every run's result page survives in `results/`. A
   shrinking suite must not look like improving quality.

## Rules

- Never edit product code during a run.
- A feature the map describes that the app no longer does is either doc drift
  (fix the map) or a product regression (report it, don't paper over it).
- Skipped checks are visible as blocked, never as pass.
- One deliberately failing case per feature so green means something.
