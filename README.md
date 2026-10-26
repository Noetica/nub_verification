# nub_verification

The verification team's home for plain-language feature maps, journeys and evidence.
Sandra and Kim describe a check; an agent selects existing tools and reports what it
could prove. Humans decide the verdict and move the Jira card.

## Current state

The PoC scaffold and a preliminary Contoso run exist. The campaign journey, readiness
integration and database tools are unfinished. No accepted Fabrikam run is recorded.
Tests run on Contoso first; Fabrikam supplies final implementation evidence and verification.

- Open [the consolidated progress report](progress-summary.html) in a browser for status by plan point.
- Read [DECISIONS.md](DECISIONS.md) for settled scope and [HANDOVER.md](HANDOVER.md) to resume work.
- [consolidation-status.json](consolidation-status.json) is the report's dated, machine-readable snapshot.
- The canonical agreement is the ENG-824 spec and grill record in `nub_specs`; the handover pins their revision.

## Use the existing PoC

Ask the agent `Test ENG-645 please` or use Claude Code's `/test ENG-645` command.
The shared scenario instructions live in [.agents/skills/scenario/SKILL.md](.agents/skills/scenario/SKILL.md);
the Claude skill and command both point there. This is a drafted workflow, not yet an
evidenced end-to-end handover to Sandra and Kim.

Read [AGENTS.md](AGENTS.md) first. A failed or blocked readiness check stops driving.
Missing data, tools, expected values or build identities must remain visible in the result.

## Contents

| Path | What exists |
| --- | --- |
| `maps/report-manager/` | One detailed report map with preliminary View evidence; eleven draft stubs |
| `journeys/` | Shared template and J1 campaign lifecycle draft for Kim/Sandra |
| `environments/fabrikam.md` | Environment and credential sources; reserved resources pending Kim |
| `tools/doctor/fabrikam.ps1` | Incomplete readiness check; blocked checks return a nonzero exit code |
| `tools/db/README.md` | Four agreed query interfaces; scripts and verified mappings still TODO |
| `results/` | Result format and preserved Contoso baseline, with a reconciliation audit note |
| `.agents/skills/scenario/` | Shared scenario instructions; Claude adapter under `.claude/` |

No scheduled maintenance is configured by this repository. The maintenance skill is
future guidance, outside the current PoC implementation.

## Boundaries

Use non-production tenants and synthetic data. Resolve secrets at runtime; keep them
out of prompts and commits. Use read-only database tools. Change expected values only
with human agreement. During verification, report product failures rather than editing
product code. Keep the evidence after cleanup.

ENG-824 owns this home, the first map/journey, the scenario entry point and four minimum
J1 database reads. ENG-645 owns Report Manager suite activation/expansion; PR #267 is
open. ENG-823/ENG-826 own new TEFT capabilities. GrokBot, the Angular upgrade, test
isolation refactoring, database writes and unattended schedules are outside this work.
