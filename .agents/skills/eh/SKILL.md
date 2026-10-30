---
name: eh
description: Explain Human — re-explain the previous reply in plain language for the Synthesys team. Use when the user invokes it by name, or says "eh?", "in English please", "what does that actually mean", or otherwise signals the last answer was too dense, jargon-heavy, or formal. Restates only — never adds new information or does new work.
---

# `eh` — Explain Human

Restate your own previous message as if explaining it to another Noetica dev at the coffee machine. Same information. Zero new claims. Zero new work.

## Rules

- Answer in the first sentence. No preamble, no "Great question".
- Strip generic enterprise jargon ("leverage", "robust", "orchestrate", "idempotent reconciliation layer"). If a plain word exists, use it.
- Synthesys vocabulary is **not** jargon here — Campaign Manager, NVP, Spider, WCF, NATS, JetStream, ACA, YARP, APIM, predictive dialler, recycling, tenant DB, Telephony SDK are fine unexplained. Don't dumb those down; the team knows them.
- If the previous answer straddled the current world (Tenant VM / Spider / WCF / APIM) and the planned world (ACA / NATS / YARP), say plainly which bits apply to which — one line each. This is the most common source of "eh?".
- Be shorter than the original. A paragraph becomes ~3 sentences; a page becomes a paragraph.
- If the original contained a recommendation or decision, end with one line: "So: do X, because Y."
- Never add new information, hedges, or caveats that weren't in the original. If the original was wrong, `eh` doesn't fix it — it just makes the wrongness easier to spot.

## Stand down

Don't apply this when the user asks for a full explanation, a document, a draft, or new analysis — those aren't `eh` requests. Format rules in CLAUDE.md or an active output style win where they conflict.
