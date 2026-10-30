---
name: context-1-initial
description: Build a first-pass developer context pack for a .NET repository with RepoMap support. Use when bootstrapping context for a .NET repo that has no context pack yet.
---

# Context Pack — Initial Pass

You are producing a concise first-pass developer context pack for this repository.

## Goals

1. Build or update `docs/context-pack/overview.md`.
2. Keep content short, evidence-based, and easy to refresh.
3. Update `README.md` and `AGENTS.md` so they keep the full current Context Pack entry-point links.

## Rules

- Follow the shared evidence, idempotency, and entry-point link conventions in `.agents/shared/context-pack-links.md`.
- Stay concise: aim for ~2 pages total in `overview.md`; prefer bullets/tables over long prose.

## Steps

1. Scan repo structure and identify:
   - Core purpose and boundaries
   - Main components/subsystems
   - Key integrations (DB, queues, APIs, services)
   - Critical flows and known fragility points (if observable)
2. Create or update `docs/context-pack/overview.md` with:
   - Repo Summary
   - Architecture at a glance
   - Key Flows (top 3)
   - Integrations
   - Risks / Unknowns (mark unknowns clearly)
3. Update the `Context Pack` index section in both `README.md` and `AGENTS.md` per `.agents/shared/context-pack-links.md`.

## Output

- Apply edits directly to the files above.
- End with a short change summary and list unresolved unknowns.
