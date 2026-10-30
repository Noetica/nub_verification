# Context Pack Conventions — Shared Resource

This file is included by the `context-*` skills. It is a supporting resource, not a skill: it is never discoverable or invocable on its own.

## Entry-point links to maintain

Every context pass keeps a short index section named `Context Pack` current in both `README.md` and `AGENTS.md`, linking each of these entry points **that actually exists** in the repo:

- `docs/context-pack/repo-map.compact.md`
- `docs/context-pack/repo-map.deep.md`
- `docs/context-pack/overview.md`
- `docs/context-pack/db-schema.md`
- `docs/context-pack/testing-patterns.md`
- `docs/context-pack/e2e-testing-guidance.md`
- `docs/context-pack/e2e-testing-bootstrapping-a-new-project.md`

Rules:

- Link only files that exist — "if applicable" always means "only if the target file already exists".
- Reuse the existing `Context Pack` section when present; create it only if missing.
- Preserve existing links (including RepoMap links) unless the target file no longer exists.
- For the entry points above, a context pass updates the index links only; `repo-map*.md`, `testing-patterns.md`, `e2e-testing-guidance.md`, and `e2e-testing-bootstrapping-a-new-project.md` are maintained elsewhere — do not edit their content from any context prompt. This does not restrict the docs a context pass owns and is expected to write (`overview.md`, `db-schema.md`).

## Evidence and confidence conventions

Used across all context-pack docs:

- Cite non-trivial claims as `path/to/file + symbol` (e.g. `src/Orders/OrderService.cs + OrderService.SubmitAsync`), or tag them `ASSUMED` when unverified.
- Tag inferred hotspot/seam findings `HEURISTIC` — they come from file size, import counts, and naming patterns, not deterministic analysis (e.g. `HEURISTIC: src/Billing/BillingCoordinator.cs appears to be a hotspot due to file size and number of responsibilities`).
- Treat every pass as **idempotent**: update existing files and sections in place; never duplicate sections or create parallel versions.
