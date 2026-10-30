---
name: context-2-interview
description: Fill gaps and resolve unknowns in an existing context pack through guided Q&A. Use for the second context pass, after the initial pack exists.
---

# Context Pack — Guided Interview

You are running a guided interview with the repo owner to improve the context pack.

## Goals

1. Resolve unknowns in `docs/context-pack/overview.md`.
2. Capture undocumented knowledge safely and label confidence.
3. Keep the pack concise and maintainable.

## Rules

- Follow `SHARED-AGENT-GUIDANCE.md` § Tool use for question pacing and presentation. Reassess remaining unknowns after each answered round instead of marching through a fixed list.
- Prioritize questions that unblock architecture, ownership, and failure-mode understanding.
- Tag interview-derived facts as `ASSUMED` until linked to code/docs.
- Keep final edits compact; avoid narrative transcripts in the context pack.
- Follow the shared evidence, idempotency, and entry-point link conventions in `.agents/shared/context-pack-links.md`.

## Interview Focus Order

1. Business-critical flows and failure modes
2. Integration contracts and ownership boundaries
3. Operational gotchas (timeouts, retries, ordering, idempotency assumptions)
4. Compliance/privacy constraints (if relevant)

## File Updates

- Update `docs/context-pack/overview.md`:
  - Convert unknowns into confirmed facts where possible
  - Keep a small `Open Questions` list for unresolved items
- Update the `Context Pack` index in `README.md` and `AGENTS.md` if links are missing or stale, per `.agents/shared/context-pack-links.md`.

Save each resolved round into the relevant sections before the next round or a pause; keep
unanswered items open. Follow the shared tool-use batching guidance for these edits.

## Output

- After interview completion, check the accumulated updates for coherence and produce:
  - What changed
  - What remains unverified
  - Top 3 follow-up actions
