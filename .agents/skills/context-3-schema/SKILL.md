---
name: context-3-schema
description: Build a concise database schema document with entity relationships and key data flows. Use when the context pack needs its schema section written.
---

# Context Pack — Database Schema Pass

You are building a concise DB understanding for the context pack.

## Goals

1. Create or update `docs/context-pack/db-schema.md`.
2. Request only the minimum source artifacts needed (tables/views/stored procedures).
3. Record how schema behavior affects critical flows.

## Rules

- Ask for source code/DDL only when required to reduce uncertainty.
- Do **not** dump raw DDL into the doc; summarize entities and relationships.
- Keep content concise: target ~1 page unless complexity clearly requires more.
- Follow the shared evidence, idempotency, and entry-point link conventions in `.agents/shared/context-pack-links.md`.

## Request Protocol

When evidence is missing, ask specifically for:
- Exact table/view/procedure name
- Owning schema/service
- Relevant query/procedure snippets only

## Required Sections (`docs/context-pack/db-schema.md`)

1. Purpose, Owning Component
2. Core Entities (table)
3. Key Relationships and Constraints
4. Important Views/Stored Procedures/Columns
5. Data Lifecycle Notes (write path, retention, archival if known)
6. Schema Risks / Unknowns / Gotchas

## Also Update

- Ensure the `Context Pack` index in `README.md` and `AGENTS.md` stays current per `.agents/shared/context-pack-links.md`.

## Output

- Apply edits directly and end with:
  - Confirmed DB facts
  - Remaining schema unknowns
  - Suggested next artifact requests
