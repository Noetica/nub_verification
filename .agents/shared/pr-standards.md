# PR Standards — Shared Resource

This file is included by `create-pr`. It is a supporting resource, not a skill: it is never discoverable or invocable on its own.

Canonical home: `nub_specs/DevOps/pr-shepherd/10-pr-standards.md` (§ PR Title Quality, § Release Note Classification). **Rules change there first**, then are mirrored here — this file is the shared copy synced into every downstream `nub_*` repo so `create-pr` never depends on a `nub_specs` checkout. A retained lockstep test (`scripts/inventory_lockstep/tests/test_pr_standards.py`, hub-only) keeps the PR template's allowed tier/type values aligned with the tables below.

## Approved title prefixes

Every accepted title segment is one row. A non-empty **Alias of** cell marks the row as an alias — allowed only where the alias is already established and unambiguous to the intended audience; prefer the full name by default.

| Title prefix | Alias of | Notes |
|---|---|---|
| `AMD` | | Accepted canonical acronym for Answer Machine Detection — short, industry-familiar, already used in existing work. |
| `Agent API` | | Use for the agent-focused API surface. |
| `Campaign Manager` | | Preferred management surface name for campaign configuration, imports, and queue operations. |
| `Customer API` | | Use for runtime customer lookup or screen-pop changes. |
| `Dashboard` | | Use for the dashboard web app or dashboard-level UX changes. |
| `Dashboard API` | | Use when the backend/read-model/API slice is the main scope. |
| `Data Explorer` | | Use for the data-exploration web app. |
| `Developer Docs` | | Use for the public API documentation portal at docs.noeticacloud.com, including the Swagger definitions it publishes. |
| `DNC API` | | Use when the backend Do Not Call API slice is the real scope rather than the UI. |
| `DNC Manager` | | Preferred name for the Do Not Call list management web app. |
| `Entity Designer` | | Use for the CRM entity design web app. |
| `Event Logger` | | Use for event-logging service and API changes. |
| `Get Filter SQL Service` | | Use for the filter-SQL RPC service (repo `nub_svc_getfiltersqlservice`); distinct from `SQI Service Engine`, the parent service it was carved out of. |
| `Housekeeper Service` | | Use for the nightly database-housekeeping service (repo `nub_svc_housekeeper`); the `Service` suffix distinguishes it from the `utils_housekeeping` repo. |
| `Live Monitor Service` | | Use for live state and KPI publication changes. |
| `Noetica Voice Platform` | | Preferred full name for the telephony platform. |
| `NVP` | `Noetica Voice Platform` | Accepted alias where brevity is helpful and the audience will recognise it. |
| `Outbound Messaging` | | Use for the outbound SMS/email messaging surface — the delivery-status webhook service (repo `nub_svc_obmessagehook`) and the message sender service (repo `nub_svc_obmessage`). |
| `Predictive Dialler` | | Preferred full name for dialler changes. Do not shorten this to `PD` in PR titles. |
| `Queue API` | | Accepted stable service name for queue-facing API changes. |
| `Recycling` | | Use for retry, recycle, or reschedule behaviour changes. |
| `Report Manager` | | Preferred name for the reporting web app. Use `Reports API` when the backend reporting slice is the real scope. |
| `Reports API` | | Use for reporting API changes — the backend slice. Use `Report Manager` for the reporting web app. |
| `Skill API` | | Use for skill-domain API changes. |
| `SQI Editor` | | Use for the SQI job definition editor web app. |
| `SQI Service Engine` | | Use for the SQI job execution backend. |
| `Synthesys` | | Use for cross-cutting platform changes that do not sit cleanly under a narrower surface. |
| `Team API` | | Use for team-domain API changes. |
| `Telephony SDK API` | | Preferred runtime integration/API surface name. Do not shorten this to `TSDK` in PR titles. |
| `User Management` | | Preferred management surface name for user/workforce administration changes. |
| `User Management API` | | Use when the backend API slice is the real scope rather than the UI. |
| `Workspace API` | | Use for workspace or environment configuration API changes. |

### Prefix selection rules

- Prefer the approved full name by default.
- Use an alias row only where it is already established and unambiguous to the intended audience (see the **Alias of** column).
- Do not invent new abbreviations for PR titles (`PD`, `CM`, `UM`, `TSDK`, and similar must not appear unless they are later promoted into the table above).
- If a change spans two well-understood areas, `Primary Area / Secondary Area: description` is acceptable — every segment must be in the table (e.g. `Noetica Voice Platform / AMD: improve beep detection thresholding`).
- When the work has a Jira card, the title carries its key — ahead of the component (`ENG-224 User Management: scope agents to a tenant`) or in a trailing parenthesis (`User Management: scope agents to a tenant (ENG-224)`); work with no card needs none. The key must never be the only meaningful content.

## Release note tiers

Choose **one** tier: the most specific audience that needs the note. Publishing rules can fan wider-audience notes out to internal readers, so do not combine tiers in the PR.

| Tier | Audience |
|---|---|
| `Development` | Development and verification team — development/change-control awareness only (dependency updates, internal refactors, test harness or tooling changes). |
| `Tech Support` | Technical support team — changes support need for diagnosis, troubleshooting, or support workflows. |
| `Noetica` | Broader internal Noetica audience, including client services and product/delivery — internal business awareness where the change is not directly customer-facing. |
| `Partner` | API, integration, or partner consumers — integration-facing changes not directly visible to end customers. |
| `Customer` | End users and customer-facing teams — customer-visible behaviour, features, important fixes, breaking changes, deprecations. |
| `None` | No release-note document is expected. `Type` must then be `N/A`. |

## Release note types

Choose **one** type.

| Type | Meaning |
|---|---|
| `Added` | New feature or capability. |
| `Changed` | Existing feature or behaviour works differently. |
| `Fixed` | Bug fix. |
| `Removed` | Existing feature, option, endpoint, or behaviour removed. |
| `Deprecated` | Existing feature remains available but should no longer be used. |
| `Security` | Security-relevant fix or hardening. |
| `Housekeeping` | Routine maintenance with no intended product behaviour change. |
| `N/A` | Only with `Tier: None`. |

