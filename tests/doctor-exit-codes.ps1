# Offline regression checks: no tenant, Azure or network calls are made.
$ErrorActionPreference = 'Stop'
$doctor = (Resolve-Path (Join-Path $PSScriptRoot '../tools/doctor/fabrikam.ps1')).Path
$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($doctor, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw "Doctor parse errors: $($parseErrors.Message -join '; ')" }

$cases = @(
    @{ Name='Blocked prerequisites stop driving'; Web='[pscustomobject]@{StatusCode=200}'; Secret="'mock-secret-id'"; AzExit=0; Expected=2 },
    @{ Name='Unreachable environment fails'; Web="throw 'mock unreachable'"; Secret="'mock-secret-id'"; AzExit=0; Expected=1 },
    @{ Name='Missing secrets fail'; Web='[pscustomobject]@{StatusCode=200}'; Secret="'ERROR: (SecretNotFound) Secret not found'"; AzExit=3; Expected=1 },
    @{ Name='Azure CLI permission errors block'; Web='[pscustomobject]@{StatusCode=200}'; Secret="'ERROR: Forbidden'"; AzExit=3; Expected=2 },
    @{ Name='Azure CLI vault errors block'; Web='[pscustomobject]@{StatusCode=200}'; Secret="'ERROR: (VaultNotFound) Vault not found'"; AzExit=3; Expected=2 }
)
$shellPath = (Get-Process -Id $PID).Path
foreach ($case in $cases) {
    $child = @'
function Invoke-WebRequest {
    param($Uri, [switch]$UseBasicParsing, $TimeoutSec)
    __WEB__
}
function az { $global:LASTEXITCODE = __AZ_EXIT__; __SECRET__ }
& '__DOCTOR__' -Environment contoso -Persona admin
exit $LASTEXITCODE
'@
    $child = $child.Replace('__WEB__', $case.Web).Replace('__SECRET__', $case.Secret)
    $child = $child.Replace('__AZ_EXIT__', [string]$case.AzExit)
    $child = $child.Replace('__DOCTOR__', $doctor.Replace("'", "''"))
    $output = & $shellPath -NoProfile -NonInteractive -Command $child 2>&1 | Out-String
    $actual = $LASTEXITCODE
    if ($actual -ne $case.Expected -or $output -notmatch 'VERDICT: STOP' -or $output -match 'VERDICT: GO') {
        throw "$($case.Name): expected exit $($case.Expected) and STOP, got $actual.`n$output"
    }
    Write-Output "PASS: $($case.Name) (exit $actual)"
}
