#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Doctor for Fabrikam / Contoso Report Manager — the read-only "is it worth testing?" check.

.DESCRIPTION
  Draft readiness check for Stream B B3. Sarah's stand-up integration and exact
  build comparison are pending. Blocked prerequisites return exit 2, not GO.

  Run this BEFORE any verification pass. It says "go" or "stop, because...".

.PARAMETER Environment
  'contoso' (default) or 'fabrikam'

.PARAMETER Persona
  'admin' (default), as used by the recorded Contoso baseline.

.EXAMPLE
  pwsh tools/doctor/fabrikam.ps1 -Environment contoso -Persona admin
#>

param(
  [ValidateSet('contoso','fabrikam')]
  [string]$Environment = 'contoso',
  [string]$Persona = 'admin'
)

$ErrorActionPreference = 'Stop'
$kvName = if ([string]::IsNullOrWhiteSpace($env:E2E_KEYVAULT_NAME)) {
  'kv-noetica-dev-uksouth'
} else {
  $env:E2E_KEYVAULT_NAME
}
$results = @()

# 1. Environment reachable
$envConfig = @{
  'contoso' = @{ BaseUrl='https://contoso.dev.noeticacloud.com/ReportManager'; LoginUrl='https://contoso.dev.noeticacloud.com/ReportManager/?path=entra' }
  'fabrikam'  = @{ BaseUrl='https://fabrikam.uat.noeticacloud.com/ReportManager';  LoginUrl='https://fabrikam.uat.noeticacloud.com/ReportManager/?path=entra' }
}[$Environment]

try {
  $resp = Invoke-WebRequest -Uri $envConfig.BaseUrl -UseBasicParsing -TimeoutSec 15
  $results += [PSCustomObject]@{ Check='Environment reachable'; Result='PASS'; Detail="HTTP $($resp.StatusCode)" }
} catch {
  $results += [PSCustomObject]@{ Check='Environment reachable'; Result='FAIL'; Detail=$_.Exception.Message }
}

# 2. Build identity is not integrated. A reachable page or guessed version URL is
#    insufficient: compare the exact website/API builds with the card before driving.
$results += [PSCustomObject]@{ Check='Build identity'; Result='BLOCKED'; Detail='Verified deployed-build source and expected-build comparison are not integrated' }

# 3. Secrets present in Key Vault
foreach ($secretName in @("zautotest-$Persona-password", "zautotest-$Persona-totp")) {
  try {
    $secretResult = az keyvault secret show --vault-name $kvName --name $secretName --query id -o tsv 2>&1
    $azExitCode = $LASTEXITCODE
    $azError = ($secretResult | ForEach-Object { $_.ToString() }) -join ' '

    if ($azExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace(($secretResult -join ''))) {
      $results += [PSCustomObject]@{ Check="Secret: $secretName"; Result='PASS'; Detail='Present in Key Vault' }
    } elseif ($azError -match '(?i)(SecretNotFound|secret.{0,40}not found)') {
      $results += [PSCustomObject]@{ Check="Secret: $secretName"; Result='FAIL'; Detail='Not found in Key Vault' }
    } else {
      $results += [PSCustomObject]@{ Check="Secret: $secretName"; Result='BLOCKED'; Detail='Azure CLI could not verify the Key Vault secret; check identity, permissions and connectivity' }
    }
  } catch {
    $results += [PSCustomObject]@{ Check="Secret: $secretName"; Result='BLOCKED'; Detail='Azure CLI could not verify the Key Vault secret; check identity, permissions and connectivity' }
  }
}

# 4. Integration is pending. The current Test-TenantFunctional.ps1 uses -SettingsFile
#    and supported -Only steps; it has no -Environment, -Persona or Conformance step.
#    Do not report PASS based on a script existing or ignoring its result.
$results += [PSCustomObject]@{ Check='Sarah stand-up integration'; Result='BLOCKED'; Detail='Supported settings/step invocation and result interpretation are not integrated; see HANDOVER.md' }

# 5. Reserved resources (Kim names these; check they exist)
#    Stream B B3: "the reserved campaign and agents exist, and the runner answers"
$results += [PSCustomObject]@{ Check='Reserved resources'; Result='BLOCKED'; Detail='Pending Kim naming the reserved Fabrikam campaigns, agents, and numbers at kickoff' }

# Summary
$failed = ($results | Where-Object Result -eq 'FAIL').Count
$blocked = ($results | Where-Object Result -eq 'BLOCKED').Count

Write-Host ""
Write-Host "=== Doctor: $Environment ($Persona) ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize

if ($failed -gt 0) {
  Write-Host "VERDICT: STOP — $($failed) check(s) failed. Do not drive." -ForegroundColor Red
  exit 1
} elseif ($blocked -gt 0) {
  Write-Host "VERDICT: STOP — $($blocked) prerequisite(s) blocked. Do not drive." -ForegroundColor Yellow
  exit 2
} else {
  Write-Host "VERDICT: GO — all checks passed. Safe to drive." -ForegroundColor Green
  exit 0
}
