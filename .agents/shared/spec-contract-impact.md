# Spec contract impact

Shared by `spec-draft` and `spec-grill`. Apply the section for the current phase.

Keep a `Contract Impact (breaking changes)` section when an existing consumer-visible contract
changes or compatibility needs investigation. State the material consequence in the overview
(What will change, or Summary in older specs) as well. If no such contract is affected, examined frontmatter (`breaking_change: false`) is
enough; omit empty contract/API/event/configuration subsections. Existing fuller specs remain valid.

## Draft classification

For `breaking_change`, **`TBD` is the conservative draft default until contract impact has actually been examined**. A contract includes an existing consumer-visible request, response, event/message, file format, protocol, endpoint, or behaviour an integration relies on. Not every contract change is breaking — an additive field or optional input with the old behaviour as its default may be compatible.

- If evidence clearly shows no existing consumer breaks, write `breaking_change: false`, leave `consumers: []` unless naming non-breaking consumers is useful, and explain compatibility in Contract Impact when that section applies.
- If the proposed design clearly breaks an existing consumer, write `breaking_change: true`, name every known consumer, fill in the Contract Impact section, and add an `[ESCALATE: ...]` or Open Question for `spec-grill` to challenge compatible alternatives and obtain explicit human acceptance.
- If either the existing consumers or compatibility are uncertain, leave `breaking_change: TBD`, record the evidence still needed, and name any consumers already known. Do not guess `false` merely because no consumer was found in the current repo; external consumers are exactly the ones most easily missed.

`spec-draft` does not add or remove the Jira `breaking-change` label. `spec-grill` owns that side effect after the human has resolved the compatibility decision; until then, `TBD` keeps `implement` safely gated.

## Grill decisions and propagation

- **Contract-impact state** — whether `breaking_change` is present and boolean; whether `consumers` is consistent with it; whether any required Contract Impact section agrees with both; and whether the proposed behaviour changes an existing consumer-visible request, response, event, file, protocol, or relied-upon behaviour despite being marked non-breaking.
- **Prefer compatibility before accepting a breaking contract.** When a proposal changes an existing consumer-visible contract, present the best credible non-breaking alternative and its cost, testing whether the same outcome can be achieved additively or through a compatibility path: an optional field with an old-behaviour default, a new endpoint/version beside the old one, expand/contract, dual read/write, an adapter, or a deprecation window. Record why the compatible route was chosen or rejected; do not pretend compatibility is free. If the alternatives do not meet the requirement or cost more than the break is worth, let the human explicitly accept the breaking change and record why.
- **The breaking-change flag is born at spec time and mirrored for visibility.** Treat contract impact as a required decision, not a default inherited from the template:
  - Compare frontmatter `breaking_change`, `consumers`, and Contract Impact where required against the actual proposed behaviour. Missing fields or required prose, contradictions, or an unexamined `breaking_change: false` on a consumer-visible change are unresolved queue items.
  - When the decision is `true`, set `breaking_change: true`, name every known consumer in `consumers`, and record what breaks, for whom, the coordination owner/action/due point, and the forward-fix plan. A breaking external contract generally cannot be made safe by rolling the producer back after consumers have adapted.
  - Track consumer coordination as a Jira subtask on the implementation card, not only as prose.
    Breaking changes retain the non-Standard classification and CAB review required by
    `../nub_specs/release-pipeline/change-management.md`; a shorter spec does not remove those
    existing delivery obligations.
  - Read the Jira card named by `jira_key` with `getJiraIssue`, then, if `breaking-change` is missing, write it back with `editJiraIssue` as the full existing label set **plus** `breaking-change` — `editJiraIssue`'s `labels` field replaces the whole array, so this read-modify-write is what preserves every existing label. The Jira label is a visibility signal for review, verification, and release management; it is not proof that an independent contract gate passed. If Jira is unavailable or the label cannot be applied, preserve that propagation failure as an unresolved Open Question rather than silently declaring the spec ready.
  - When the decision is `false`, set `breaking_change: false`, explain compatibility in Contract Impact when required, and leave `consumers: []` unless naming non-breaking consumers is useful. If Jira already carries `breaking-change`, surface the contradiction and ask before removing it; never silently remove a risk label or replace unrelated labels.

## Status eligibility

If `breaking_change: true`, offer `status: review` until the required independent review has happened. Offer `approved` only when that reviewer has explicitly accepted the break and the consumer-coordination plan; the author accepting their own trade-off is not independent review.
