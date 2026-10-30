---
name: context-5-refresh
description: Refresh a context pack against current evidence and remove claims that no longer hold. Use when an existing context pack has gone stale.
---

# Context Pack — Refresh / Staleness Check

You are refreshing the context pack and identifying outdated content.

## Goals

1. Detect stale or drifting statements in context-pack docs.
2. Update docs in place with current evidence.
3. Keep docs concise after refresh.

## Scope

- `docs/context-pack/overview.md`
- `docs/context-pack/db-schema.md`
- `README.md` and `AGENTS.md` context-pack links
- Other entry-point files (`repo-map*.md`, `testing-patterns.md`, `e2e-testing-guidance.md`) are out of edit scope, per `.agents/shared/context-pack-links.md`

## Rules

- Treat refresh as a diff against current repo reality.
- For each stale claim found, either:
  - update with evidence, or
  - mark as `OUTDATED`/`ASSUMED` with a follow-up note.
- Remove dead sections rather than accumulating historical clutter.
- Keep wording concise and operational.
- Follow the shared evidence, idempotency, and entry-point link conventions in `.agents/shared/context-pack-links.md`.

## Refresh Procedure

1. Re-scan relevant code/docs for each major claim.
2. Build a quick stale-claim list (claim, old basis, new evidence).
3. Patch docs in place.
4. Ensure the `Context Pack` index in `README.md` and `AGENTS.md` stays current per `.agents/shared/context-pack-links.md`.

## Output

- Apply edits and provide:
  - Stale claims fixed (short list)
  - Claims still unverified
  - Suggested refresh cadence (e.g., monthly or per major change)
