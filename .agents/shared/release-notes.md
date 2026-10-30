# ENG card release notes — Shared Resource

How an agent fills the `## Release notes` section on an ENG card (ENG-828). The layout and the
writing rules are owned by `release-pipeline/release-notes-template.md` in `nub_specs`; read it from
`main` with `gh repo read-file release-pipeline/release-notes-template.md --repo Noetica/nub_specs`
before writing. If it cannot be read, do not write the section from memory: report
`⚠ Release notes not written — template unreadable` and leave the section as it is. A Jira rule has
Rovo fill an empty section when the card reaches Awaiting Verification, so nothing is lost.

The one caller is `groom-card-for-verification` step 4a; `create-pr` and `implement` reach it
through that chain. Every new ENG card is created with the heading and nothing under it
(`SHARED-AGENT-GUIDANCE.md` § Jira).

## Fill only an empty section

First check the card status fetched by `groom-card-for-verification` step 2. On a **Done** card,
preserve the Release notes section exactly as fetched, including its absence: do not fill it,
add a placeholder heading, or offer a standalone rewrite. Return it unchanged to the caller.

The section runs from `## Release notes` to the next level-1 or level-2 heading. It is **empty**
when there is no text under the heading, or no heading at all. It is **filled** otherwise.

- **Empty** → draft it, as below; the caller owns the write.
- **Filled** → leave it word for word. A person, an earlier run or Rovo wrote it, and the developer
  or verifier corrects it by hand. Preserve it in both standalone and chained runs.
- Whatever else a groom rewrites, the Release notes section is carried over as read, like INTENT.

## What to write

1. **Release audience.** Read `customfield_10532` on the card. `Customer facing` → write both the
   Internal and the Customer facing parts. `Internal` → the Internal part only. Not set → the
   Internal part only, and say in the report:
   `⚠ Release audience not set on <KEY> — set it, then add a Customer facing part if customers will notice`.
2. **Sources, in order:** the published spec (What will change, Decisions, Delivery and
   verification), the PR and its diff, the card's own evidence. Write from these; invent nothing.
3. **Release:** `Awaiting deployment approval`. The DP card rewrites it at Approved.
4. **Build:** `Component` is each repo the card ships from, `PR` is `Noetica/<repo>#<n>`, and
   `Build` is the card's `Artifact number(s)` entry for that repo, or `pending deployment` while it
   is empty. Do not set `Artifact number(s)` (that is `notify-jira`'s).
5. **Related work:** cards the card or spec links or names, one line each in the template's form.
   Only keys you have seen; mark the status as read from Jira.
6. **Support:** `No support action.` unless Technical Support will need to recognise or diagnose
   something new (a symptom customers will report, a new log line, a new setting). Then write the
   runbook in the template's Support layout with `SKB: to be assigned`, using only checks, log lines
   and actions from the card's evidence and the spec. Leave a step out rather than guess it.
7. **Customer facing part:** written fresh for a contact-centre manager, not cut down from the
   Internal text. The template's internal-terms list is the test: none of those words, no customer
   or tenant names, no ticket numbers and no card keys.

No customer PII anywhere in the section, the same rule as the rest of the groom.

## Draft and hand off

Return the drafted or preserved section to `groom-card-for-verification` step 4a; do not call
`editJiraIssue` from this resource. The caller applies its idempotency rules and writes the
description in `groom-card-for-verification` step 7, after standalone preview and confirmation, re-reading the card first so notes filled meanwhile, or a card now Done, are preserved.
That write follows `.agents/shared/jira-rich-text.md`; also check the Release notes `###`, `####`
and `#####` headings arrived as real headings, because the PDF generator reads them.
A failed write is one line in the report (`⚠ Release notes not written — <reason>`) and never blocks
the groom's other writes or the PR.
