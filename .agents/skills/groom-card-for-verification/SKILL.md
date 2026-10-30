---
name: groom-card-for-verification
description: Reshape a Jira card into a form the verification team can read and test against (Card Shepherd). Use when asked to groom a card for verification or make a card verification-ready.
---


# Groom Card For Verification

Give a Jira card a handoff the **verification team** can act on: a plain "what changed & why",
a short "how to verify", the build it ships in, and a link to the spec for the agreed behaviour.

Early cards capture a short request and useful evidence (`.agents/shared/card-intent.md`). Older
cards may contain a dense RCA or design. This prompt gives either form its verification handoff
once the change is built. It does **not** change how cards are authored, and it does **not** move
the card's status (that is `create-pr`'s job).

This prompt operationalises `DevOps/card-shepherd/10-card-standards.md` in `nub_specs`. Read it from
`main`, the same published source as the spec (step 3), with
`gh repo read-file DevOps/card-shepherd/10-card-standards.md --repo Noetica/nub_specs` — never from
a local checkout, which may be absent or stale. That contract is canonical — if a rule conflicts
with this prompt, the contract wins.

`create-pr` runs this prompt automatically after creating a PR and transitioning the card to Peer
Review. It can also be run standalone at any time — `groom-card-for-verification NUB-2218` — to
retrofit existing cards.

**Why `create-pr` opens the PR as a draft.** Finish the card's verification handoff before the
developer chooses to start normal automated review. Preserve the human INTENT and keep the PR's
claims accurate. A chained run against an already-groomed card skips needless description rewrites
and updates `Components` only (step 6); use a standalone refresh when the spec has changed.

## Goals

- Produce a card a tester can use without reading the spec, the diff, or the supporting investigation.
- Distil **from the spec**, never regenerate — the card view is a projection of the spec.
- Link supporting detail at its source; never duplicate it into Jira.
- A card with no spec is preserved. With a spec, replace the description below INTENT with the
  verification view; Jira history retains the prior description. The spec holds required behaviour,
  while supporting investigation may be in `grill-record.md`; do not claim all prior detail is in the spec.
- Keep the card's INTENT section (or its exemption record) unchanged at the top: it is the
  requester's own words, not a projection of the spec (`.agents/shared/card-intent.md`).
- Declare the repos the card will ship from in `Components`, so the post-merge automation knows when
  the card is actually verifiable.
- Fill an empty `## Release notes` section, and carry a filled one over word for word (step 4a).
- Stay advisory and fail-soft when chained: never block or retract the PR.

## Run modes

Run mode and Jira-key resolution are **independent**. The mode is set by the caller — never inferred
from whether a key was supplied.

| | Standalone (human runs `groom-card-for-verification [KEY]`) | Chained (invoked by `create-pr`) |
|---|---|---|
| How you know which | the default — any invocation not explicitly declared chained | `create-pr` step 18 invokes this prompt in chained mode |
| Jira key | the explicit argument if given, otherwise derived from the branch | derived from the branch name (`[A-Z]+-\d+`) |
| Missing/unfetchable card | **refuse** — it is the whole point of the run | **fail-soft** — log one line, do not block the PR |
| Before writing | draft → **preview → confirm**, always (even when the key came from the branch) | may write directly (the dev is present), then print what it wrote — unless the card is already groomed, when the description write is skipped entirely or limited to a notes-only update (step 6) |

## Instructions

### 1. Determine the run mode and resolve the Jira key

These are two separate decisions — do not let one drive the other.

- **Mode:** you are in **chained** mode only when `create-pr` invokes this prompt as part of its
  post-PR flow. Every other invocation is **standalone**. A standalone run always previews and waits
  for confirmation before writing, regardless of where the key came from.
- **Key:** if an explicit argument is given, use it; otherwise derive it from the current branch
  (first `[A-Z]+-\d+` match). Validate `[A-Z]+-\d+`.
  - Standalone, no valid key → refuse with an example (`groom-card-for-verification NUB-2218`).
  - Chained, no key on the branch → stop with a one-line fail-soft note; there is nothing to groom.

### 2. Fetch the card

Call `getJiraIssue` (`responseContentFormat: markdown`; include `summary`, `description`,
`status`, `comment`, `components`, and the **`Artifact number(s)`** custom field (`customfield_10465`
on the ENG project). If you don't have that field's `customfield_*` id, fetch with
`fields: ["*all"]` and `expand: "names"` and match it by its display name `Artifact number(s)`.
`components` is needed by step 5 — the repos the card is expected to ship from. Include
**`Release audience`** (`customfield_10532`) too, for step 4a.

- Standalone and the fetch fails → refuse (same policy as `spec-draft`'s fetch): the card is
  essential input, not bonus output.
- Chained and the fetch fails → fail-soft: `⚠ Card grooming skipped — could not fetch <KEY>` and
  return control. The PR is unaffected.

### 3. Locate the spec — the source of truth

Read and follow `.agents/shared/locate-spec.md` as a read-only caller — it reads the published spec
on `nub_specs` `main`, searching case-insensitively across all years (historical spec directories
are uppercase; a lowercase-only search misses them and skips a groomable card). **Local spec
unresolved** and **unavailable** are their own outcomes, never "no spec": a card is groomed only
from the published spec. For a local match, standalone → ask locate-spec's publish-or-obsolete
question and stop until resolved, then use its resulting lookup outcome; chained → ask no question,
skip to step 8 with the unresolved outcome, and let `create-pr` step 19 present the decision.
For unavailable, standalone → stop and ask to authenticate `gh` or
restore network access; chained → skip to step 8. Let its `Status` block carry the outcome, using `local spec unresolved` or
`nub_specs unreadable` wherever step 8's value takes a reason. Do not compose a report line here, and do not invent a
status value: `create-pr` step 19 matches step 8's exact strings and is forbidden from guessing, so a
bare "not available" line — or a reworded one — leaves it no lawful move. The **Report from grooming** section of `.agents/shared/grooming-handoff.md` is the
home for how the two lines are filled in, including that `Description:` is classified on the four
canonical headings in the description step 2 already fetched.

- **Spec found** → read it. This is the canonical source for every distilled section. Supporting
  investigation may be in its grill record; the required behaviour stays in the spec. Read the contract
  from `main` as described above; if that read fails, handle it as **unavailable**. Continue to step 4.
- **No spec** (common for older cards) → **do not rewrite the description, and do not fabricate.**
  The contract requires every verify step to trace to a spec Acceptance Criterion or manual verification
  note, and a card with no spec is *preserved, not overwritten* (`10-card-standards.md`). With no
  spec there is nothing to ground the card view in, so grooming stops here without touching the card:
  - Standalone → report that the card needs a spec first and recommend `spec-draft <KEY>`, then
    re-running grooming.
  - Chained → let step 8's `Status` block carry the outcome, using `no spec` wherever its value
    takes a reason. Do not compose a report line here either: step 8's lead-line rule already emits
    one, with the `spec-draft` pointer.
  - Either way the card description and the PR are left untouched. Skip to step 8.

### 4. Distil the four sections (per `10-card-standards.md`)

Keep to the contract's order and length limits. Distil; do not invent. The card's INTENT section,
when it has one, is not distilled: step 7 carries it over as read.

1. **What changed & why** — 2–4 plain-language sentences on the behaviour change and why it
   matters. Use the **internal** release-note framing (Development / Tech Support / Noetica voice),
   not the polished Customer note. Source: What will change (Summary in older specs) and any release-note summary. Name the
   user-/operator-visible outcome, not the class names or line numbers.
2. **How to verify** — at most 5 tester-actionable steps in "set up *this* → do *that* → expect
   *this*" form. Source: Acceptance Criteria + any manual commitments in Delivery and verification (Manual-testing notes in older specs). **Every step must
   trace to an AC or a manual verification commitment** — if you cannot ground a step, leave it out. Prefer a
   single concrete reproduction over an exhaustive matrix; an exhaustive plan belongs in a linked
   test plan, not the card.
3. **Build / version** — state the card's **`Artifact number(s)`** field as it stands, or
   `pending deployment` when it is empty. The field is a **per-repo ledger**, so expect
   more than one value on a card that spans repos: `repo: version` entries joined by `; ` (the field is a
   multi-line textarea in the card body, so a hand-edited card may instead carry one entry
   per line; treat both shapes the same), e.g.
   `nub_api_usermanagement: 2607.2837.01; nub_web_usermanagement: 2607.2876.01`. A repo whose merge
   produced no build carries the token `docs-only` in place of a version.
   - One entry → state it plainly. More than one → render a short repo → artefact list or table, so
     a tester can see which build belongs to which repo.
   - An older card may carry a **bare version with no repo prefix** (from the older field format). State
     it verbatim; do not reformat it or guess which repo it came from.
   - If the card declares repos in `Components` that have **no entry yet**, say which are still
     pending — the card has not fully shipped, and the automation is deliberately holding it in Peer
     review until they report.
   - **Do not** set `Artifact number(s)` yourself — that write-back is owned by the post-merge
     `notify-jira` CI leg, not Card Shepherd.
4. **Developer detail** — a link to the spec: the GitHub URL
   (`https://github.com/Noetica/nub_specs/blob/main/specs/<year>/<key-slug>/spec.md`) if known,
   else the repo path.

Guardrails:
- **No customer PII** (e.g. full phone numbers) in any section — the spec already flags PII in logs.
- **No invented steps, statuses, or outcomes.** If the spec is silent, say so; don't fill the gap.

### 4a. Release notes

Read and follow `.agents/shared/release-notes.md`. An empty `## Release notes` section is drafted
from the spec, the PR and the card; a filled one is carried over as read. The card's Release
audience (`customfield_10532`) decides whether a Customer facing part is written: fetch it with step
2's fields. Only reached with a published spec: when step 3 stopped, the section is left for the
Rovo fallback at Awaiting Verification. A Release notes problem is one report line and never blocks
the rest of the groom.

### 5. Author the `Components` declaration

If step 3 stopped, skip this step: the published spec's `related_repos` was not read. Otherwise
read and follow `.agents/shared/grooming-writes.md` **Components declaration**. Compute exactly the
stampable repos with existing ENG components from `related_repos`, probe the fleet, and add only
missing names. Preserve existing components and warn about disagreements or undecidable repos.
Standalone runs preview the set with the description and wait for confirmation; chained runs may
write directly. Failure is advisory and does not block the description write or the PR.

### 6. Idempotency

The already-groomed test is the presence of all four canonical headings from step 4. In chained
mode, never re-distil those sections when they exist, while still doing step 5's additive
`Components` write: a re-distillation can introduce needless wording churn even when the meaning
stays the same. Skip the description write entirely, unless the **notes-only update** in
`.agents/shared/grooming-writes.md` applies (a card not Done whose Release notes section is empty or
absent, and step 4a produced a draft): then fill only that section, into a description re-read
just before writing.

Read `.agents/shared/grooming-writes.md` **Idempotency and standalone refresh** when the card already
has those headings, or when running standalone. It defines the skip, the known stale-spec limit,
and the standalone preview before a rewrite. A standalone refresh
still previews and requires confirmation; use it when the spec changed and the card needs a new
projection. Re-runs replace the canonical structure, never append or stack another groom.

### 7. Preview, then write

Compose the new description as the four sections above, in order. When the fetched description has
an INTENT section, put it first, word for word as read. It ends where `card-intent.md` says: at the
next level-1 or level-2 heading or a horizontal rule, so other card content and any earlier groom's
four headings stay out of it. Place it above everything this prompt writes. It is the human's text,
already on the card, so it is carried over as written; step 4's guardrails govern the sections this
prompt writes, and the no-PII rule for the INTENT's copies lives in `card-intent.md`. An empty
section counts as none: leave it out. After the four sections comes `## Release notes`, as step 4a
left it: carried over word for word, or newly drafted. On Done cards preserve exactly what was
fetched, including no heading when absent. Otherwise never drop it, even when empty: the heading
is what the Rovo fallback and the PDF generator look for.

- **Chained, and step 6's skip applies** (the card already carries all four canonical headings and
  no notes-only update applies): do not write the description at all. Go straight to step 8 and
  report it as already groomed. Step 5's `Components` write still happens.
- **Chained, notes-only update** (step 6): apply the re-read below; skip if the card is now Done or
  its notes are now filled. Otherwise write that latest description with only the Release notes
  section filled, verify it as below, and report the write's result in step 8.
- Standalone: print the proposed description and **wait for confirmation** before writing.
- Chained (card not yet groomed): you may write directly; still print what you wrote afterwards.

**Re-read before every description write.** Immediately before calling `editJiraIssue`, fetch the
card's description and status again. Take the Release notes section from that fresh read when its
notes are filled or the card is now Done (preserving a Done card's section exactly, including its
absence); use step 4a's draft only when the fresh section is still empty and the card is not Done.
If the re-read fails, skip the write and report it as `failed`. In a standalone run, if this changes
what was previewed, preview again and wait for confirmation before writing.

Write with `editJiraIssue`, following `.agents/shared/jira-rich-text.md` — the single home for
Jira rich-text writes: the format to send, the escaping traps, and how to verify what landed. The
verification there is what confirms the four headings arrived as real headings rather than literal
markup. Do **not** transition the card and do **not** touch labels, assignee, or the
`Artifact number(s)` field. `Components` is the one other field this prompt writes, and only as
step 5 describes.

The current description becomes the verification view. Jira retains the previous description in
its edit history; required behaviour stays in the spec, and supporting investigation may be in
`grill-record.md`. The canonical spec link is not a claim that the spec holds every earlier note.

- Write fails → standalone: report the error and the drafted body so the user can paste it.
  Chained: fail-soft (`⚠ Card grooming skipped — could not update <KEY>`), PR unaffected.

### 8. Report

Read and follow `.agents/shared/grooming-handoff.md` **Report from grooming**. It is the single home
for this report's lead lines, exact `Status` values and their interpretation by `create-pr` step 19.
End every report reaching here, including skips, with its two status lines. Classify Description
and Components independently; an earlier step 3 stop uses the fetched headings to distinguish an
unchanged description from one not attempted, while Components records the stop reason. Preserve
those exact values and use the resource's outcome-specific next-action line. A chained fetch
failure in step 2 returns before this report and emits no status block.

## Output rules

- The end state is an updated Jira card (or, standalone, a previewed body awaiting confirmation) —
  not just drafted text. Several outcomes leave the description untouched — no spec (a
  recommendation instead of a rewrite), an unresolved local spec or an unreadable `nub_specs` (each its own outcome,
  never "no spec" — step 3), a card already groomed with nothing but filled or Done-card notes
  (step 6), and a failed write (step 7) — which
  is why the report's `Status` block states `Description:` outright instead of leaving the caller
  to count cases.
- Keep the card sections short and test-actionable; match the contract's headings exactly so
  re-runs stay idempotent.
- Do not fabricate verify steps, build numbers, links, or outcomes.
- When chained, every failure is advisory: one line, never a block or retraction of the PR.

## Scope

- One card per run. No bulk grooming.
- Does not move card status, set the `Artifact number(s)` field, or edit labels/assignee. It does author
  `Components` (step 5) — additive only, never removing what a human put there.
- Does not set Release audience or rewrite a filled Release notes section (step 4a).
- Does not author or edit the spec — that is `spec-draft` and `spec-grill`.
- Does not rewrite a card that has no spec yet — it recommends `spec-draft` instead.
- Does not rewrite a card when `nub_specs` is unreadable — that is its own outcome, reported
  never as "no spec" (step 3).
- In chained mode, does not rewrite a description that is already groomed — it writes `Components`,
  plus the Release notes section alone when that is empty or absent on a card not Done, preserving
  the existing verification handoff for companion PRs (step 6).
