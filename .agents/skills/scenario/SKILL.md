---
name: scenario
description: Select a user's named card or plain-language scenario, follow existing maps and journeys, and return visible per-check results and evidence.
---

# Scenario verification

Read `AGENTS.md` before driving. This workflow is a PoC; it is not yet evidenced as a
complete handover to Sandra and Kim. The environment sequence is Contoso development
checks first, then Fabrikam for final evidence and verification.

## Card mode

1. Fetch the card key supplied by the user or `$ARGUMENTS`; ENG-645 is an example,
   never a hardcoded replacement for the requested card. Use the connected Jira tool.
2. Read its How to verify instructions and linked spec. Find the named journeys and
   feature maps. Missing instructions or maps are blocked prerequisites; do not invent
   acceptance criteria or silently reduce the required checks.
3. Establish the target builds, environment, approved synthetic fixtures and expected
   values. Run readiness checks. A nonzero Doctor exit or unverified prerequisite stops
   driving and becomes a BLOCKED result.
4. Select existing harness operations. Reuse Report Manager's product-owned Playwright
   harness and Sarah's supported read-only checks. Do not assume her removed website
   write tests exist. Setup uses approved product UI/API operations, never database writes.
5. Run only supported legs. The four J1 read tools are not implemented yet. Do not invent
   SQL or report their checks as passed. New TEFT outcomes and unattended agent operation
   belong to ENG-823/ENG-826; mark dependent checks BLOCKED or NOT RUN.
6. Produce `results/<run-id>/result.md` and `result.json` using `results/README.md`.
   Check that evidence links resolve. Keep videos and traces for successful and failed
   browser steps, exact builds, UTC time, tool/journey versions and cleanup outcome.
7. Propose a verdict. Humans decide and move the card. Post a Jira comment only when
   authorized by the current verification request; otherwise return the proposed text.

## Plain-language scenario mode

Find a matching existing journey. If none exists, draft one using the six-heading
template for human review, state proposed expected outcomes and wait for agreement
before treating a run as verification. A tool or product failure stays visible; never
rewrite an expected value to obtain a pass. Offer deterministic automation only after
a clean, repeatable journey and the human's explicit yes.

## Invocation

Ask the agent `Test ENG-645 please` or run `/test ENG-645` in Claude Code. Use the
connectors and permissions already available in that session; do not narrow the tool
allow-list so the required Jira connector becomes unavailable. The Claude command and
skill adapter both load this file as their single instruction source.
