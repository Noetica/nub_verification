# Spec coherence and readability

Read from `spec-grill` step 6. Do this in the current session; a fresh session is optional when
useful, not a prerequisite for approval.

**Before any coherence edits:** if the spec has a real Jira key and its card could not be read,
skip this pass, leave any legacy `OQ-C` untouched, and report the blocker. Do not clear history,
rewrite scope or claim approval without that source. A declared `jira_key: N/A` uses the spec
and settled decisions alone. Independent investigation outside this pass may still continue.

- Read the spec against the card (when it has one) and settled decisions. Resolve contradictions to a stated winner;
  a new choice or an unaccepted material consequence reopens the grill.
- Make the overall change and its consequences understandable near the top. Remove repeated
  framing, N/A boilerplate and implementation prescriptions. Do not shorten by making prose dense.
- Preserve the human's INTENT word for word. Keep required behaviour, constraints and meaningful
  acceptance examples in the spec. Supporting evidence may live in the grill record; it must not
  hide a requirement or a material consequence the human has not reviewed.
- Move resolved-question history to the append-only grill record before removing it from the
  spec. Keep current outcomes at their normative homes. Never remove an unresolved question to
  make the spec appear finished. Existing inline resolved rows may stay when moving them adds no
  value; old approved specs do not require wholesale reformatting.
- A legacy unticked `OQ-C` asks for this pass. Once it is done, record its completion in the log
  and remove or resolve that row. Do not create a new `OQ-C` or demand another session. Other
  unresolved items retain their state.

If the pass reopens a decision, return to `spec-grill` steps 4–5 to settle it. Otherwise continue
to step 7 with the final plain-language read-back.
