# Locate a Spec by Jira Key — Shared Resource

This file is included by `spec-draft`, `spec-grill`, `implement`, `branch-from-jira`, and `groom-card-for-verification`. It is a supporting resource, not a skill: it is never discoverable or invocable on its own.

## Purpose

Find the spec directory for a Jira key in `nub_specs`, reliably, on any filesystem. This partial owns the *how*; the caller decides what each outcome below means and keeps its own messages.

## Outcomes

- **found** — a matching spec in the caller's source.
- **not found** — the source was read and holds no spec for the key.
- **local spec unresolved** (read-only callers) — no published match, but a local match needs the developer's decision in step 3. Do not infer whether it is unpublished work or an obsolete copy.
- **missing locally** (authoring callers) — `main` has a matching spec that the sibling working tree lacks. Give the published path and ask the developer to reconcile the checkout before authoring; do not assume the cause, restore files automatically, write a second spec or report "no spec".
- **unavailable** — the source could not be read. For a read-only caller this includes a failed
  remote read, even when a local checkout exists: a local copy cannot show what is on `main`.

Never report an unresolved local match or an unavailable source as "no spec". Conflating them can bypass the groomed-spec gate or produce a false "no spec" advisory.

## Step 1 — Choose the source and confirm it is readable

The caller's role decides the source:

- **Authoring callers** (`spec-draft`, `spec-grill`) write the spec, so they read and write the sibling working tree. Check directly that it is present — e.g. `../nub_specs/templates/spec-template.md` exists — and report **unavailable** if not. Authoring happens on `main` only: if `git -C ../nub_specs branch --show-current` is not `main`, stop and ask the developer to switch. Then bring it up to date with `git -C ../nub_specs pull --ff-only origin main`, so a working-tree match is the current version; if the pull fails (local changes that conflict, a diverged branch, or no network), stop and ask the developer to reconcile the checkout, with the error: authoring on a copy that may be behind `main` risks deciding against superseded text. Whenever its working-tree search finds nothing — before creating a new spec, or before reporting that none exists — an authoring caller also runs the read-only search below against `main`. A published match with no working-tree copy is **missing locally**. If `main` cannot be read, say that check could not run and ask before writing a new spec.
- **Read-only callers** (`implement`, `branch-from-jira`, `groom-card-for-verification`) read the **published** spec: `nub_specs` `main`, which is what downstream links pin, read through the remote. Confirm it with `gh repo read-dir specs --repo Noetica/nub_specs` (needs `gh` ≥ 2.95, the same remote read `SHARED-AGENT-GUIDANCE.md` § Reading other repositories uses). If that fails, report **unavailable** with the error, so the user knows whether to authenticate `gh` or restore network access. A local checkout is used only to diagnose unpublished work: step 3, and the mention after a published match.

Do **not** infer availability from the search below: an empty result means "no spec for this key yet", a different condition.

## Step 2 — Search on the stable key prefix, case-insensitively, across all years

Search `specs/*/<key>-*/spec.md` in the chosen source: glob `../nub_specs/specs/*/<key>-*/spec.md` in the working tree; on the remote list `specs/` and each year with `gh repo read-dir specs/<year> --repo Noetica/nub_specs` and read a match with `gh repo read-file specs/<year>/<dir>/spec.md --repo Noetica/nub_specs`.

- **Key prefix, not the full slug.** The Jira key is deterministic; the slug is LLM-derived and can drift between the run that wrote the spec and this one, so an exact-slug match produces false misses.
- **Any project key.** The rule is key-agnostic: post-cutover cards use `ENG-nnn` (`specs/2026/eng-91-…`), pre-cutover ones use `NUB-nnnn`. Match whatever key the caller passed — never assume a prefix.
- **Case-insensitive.** Newer spec dirs use the lowercased key (`eng-91-…`, `nub-1234-…`) but historical dirs use the uppercase Jira key (e.g. `specs/2025/NUB-1739-…`). On a case-sensitive checkout, glob both `<key-lowercased>-*` and `<KEY-uppercased>-*`, or list `../nub_specs/specs/*/` and filter by prefix case-insensitively; always filter remote listings case-insensitively.
- **All years.** Don't pin to the Jira `created` year — a spec may be drafted in a later year than the card.
- **Multiple matches:** prefer the most recently modified and tell the user which you picked. On the remote, compare each candidate's latest commit date with `gh api "repos/Noetica/nub_specs/commits?path=<spec path>&per_page=1"`.

## Step 3 — Read-only callers: resolve a local match before reporting "not found"

After a successful published search with no match, search a readable `../nub_specs` working tree using the same key rules. No readable checkout, or no local match, means **not found**. A local match means **local spec unresolved**: return its path and the decision needed — should it be published, or is it obsolete? The caller presents that question, or passes it to its parent when its contract calls for an advisory handoff. Do not classify it from Git history, use it as the published spec, or fall through to a no-spec path while the decision is unresolved.

- If it should be used, it needs committing and pushing to `nub_specs` `main`; then repeat the published lookup. This lookup does not itself authorise publication.
- If the developer explicitly confirms it is obsolete, disregard that copy and report **not found** without deleting it. The confirmation holds for the rest of the session: a later lookup for the same key that finds the same local path — a chained groom after `implement`, for example — treats it as obsolete without asking again. A new session asks again while the copy remains. Resolve every local match before reporting that outcome.
- With no decision or publication yet, retain **local spec unresolved**. The caller owns its stop or advisory handoff.

When the published search matches and a readable working tree holds a different version, use the published one and mention the difference without assuming which is newer.
