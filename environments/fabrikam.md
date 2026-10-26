# Environments

## Fabrikam (UAT)

- **Report Manager URL:** `https://fabrikam.uat.noeticacloud.com/ReportManager`
- **Login URL:** `https://fabrikam.uat.noeticacloud.com/ReportManager/?path=entra`
- **Tenant ID:** (Kim names the reserved one at kickoff)
- **Reserved campaigns, lists, agents:** (Kim names these; recorded here when agreed)

### Credentials (from Key Vault, never in this file)

| Secret name in `kv-noetica-dev-uksouth` | What it is |
|------------------------------------------|------------|
| `zautotest-admin-password` | Admin persona password |
| `zautotest-admin-totp` | Admin TOTP seed |
| `zautotest-user-password` | (Known-bad as of 2026-06 — do not use) |
| `zautotest-user-totp` | (Known-bad as of 2026-06 — do not use) |
| `FABRIKAM-READONLY-CONNECTION-STRING` | Read-only SQL (explorer_ro on sqldb-fabrikam-noetica-qa-uksouth) |

Fetch with:
```pwsh
az login
pwsh scripts/fetch-e2e-secrets.ps1 -Persona admin -KvName kv-noetica-dev-uksouth
```

**VPN required.** The SQL firewall allows only the London and Durham VPNs. The dev
environment URL may also be in-vnet only (check with Sarah).

## Contoso (dev)

- **Report Manager URL:** `https://contoso.dev.noeticacloud.com/ReportManager`
- **Login URL:** `https://contoso.dev.noeticacloud.com/ReportManager/?path=entra`
- **Persona:** admin (same Key Vault secrets)

Contoso is the first target for the PoC. It has the same reports and data structure as
Fabrikam but is the shared dev tenant (lower isolation, acceptable for the pilot).

## Data environments (allow-list for data-driven checks)

The harness gates data-driven report entry on an allow-list of environment hosts
(`E2ESettings.DataEnvironmentHosts`). Currently: `contoso` and `fabrikam`.
Tests skip entirely on any other environment. To add one: add the host to the allow-list
and create `TestData/report-inputs.<env>.json`.
