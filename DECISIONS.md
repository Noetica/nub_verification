# ENG-824 consolidated decisions

This is the current decision readout from the Hermes and Codex sessions on 26 Oct
2026. The canonical spec and append-only grill record live in `nub_specs`; see
`HANDOVER.md` for their pinned revision. Historical run results remain historical.

| ID | Settled decision | Source and consequence |
| --- | --- | --- |
| D1 | ENG-824 owns the verification home, first report map/J1 draft, scenario entry point and four minimum J1 reads. | Human selected the scope split; G-001/G-005 record it. ENG-645 owns Report Manager suite activation/expansion; ENG-823/ENG-826 own new TEFT capabilities. |
| D2 | Run tests on Contoso first; final implementation evidence and verification come from Fabrikam. | Explicit user clarification in the Codex session; G-002. Contoso is preliminary. |
| D3 | Kim's reserved resources and agreed expected values gate accepted Fabrikam evidence while independent work continues. | Hermes user reply at 17:34:13 UTC: accepted condition; work through the tasks possible meanwhile. G-006. The confirmation itself has not happened. |
| D4 | Include only the four named read-only J1 query tools. | Hermes user accepted inclusion where required by the committed spec; G-005 resolves OQ-2. Do not ask this scope question again. Scripts are not implemented and actual schema mappings still need verification. |
| D5 | Keep the core PoC focused. | Human excluded GrokBot, the Angular upgrade, test-isolation refactoring, tenant writes and unattended scheduling. Data Import investigation is a possible future use of the harness; changing its data is not current implementation work. |
| D6 | Reuse existing product and stand-up tooling. | No third browser-test pack, duplicate TEFT engine or copied Sarah scripts. Sarah's removed write tests cannot be used for setup; reuse only supported current operations. |
| D7 | Preserve expected outcomes and human verdicts. | Never change expected values to obtain a pass, hide failed/skipped checks or move Jira status during verification. |
| D8 | Consolidate one current status report and one shared scenario body. | This reconciliation replaces competing HTML summaries with `progress-summary.html`, backed by `consolidation-status.json`; both Claude entry points load `.agents/skills/scenario/SKILL.md`. |

## Facts that are not completed deliverables

Report Manager PR #267 is open. Its smoke preflight failed because four repository
variables were missing; that is not a deployed green run. `nub_verification#1` is the
separate merged documentation PR. PR #2 is the current consolidation branch and still
needs reviewer attention. The saved Contoso suite failed overall, and no accepted
Fabrikam run exists.

The old database README's generic tables were not grounded in the canonical schema.
G-007 corrects that claim while preserving the approved query scope. Placeholder
CODEOWNERS identities were rejected by GitHub. The consolidation replaces them with
repository collaborators `KimConstantine`, `sandramaced`, `HeyGirardi` and `Sarah461-sys`,
whose write/admin access was verified through GitHub. No repository permissions were changed.

The grill reached a walkthrough; no final implementation approval is recorded.
The spec remains draft with Kim's prerequisite and technical schema research visible.
