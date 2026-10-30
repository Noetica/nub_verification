# Spec question formats

Conditional input methods for `spec-grill` question rounds. The skill owns question selection
and checkpoint persistence; apply the relevant section below.

## Written answers

**Written answers are another input method.** If the user prefers a larger set or asynchronous
answers, present the currently independent questions together with labelled answer spaces in chat,
the spec's Open Questions section, or a temporary worksheet linking back to those IDs. Say which
questions are deferred and why. Follow [Visual decisions](#visual-decisions) below when a picture
or interaction would help.
Do not require a new UI or copy the spec into a second maintained document. Wait for
the user to submit the answers; do not poll a file while they are filling it in.

On submission, re-read any user-edited file and the affected spec sections. Treat written answers
as input to the same contradiction and dependency checks as chat, not as automatic resolution.
Accept clear answers, leave blanks and ambiguous or conflicting answers open, and ask targeted
follow-ups. If an answer changes a prerequisite, revalidate affected answers from the same round
before adopting them. Recommendations are not selected unless the user explicitly accepts them.

## Visual decisions

Use a visual when seeing the alternatives or trying an interaction helps answer a particular
question: layouts, state transitions, ownership boundaries or competing flows. A UI-related topic
alone is not a reason to make a mockup.

- **Frame the decision.** Show the Open Question ID, what the visual should help decide, and a
  revision label. Use comparable alternatives with stable option labels, visible assumptions and
  the meaningful differences highlighted. Keep fidelity proportionate to the question; label
  proposed behaviour as a proposal, not evidence of an implemented system.
- **Use the available surface.** Prefer the client's existing visual facilities. A standalone local
  HTML page is a fallback when it can be opened; do not require a new server or plugin. Provide a
  short text explanation and an accessible way to answer in chat. If the visual cannot be shown,
  use a textual comparison or leave the question open when the missing visual is essential.
- **Read deliberate feedback.** Exploratory clicks are provisional. Use an explicitly submitted
  choice or the user's chat answer; a clear chat correction takes precedence. Use captured browser
  feedback only when the client actually exposes it, and associate it with the displayed question
  and revision. Ask a targeted follow-up if the intended choice remains ambiguous.
- **Keep the display current.** Update or retire a visual when the question or its assumptions
  change. Revalidate a previous selection if its option's meaning changes; never apply an old click
  to a new revision merely because the option label is unchanged.
- **Persist the meaning.** At the round's checkpoint, record the accepted behaviour and rationale
  in the spec, under the existing resolution rules. Link a retained visual when it adds useful
  detail, preserving that revision in a durable location with the spec. Essential requirements
  must remain understandable without a temporary browser session or an unrecorded click history.
