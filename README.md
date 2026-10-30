# nub_verification

The verification team's repository for maps, journeys, and the tools that drive them.
Owned by the verification team. Maps and journeys are written in plain words; agents
keep them honest, humans keep the verdict.

## Directory structure

```
AGENTS.md                           # The verification skill: Connect, Doctor, Drive, Evidence, Cleanup
.claude/
  skills/
    scenario/SKILL.md               # "Test ENG-nnn please, Claude" — the entry point
    verify-reportmanager/SKILL.md   # Report Manager verification skill (product-specific)
maps/
  report-manager/
    README.md                       # Feature map index + conventions
    daily-outbound-interval.md      # One file per feature
    outbound-outcome.md
    ...                             # (12 reports)
  campaign-manager/                 # (future)
  user-management/                  # (future — Angular upgrade target)
journeys/
  campaign-lifecycle.md             # J1: the first journey
  mini-journey-teft.md              # J2: Queue API records, one simulated agent, TEFT (ENG-826)
  ...                               # (J3-J9 to follow)
tools/
  doctor/                           # Is-Fabrikam-worth-testing checks
  db/                               # Named read-only query scripts
  report/                           # Report workbook parser
results/
  README.md                         # The run result format
environments/
  fabrikam.md                       # URLs, tenant, reserved resources, credential sources
CODEOWNERS                        # Kim and Sandra for maps/ and journeys/
```

## How to use

1. **Run a card:** `claude -p "Test ENG-645 please, Claude"` — the scenario skill reads
   the card's How to verify, finds the journeys and feature maps it names, and runs them.
2. **Browse the maps:** open `maps/<product>/README.md` and pick a feature file.
3. **Scheduled maintenance:** a cron job drives every feature and flags drift (see
   `tools/doctor/` for the readiness check).

## Rules

- Non-production tenants and synthetic data only. No secrets in any repo.
- Expected values are written before the run, from product rules, never from the system.
- One deliberately failing case per journey.
- Agents never edit product code, never change expected values to make a result pass,
  and never move a Jira card as a verification verdict (into or out of Verification, or to
  Done). Humans keep the verdict. The development skills' moves to In Progress and Peer
  Review are allowed.

## Related

- [Whole-Journey Verification](https://claude.ai/artifact/AWFz8bnLQbqUELvjUfTBP6) — the vision
- [nub_specs/verification](https://github.com/Noetica/nub_specs/tree/main/verification) — the plan
- [pstack: create-verification-skill](https://github.com/cursor/plugins/tree/main/pstack/skills/create-verification-skill) — the skill format
- ENG-550: the overall shape · ENG-645: the Report Manager pilot
