# Card INTENT — Shared Resource

Read this before proposing a card, drafting or grilling a spec, implementing a card, grooming it,
reviewing its change or writing its PR description. `SHARED-AGENT-GUIDANCE.md` § Jira conventions
points here. It is a supporting resource, not a skill: it is never discoverable or invocable on its
own.

## What it is

The INTENT is a human's own statement of what a change is for. Only "what we want to achieve" is
needed; "what must not change" and any constraints are optional. On a card that belongs to a
project with a brief, it says what this change contributes and may link to the brief. Do not ask
for the project's purpose to be restated.

It is the first section of the card description, headed `## INTENT`, and the card is its only
source. The section runs from that heading to the next level-1 or level-2 heading, or a horizontal
rule; level-3 and deeper headings inside it are part of it. A section with no text of its own, only
the empty heading, counts as no INTENT; any text in it is the human's and is kept. On a card that
needs one, it replaces the TL;DR: there is no separate agent summary above it.

## Which cards need one

- **A Bug** (`fields.issuetype.name` is `Bug`) is exempt. Do not ask; its type is the record.
- **A Subtask** uses its parent's INTENT or recorded exemption, and a Subtask of a Bug is exempt as
  a Bug (`fields.parent.fields.issuetype.name`). `fields.parent` does not carry the parent's
  description, so fetch the parent with `getJiraIssue` and read its INTENT section; if that fetch
  fails, stop as the calling skill does when its own card fetch fails. Wherever the skills say "the
  card's INTENT", for a Subtask that means the parent's, attributed to the parent's key. Ask only
  when the parent needs an INTENT and has neither, and record the answer on the parent. A Subtask's
  own description never gets an INTENT section.
- **Any other card** needs an INTENT, unless its INTENT section holds a recorded exemption.

Only the human decides that a non-Bug card is a bug fix or a minor chore; an agent never decides the
exemption itself. A declared chore still has an INTENT section, holding its exemption record.
Exempt cards use the brief description below, and still get ordinary questions when the problem
or the expected behaviour is unclear. Card grooming later replaces everything else on the
card, TL;DR included; only the INTENT section survives it.

## Proposing a card

A new card captures the request, not a preliminary specification. Use the smallest description
that lets a colleague understand or investigate the work:

- **Feature or task:** `## INTENT`, using the human's supplied words, or empty for them to fill.
  Add a short context paragraph or source link only when it explains the request. Do not repeat
  the intent in a summary, goals or acceptance criteria.
- **Bug:** a short `## TL;DR` stating expected versus observed behaviour, followed by useful
  evidence: reproduction steps, environment/version, a concrete example or a log/link. Include
  what is known; do not invent reproduction steps, root cause or a fix, or demand every field.
  Preserve an existing human INTENT when the bug has one; the exemption avoids asking for one.
- **Human-declared chore:** the exemption record in `## INTENT`, with a brief TL;DR below only
  if it adds useful context, under its own `## TL;DR` heading.
- **Subtask:** use its parent's INTENT or exemption; state only its own contribution.

For every card with an INTENT section, keep only the human's words or exemption record inside it.
Start following context, evidence or proposals under a separate level-2 heading or after a
horizontal rule, so they cannot become part of INTENT, even when that section is empty.

Do not add approach, architecture, rollout, risk, test-plan or decision sections by default.
Preserve a real constraint or explicit decision already supplied by the human, even when it is
technical. If a proposed approach from the conversation is worth keeping, label it **Proposed**
and give its direction in a sentence or two; file-level edits and rule wording wait for the spec. A known blocker or unanswered question earns space when it affects pickup;
do not generate a questionnaire just to make the card look complete. Detailed investigation
belongs in linked evidence, and design follows in the spec when needed. This is the creation
shape; the later verification handoff has its own card format.

Keep the description a current account of the request, not an accumulating delivery diary.
Put detailed investigation and progress history in linked records or existing comments; keep only
the current outcome, essential evidence and pointers in the description.

**Attribution is evidence, not formatting.** Attribute a decision to a person only when they
said it or explicitly accepted that choice. Approval to create a card is not blanket acceptance
of agent-generated detail. A person's name in an existing card's Decisions heading alone is not
proof of that acceptance. Keep uncertain provenance as a proposal for the spec walkthrough;
do not invent a quotation or confirmation. The INTENT itself remains the human's source text.

## When a card has none: ask once

When `spec-draft` or `implement` meets a card that needs an INTENT and has neither an INTENT nor a
recorded exemption, it asks the human one question and waits. Do not proceed on an invented INTENT,
and do not write one yourself:

> `<KEY>` has no INTENT. In your own words, what is this change for? Only what you want to achieve is
> needed. If it is a bug fix or a minor chore instead, say so and I'll record that on the card.

- **The human writes it on the card:** read the card again and use that text.
- **The human gives it in chat:** show exactly what you will write, then write it onto the card word
  for word as the first section.
- **The human says it is a bug fix or a chore:** record that in the INTENT section in place of intent
  text, as their answer with their name and the date, for example
  `Exempt: minor chore (version bump). Luke Harris, 2026-09-27.` Show it before writing. Later
  skills, and the card's Subtasks, read the record and do not ask again.

Write to the card with `editJiraIssue`, following `.agents/shared/jira-rich-text.md`. Read the card
immediately before the write and compose from that read, leaving the rest of the description as it
is. After the write, read the card again, including the rendered view `jira-rich-text.md`
requires, and confirm the stored section is a real `INTENT` heading holding the text you showed;
from then on use that re-read card, including where a skill would otherwise reuse the card already
in hand (a chained `spec-grill`, for example). If the write fails, or the re-read does not match,
say so, show the exact text for the human to put on the card, and do not continue as if the card
carries it. If a PR already uses an earlier INTENT, report the change and refresh its copy;
never present the earlier review as covering the changed requirement.

When the human asks for help finding the words, you may suggest some, but the final text is theirs:
plain language, not agent phrasing, and never polished without being asked.

## Copies are word for word

The spec's Intent section and the PR description each carry the card's INTENT (or its exemption
record; `Exempt: Bug` for a Bug; `N/A: no card` when there is no linked Jira card) unchanged, marked
with its source and date and quoted as a blockquote, every line prefixed, so headings inside it do
not start sections of the spec or PR. The groomed card keeps its INTENT section as it stands.
No restatement, condense or grooming pass edits a copy.

A copy is current when its quoted text matches the card's INTENT section, or its exemption record,
or is `Exempt: Bug` for a Bug, or `N/A: no card` when there is no linked Jira card; the
source-and-date line is not part of the comparison. If a copy and the card disagree, the card wins:
refresh the copy.

A card that needs an INTENT and has neither one nor an exemption has nothing to copy. Apart from
`spec-draft` and `implement`, which ask, a skill that meets such a card leaves the copy absent
(`create-pr` instead stops before any push or PR), says so, and gives the recovery: the human writes
the INTENT on the card, or runs `implement <KEY>`, which asks (`spec-draft` only when there is no
spec yet). It never composes INTENT text.

If the INTENT holds customer PII or a secret, do not copy it into the spec or PR: ask the human to
revise the card, then copy the revised text.

## When the human changes it

The INTENT is treated as stable while the work runs. Only the human changes it, for example when
implementation shows the original was misguided, and the human makes the change of direction clear
and decides whether to revisit the spec or restart. Agents are not expected to notice edits nobody
mentioned.

When you know the INTENT has changed:

- Say what the change means for work already done, and recommend revisiting the spec or restarting
  where that fits. The decision is the human's.
- Never present an earlier review as covering the new text.
- A dated line at the end of the card's INTENT section records the change,
  `Changed <date> by <name>: <what changed and why>`. If the card lacks one, offer to add it,
  showing it first.
  It is part of the section, so a copy refreshed afterwards carries it.

## Working to it

The INTENT is the target, above the spec's acceptance criteria. A spec decision, plan step or
review fix that conflicts with it is raised with the human as a question. Never resolve the conflict
by narrowing the INTENT or by quietly departing from it.

Satisfying INTENT does not authorise every addition that might help. Keep material changes within
the human-agreed scope. Consequential changes include effects on observable behaviour, existing
data, permissions, configuration, external contracts, architecture, dependencies, deployment,
cost, ongoing maintenance or other operational obligations, including effects across repositories.
This is the shared definition for drafting, grilling, implementation and review remedies; callers
refer here rather than maintaining their own lists. Explain an additional consequence, its
reason and the simpler alternative, and obtain a decision before adopting it. Existing code is
evidence of constraints, not authority to choose new policy. A plan written by the agent cannot
expand the agreement. Ordinary implementation choices and repairs that preserve agreed behaviour
stay with the implementer; do not ask about every helper or existing validation check. If a real
safety constraint conflicts with the agreement, surface that conflict rather than silently adding
a new control or weakening the constraint. This applies to review fixes as well as initial work.

Nearby work is not automatically part of this card. A security/compliance programme, future
architecture or other initiative found in context applies only where its requirements actually
govern this component and change. Establish that applicability from the agreed scope or governing
guidance; if it is unclear and would materially change the work, ask. Do not turn background
reading into a new requirement, or ignore an existing requirement that does apply.
