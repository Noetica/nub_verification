<!--
Designed for human-authored PRs.
Bot-generated maintenance/sync PRs may use a lighter format.
Use the seven normal sections below. Add Rollout / Rollback / Monitoring only for an exceptional rollout.
Use `N/A` where a section does not apply; the Intent section uses only the values it names below.
Use `not required - [reason]` where a normally expected document is not needed.
-->

# Intent

Copy the Jira card's INTENT section here word for word as a blockquote (`> ` before every line),
with its source and date. For a Bug card
write `Exempt: Bug`; for a card whose INTENT section records an exemption, copy that record.
Write `N/A: no card` only when the PR has no linked Jira card (no key on the branch).

# Summary

Tell a reviewer who has the diff, card and spec what changed and why, not a tour of the changes.
Describe what was actually built and state any gap against the Intent.

# Linked Work

Include a GitHub Issue reference only when one exists.
- Jira: N/A


# Linked Documentation

- Spec: N/A
- Test plan: N/A
- Product documentation: N/A

Use links or paths where documents exist.
`Spec` should normally link to the relevant spec in `nub_specs`.
If a document is not needed, state the reason explicitly.

Examples:
- `Spec: nub_specs/specs/2026/NUB-1234-example-change/spec.md`
- `Spec: not required - routine dependency update`
- `Spec: not required - test-only verification harness change`
- `Test plan: not required - low-risk change covered by automated tests`
- `Product documentation: not required - no user-facing behaviour or configuration change`

Other not-required documentation should also be recorded here with a short reason.

# Risk Signal

- Risk: None

State `None` if no risky paths are touched.
If risky, summarise why here; include rollout notes when deployment needs exceptional handling.
For consequential changes, even when path risk is `None`, say whether they were agreed in the spec/card or added since,
including review fixes, and name any later human decision. Disclosure alone is not agreement.
Name each consequential addition or decision in a line; keep its evidence in Testing rather than
repeating it here.

# Release Note

- Tier: None
- Type: N/A
- Summary: N/A

Allowed tiers: `Development`, `Tech Support`, `Noetica`, `Partner`, `Customer`, `None`.
Choose the most specific audience that needs the note. Wider audiences can include internal readers during publishing; do not combine tiers in the PR.

Allowed types: `Added`, `Changed`, `Fixed`, `Removed`, `Deprecated`, `Security`, `Housekeeping`, `N/A`.

# Testing

State evidence that was actually observed.
If automated coverage is indirect, say so.
If manual verification is planned but not yet done, record it under `Not run / reason` rather than implying it already happened.

Name the suites or manual checks, their results and any gaps; do not list every behaviour the
tests check. Keep relevant affected areas and QA focus, and omit empty test-category placeholders.
Include `Not run / reason` for expected verification that was not performed.
Record review evidence as `.agents/shared/create-pr-review-evidence.md` specifies: fixed, refuted
and advisory findings by ID only, with accepted limitations and human decisions in full.

<!-- For an exceptional rollout only, add a visible section headed Rollout / Rollback / Monitoring.
Describe the unusual ordering, recovery or monitoring the reviewer needs in that section.
-->
