---
name: context-4-edit
description: Reduce duplication and tighten signal across an existing context pack. Use when the context pack has grown repetitive or noisy.
---

# Context Pack — Optional Edit/Reduce Pass

You are a second-pass editor (ideally a different LLM) to reduce size and improve signal.

## Goals

1. Review `docs/context-pack/overview.md` and `docs/context-pack/db-schema.md`.
2. Remove duplication, vague wording, and low-value detail.
3. Preserve factual correctness and evidence tags.

## Rules

- Do not add net-new claims unless they are clearly evidenced.
- Prefer shorter bullets, tighter tables, and explicit unknowns.
- Keep total context-pack size lean (default target: ~2-3 pages combined).
- Preserve citations and `ASSUMED` tags.
- Follow the shared evidence, idempotency, and entry-point link conventions in `.agents/shared/context-pack-links.md`.

## Editing Checklist

1. Merge repeated content across docs
2. Replace generic statements with concrete, scoped wording
3. Move low-confidence content into `Risks / Unknowns`
4. Ensure `README.md` and `AGENTS.md` still expose the full current Context Pack links, per `.agents/shared/context-pack-links.md`

## Output

- Apply edits and report:
  - Approximate size reduction
  - Any statements downgraded to `ASSUMED`
  - Any remaining ambiguous areas
