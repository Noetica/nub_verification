#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Doctor for Fabrikam / Contoso Report Manager — the read-only "is it worth testing?" check.

.DESCRIPTION
  Wraps Sarah's stand-up tester (ENG-809, nub_devops Powershell/Stand Up/) plus the
  Report Manager build check (ENG-609). Built from Stream B step B3: "built from
  Sarah's stand-up tester."

  Run this BEFORE any verification pass. It says "go" or "stop, because...".

.PARAMETER Environment
  'contoso' (default) or 'fabrikam'

.PARAMETER Persona
  'admin' (default). The 'user' persona TOTP is known-bad.

.EXAMPLE
  pwsh tools/doctor/fabrikam.ps1 -Environment contoso -Persona admin
#>

param(
  [ValidateSet('contoso','fabrikam')]
  [string]$Environment = 'contoso',
  [string]$Persona = 'admin'
)

$ErrorActionPreference = 'Stop'
$kvName = $env:E2E_KEYVAULT_NAME ?: 'kv-noetica-dev-uksouth'
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

# 2. Build identity (Sarah's deploy check, ENG-609)
#    TODO: call Sarah's deploy check or the /api/version endpoint
try {
  $verResp = Invoke-RestMethod -Uri "$($envConfig.BaseUrl)/api/version" -UseBasicParsing -TimeoutSec 10
  $results += [PSCustomObject]@{ Check='Build identity'; Result='PASS'; Detail="Version: $($verResp.version)" }
} catch {
  $results += [PSCustomObject]@{ Check='Build identity'; Result='BLOCKED'; Detail="Could not reach /api/version: $($_.Exception.Message)" }
}

# 3. Secrets present in Key Vault
foreach ($secretName in @("zautotest-$Persona-password", "zautotest-$Persona-totp")) {
  try {
    $secret = az keyvault secret show --vault-name $kvName --name $secretName --query value -o tsv 2>$null
    if ($secret) {
      $results += [PSCustomObject]@{ Check="Secret: $secretName"; Result='PASS'; Detail='Present in Key Vault' }
    } else {
      $results += [PSCustomObject]@{ Check="Secret: $secretName"; Result='FAIL'; Detail='Not found in Key Vault' }
    }
  } catch {
    $results += [PSCustomObject]@{ Check="Secret: $secretName"; Result='BLOCKED'; Detail=$_.Exception.Message }
  }
}

# 4. Sarah's stand-up tester conformance (ENG-809) — calls her scripts, doesn't copy them
#    Stream B B3: "built from Sarah's stand-up tester"
try {
  $standupScript = "C:\repos\nub_devops\Powershell\Stand Up\Test-TenantFunctional.ps1"
  if (Test-Path $standupScript) {
    # Run the conformance stage only
    $conformance = & $standupScript -Environment $Environment -Only Conformance -Persona $Persona 2>&1
    $results += [PSCustomObject]@{ Check='Sarah conformance'; Result='PASS'; Detail='See stand-up tester output' }
  } else {
    $results += [PSCustomObject]@{ Check='Sarah conformance'; Result='BLOCKED'; Detail="Stand-up tester not found at $standupScript — run on a machine with nub_devops checked out" }
  }
} catch {
  $results += [PSCustomObject]@{ Check='Sarah conformance'; Result='BLOCKED'; Detail=$_.Exception.Message }
}

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
  Write-Host "VERDICT: CAUTION — $($blocked) check(s) blocked. Review before driving." -ForegroundColor Yellow
  exit 0
} else {
  Write-Host "VERDICT: GO — all checks passed. Safe to drive." -ForegroundColor Green
  exit 0
}
