# .claude/commands/test.md

Test the card the user names. Reads the card's **How to verify** section from Jira,
finds the journeys and feature maps it touches in `nub_verification`, runs Doctor,
drives the checks, and writes a result page at `results/<run-id>/`.

Usage: `/test ENG-645`

The result page states pass, fail, blocked, or not-run for each check; includes
deployed build identities, a run ID, and links to evidence (traces, videos,
screenshots, database rows, workbook). The agent posts a Jira comment with the
proposed verdict — a human decides and moves the card.

The agent never edits product code while verifying, never changes an expected value
to make a result pass, and never transitions the Jira card.
