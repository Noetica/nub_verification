# Grooming writes

## Contents

- [Components declaration](#components-declaration)
- [Idempotency and standalone refresh](#idempotency-and-standalone-refresh)

## Components declaration

`Components` is what the post-merge automation waits for: it moves the card out of Peer review only
once **every** component named on it has reported an artefact (the mechanism lives in the
`Noetica/Actions` `notify-jira` action). So the declaration has to name exactly the repos this card
will ship from. Authoring it belongs here because this session can see the spec and probe the fleet —
CI can only self-heal the repo it is currently building.

Skip this step whenever `groom-card-for-verification` step 3 stopped — no spec, local spec unresolved, or `nub_specs` unreadable. It routed to `groom-card-for-verification` step 8 without touching the card; this step needs the published spec's `related_repos` frontmatter, which was never read.

1. **Start from the spec's `related_repos` frontmatter** — the card's own statement of which repos
   the work touches.
2. **Intersect with the project's component option list.** Only names that already exist as ENG
   components can be set. Read the list from `getJiraIssueTypeMetaWithFields` (`projectIdOrKey: "ENG"`,
   the card's `issueTypeId`, `requiredFieldsOnly: false`) — the `components` field comes back with
   every option under `allowedValues[].name`. Docs repos (`nub_specs`, `nub_documents`) have no
   component and drop out here. If a genuinely stampable repo is missing a component, say so in the
   report — creating one is a one-off Jira admin job, not something to work around.
   - **If that fetch fails, do not guess and do not skip the step.** Carry the computed set into the
     `groom-card-for-verification` step 5 write and let Jira arbitrate: `editJiraIssue` rejects an unknown component name, so a
     rejection *is* the "no ENG component" answer. Re-issue the write without the rejected name (one
     `add` per request isolates which name Jira refused) and report those names exactly as this step
     would have.
3. **Filter to stampable repos.** A repo can only ever report an artefact if one of its workflows
   calls the shared `Noetica/Actions` `deploy.yml`. Probe each remaining candidate, cheapest first:
   - `gh repo read-file .github/workflows/main.yml --repo Noetica/<repo>` and look for
     `Noetica/Actions/.github/workflows/deploy.yml`. That is the common case and one call.
   - No `main.yml`, or a `main.yml` that does not call it → list the directory with
     `gh repo read-dir .github/workflows --repo Noetica/<repo>` and check the other workflows
     (`nub_svc_prioritycolumnupdater` calls it from `octopus.yml`, which is why the test is "calls
     the shared `deploy.yml`", never "has a `main.yml`").
   - Nothing calls it → **do not declare that repo.** Package repos (`nub_utils*`),
     `nub_model_repository`, dormant repos and the self-managed-deploy services fall out here: their
     merges can never stamp, so declaring one would hold the card in Peer review forever. Never
     declare `Actions` either — it is outside the automation's fleet gate entirely.
   - If a probe fails (rate limit, no access), treat that repo as **undecidable**: do not declare it,
     and name it in the report so a human can decide.
4. **Add, never remove.** Compute the set, then `add` the names that are not on the card yet. If the
   card already carries a component the computed set does **not** include — hand-added, or a repo
   dropped from `related_repos` — leave it in place and **warn**: under-declaration is the dangerous
   direction (it lets the card transition while a repo is still unmerged), so err toward declaring
   more and flag the disagreement for the human.
5. **Write it** with `editJiraIssue` using an `update` op per name, not a `set` of the whole array:

   ```json
   { "update": { "components": [ { "add": { "name": "nub_api_usermanagement" } } ] } }
   ```

   `add` is race-free, so it cannot drop a component another writer added in the meantime. Standalone
   runs preview the computed set with the description and wait for the same confirmation; chained
   runs may write directly.
6. **Fail-soft, both modes.** A components write that fails is one line in the report
   (`⚠ Components not updated — <reason>`); it must never block the description write, the PR, or
   the run. The automation self-heals the reporting repo's own component on merge, and a card with no
   components simply behaves by transitioning on the first stamp.

## Idempotency and standalone refresh

Card Shepherd writes are repeatable, and a groomed description **is** the card's INTENT section when
it has one, followed by exactly the four sections in `groom-card-for-verification` step 4 under the stable headings
(`## What changed & why`, `## How to verify`, `## Build / version`, `## Developer detail`), then the
`## Release notes` section, carried over or drafted by `groom-card-for-verification` step 4a. The
already-groomed test below keys on those four headings alone. Because a re-run replaces the whole
description with that same canonical structure, re-running never stacks a second copy — do not
append to or duplicate an existing groom.

In **chained** mode, when the card description already carries all four canonical headings:

- **Do not re-distil the four sections.** Re-distilling the same spec gains nothing. Skip the
  description write entirely and use `groom-card-for-verification` step 8's
  `✓ Card already groomed: <KEY> …` line — unless a notes-only update applies.
- **Notes-only update.** When the card is not Done, `groom-card-for-verification` step 3 did not
  stop, its `## Release notes` section is empty or absent, and `groom-card-for-verification` step 4a
  produced a draft (not when the template was unreadable), fill only that section. Immediately
  before writing, re-read the card's description and status: if it is now Done or its notes are now
  filled, skip the write; otherwise put the draft into that latest description (added after the four
  sections when absent) and change nothing else. If the re-read fails, skip the write and report it.
  Report an attempted write's actual result as `written` or `failed`, never `unchanged`.
- **Still perform step 5's `Components` write.** It is an additive `add` op on a separate field
  and is what a second repo's PR may need for the post-merge handoff.
- A **standalone** run may refresh the description, but previews it and waits for confirmation.
  Preserve the INTENT word for word and ensure the proposed verification steps match the published spec.
- **Known limit of the skip:** the test checks the headings, not whether the spec changed since
  grooming. If the spec moved during implementation, use a standalone refresh so the verify steps
  remain accurate.

On a multi-repo card, the first repo's PR grooms the card and later PRs add their components without
needlessly rewriting the shared verification handoff.
