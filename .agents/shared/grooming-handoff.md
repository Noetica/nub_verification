# Grooming handoff

## Contents

- [Report from grooming](#report-from-grooming)
- [Interpretation before the ready decision](#interpretation-before-the-ready-decision)

## Report from grooming

```
✓ Card groomed: <KEY>
  - Build / version: <value | pending deployment>
  - Components: <declared names> | [+ added: <names>] | [⚠ on the card but not computed: <names>]
  - Spec: <link>
⮕ Verification can now read “What changed & why” + “How to verify” directly on the card.
```

Add a line for anything `groom-card-for-verification` step 5 could not settle: a stampable repo with no ENG component, or a repo
whose stampability probe failed.

**Then end every report that reaches this step — success or skip — with these two status lines.**
They are the contract `create-pr` step 19 reads — the ones under `Status`, not the `Components:`
line inside the `✓` block above, which lists names rather than an outcome. (A chained fetch failure
at `groom-card-for-verification` step 2 returns without reaching here and emits none; the **No `Status` block at all** case below covers that missing
block.)

```
Status
  Description: written | unchanged | failed | not attempted (no spec) | not attempted (local spec unresolved) | not attempted (nub_specs unreadable)
  Components:  updated | already correct | failed | not evaluated (no spec) | not evaluated (local spec unresolved) | not evaluated (nub_specs unreadable)
```

**That is the whole lawful set, reasons included — quote one exactly, never a paraphrase.**
`create-pr` step 19 matches these strings; a reworded reason matches no row and falls to its
unrecognised-value fallback, which warns rather than stays quiet. Do not invent a value for a case
not listed here. The producer and consumer rules live together in this resource; keep them consistent.

Report the two **independently**, and never infer one from the other. The description write and the
`Components` write fail on their own terms — `groom-card-for-verification` step 5's failure explicitly does not block `groom-card-for-verification` step 7, but
it does not guarantee it either, and both can fail in the same run. A caller given one combined
outcome label cannot tell that case apart.

Values:

- `written` / `failed` — `groom-card-for-verification` step 7 attempted the description write and it succeeded / did not.
  This includes a notes-only update on an already-groomed card (`.agents/shared/grooming-writes.md`):
  classify on the write attempted, never on the headings.
- `unchanged` — **the four canonical headings were already present, so no write was attempted.**
  That is the observable, not one particular route to it: `groom-card-for-verification` step 6's chained skip reaches it, and so
  does a `groom-card-for-verification` step 3 stop on a card that was groomed earlier. Classify on the headings in the description
  `groom-card-for-verification` step 2 already fetched — never on which step you arrived from. Reporting an already-groomed card
  as `not attempted` would have `create-pr` warn that a later run is about to rewrite it, when
  `groom-card-for-verification` step 6 will skip that run too.
- `not attempted (<reason>)` — `groom-card-for-verification` step 3 stopped **and** the headings were absent. The reason decides
  the caller's next move, so it is load-bearing: `no spec` means no later run will groom it either
  (`groom-card-for-verification` step 3 stops them the same way). `local spec unresolved` needs locate-spec's decision: publishing
  enables a later groom, while confirming the copy is obsolete yields no spec. `nub_specs unreadable`
  needs a successful remote read before grooming can proceed.
- `Components` is always `not evaluated` on every `groom-card-for-verification` step 3 stop — `groom-card-for-verification` step 5 needs the spec's
  `related_repos`, which was never read — and its reason names **the stop that happened**, `no spec`,
  `local spec unresolved` or `nub_specs unreadable`, whatever `Description:` says. It carries one even where `Description:`
  is a bare `unchanged` and carries none, because each stop needs different advice from the caller:
  `no spec` needs `spec-draft`, `local spec unresolved` needs locate-spec's publish-or-obsolete decision, and
  `nub_specs unreadable` needs `gh` authenticated (2.95 or newer) or network access restored, then
  a re-groom. Never copy a reason onto
  `unchanged` — `unchanged (…)` is outside the lawful set above, and `create-pr` reads anything
  outside it as a failure.

The three stops cross with the two heading states, so there are six blocks, not three. `Components:`
names the stop in all six; only `Description:` turns on the headings:

| `groom-card-for-verification` step 3 stop | Four headings | `Description:` | `Components:` |
|---|---|---|---|
| `nub_specs` unreadable | present | `unchanged` | `not evaluated (nub_specs unreadable)` |
| `nub_specs` unreadable | absent | `not attempted (nub_specs unreadable)` | `not evaluated (nub_specs unreadable)` |
| local spec unresolved | present | `unchanged` | `not evaluated (local spec unresolved)` |
| local spec unresolved | absent | `not attempted (local spec unresolved)` | `not evaluated (local spec unresolved)` |
| no spec | present | `unchanged` | `not evaluated (no spec)` |
| no spec | absent | `not attempted (no spec)` | `not evaluated (no spec)` |

Three of those six worked in full, for the report layout rather than the values — an unreadable
`nub_specs` on a card already groomed, an unresolved local spec on one that is not, and a missing spec on
one that is not:

```
⚠ Card grooming skipped — nub_specs main could not be read (<gh error>)
⮕ Authenticate gh (2.95 or newer) or restore network access, then re-run grooming.
Status
  Description: unchanged
  Components:  not evaluated (nub_specs unreadable)
```

```
⚠ Card grooming skipped — a local spec for <KEY> has no match on nub_specs main
⮕ Decide whether to publish it or confirm it is obsolete; follow locate-spec's resolution before re-running grooming.
Status
  Description: not attempted (local spec unresolved)
  Components:  not evaluated (local spec unresolved)
```

```
⚠ Card grooming skipped — no spec for <KEY>
⮕ Run spec-draft <KEY> to give this card a spec, then re-run grooming.
Status
  Description: not attempted (no spec)
  Components:  not evaluated (no spec)
```

Lead with one line above the status block:

- groomed → the `✓ Card groomed: <KEY>` block above.
- `groom-card-for-verification` step 6's notes-only update → `✓ Card already groomed: <KEY> — release notes added` only when that write succeeded; a failed write takes the `⚠` line below with `could not update <KEY>`. A notes-only update skipped by the re-read, or because no draft was produced, reports as step 6's skip (`unchanged`), with step 4a's warning line.
- `groom-card-for-verification` step 6's skip → `✓ Card already groomed: <KEY> — description unchanged (already in the canonical format)`. Keyed on **`groom-card-for-verification` step 6**, not on `Description: unchanged`: a `groom-card-for-verification` step 3 stop can
  report `unchanged` too, but its `Components` was never evaluated, so a `✓` lead would present
  outstanding work as a finished groom.
- otherwise → `⚠ Card grooming skipped — <one-line reason>`, with the next-action line for the
  `groom-card-for-verification` step 3 stop: a missing spec → `⮕ Run spec-draft <KEY> to give this card a spec, then re-run
  grooming.`; an unresolved local spec → `⮕ Decide whether to publish it or confirm it is obsolete;
  follow locate-spec's resolution before re-running grooming.`; `nub_specs` unreadable → `⮕ Authenticate gh (2.95 or newer) or restore network
  access, then re-run grooming.`

`Components` is outstanding work in its own right whenever it is `failed` or `not evaluated (…)` —
always with its reason, never bare — even when the description needed no rewrite. The interpretation below explains why it matters
and how `create-pr` step 19 handles each reason.

## Interpretation before the ready decision

- **When the branch carries a Jira key, there is a card to protect: always read the two
  `Status` lines `groom-card-for-verification` step 8 ends with, whatever the line above them said.** A `✓` lead is not a clearance: grooming is fail-soft, so
  a run reports `✓ Card groomed` even when `Components: failed`. Read the two
  **independently** — the description write and the `Components` write fail on their own terms,
  so answer two questions rather than matching one outcome label. Both writes can fail in the same run.
  - **Will a later groom rewrite the description?** `written` or `unchanged` → no, on this run
    or a later one. `failed`, or `not attempted (nub_specs unreadable)` → yes: the next chained
    groom on this card (the second repo's PR, or a standalone run) may rewrite it. Say the
    verification handoff remains outstanding and offer to re-run grooming before flipping. For `nub_specs unreadable`, say the re-groom needs `gh` authenticated (2.95 or
    newer) or network access restored first, since the remote read is what failed. `not attempted (local spec unresolved)` → potentially:
    use the publish-or-obsolete decision that `create-pr` step 19 loads from locate-spec. Publishing enables a
    later groom that refreshes the verification handoff; confirming the copy is
    obsolete yields no spec and no rewrite. Offer to settle this before flipping; do not assume
    publication is wanted. `not attempted (no spec)` → no: `groom-card-for-verification` step 3 stops the
    next run for the same reason, so nothing is coming. **Any other value**, including a reason worded differently from
    `groom-card-for-verification` step 8's — the values are a closed set, so an unrecognised one means the report is not one
    this contract can read. Treat it as `failed`: warn and offer the re-groom, because that is
    the direction a wrong guess is survivable in. Keep these interpretations consistent with the status values above.
  - **Is the `Components` declaration outstanding?** `updated` or `already correct` → no.
    `failed` or `not evaluated (nub_specs unreadable)` → yes, and it matters on its own: an
    under-declared multi-repo card can transition out of Peer review before every repo has
    shipped. Say it and offer the re-groom for that
    reason alone — `groom-card-for-verification` step 5's `add` is additive, so a re-run cannot drop what is already there;
    for `nub_specs unreadable`, fix `gh` authentication or network access first.
    `not evaluated (no spec)` → yes, outstanding on the same grounds, but the offer is
    `spec-draft <KEY>`, **not** a re-groom: a re-run stops at `groom-card-for-verification` step 3 exactly as this one did.
    `not evaluated (local spec unresolved)` → yes, outstanding on the same grounds; resolve it
    through locate-spec. Publish-then-re-groom applies only if the developer wants that spec;
    confirming it is obsolete leaves the no-spec outcome above.
    **Any other value**, a bare `not evaluated` included → outstanding, but the reason that
    decides the action is the part that is missing. Say that, and offer both `spec-draft
    <KEY>` and the re-groom rather than guessing between them: unlike the `Description:`
    question, where every unrecognised value is safely treated as `failed`, guessing wrong here
    sends the developer to a command that cannot help.
  - **Both bad** → say both, and offer one action that addresses both: a re-groom,
    `spec-draft <KEY>` where the reason is `no spec`, or locate-spec's publish-or-obsolete
    decision where it is `local spec unresolved`.
    Never let a good value on one line suppress the warning the other line earns; each line describes an independent write.
  - **Both good** → say nothing further, and do not offer a re-groom.
  - **No `Status` block at all, though the branch carries a key** — a Jira *fetch* failure,
    or a missing grooming prompt, so nothing ever read the card. Assert nothing about its shape: say that **if** it is not
    already groomed, its verification handoff remains outstanding, and offer the re-groom.
