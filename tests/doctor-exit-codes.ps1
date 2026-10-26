# Offline regression checks: no tenant, Azure or network calls are made.
$ErrorActionPreference = 'Stop'
$doctor = (Resolve-Path (Join-Path $PSScriptRoot '../tools/doctor/fabrikam.ps1')).Path
$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($doctor, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw "Doctor parse errors: $($parseErrors.Message -join '; ')" }

$cases = @(
    @{ Name='Blocked prerequisites stop driving'; Web='[pscustomobject]@{StatusCode=200}'; Secret="'mock-value'"; Expected=2 },
    @{ Name='Unreachable environment fails'; Web="throw 'mock unreachable'"; Secret="'mock-value'"; Expected=1 },
    @{ Name='Missing secrets fail'; Web='[pscustomobject]@{StatusCode=200}'; Secret='$null'; Expected=1 }
)
$shellPath = (Get-Process -Id $PID).Path
foreach ($case in $cases) {
    $child = @'
function Invoke-WebRequest {
    param($Uri, [switch]$UseBasicParsing, $TimeoutSec)
    __WEB__
}
function az { __SECRET__ }
& '__DOCTOR__' -Environment contoso -Persona admin
exit $LASTEXITCODE
'@
    $child = $child.Replace('__WEB__', $case.Web).Replace('__SECRET__', $case.Secret)
    $child = $child.Replace('__DOCTOR__', $doctor.Replace("'", "''"))
    $output = & $shellPath -NoProfile -NonInteractive -Command $child 2>&1 | Out-String
    $actual = $LASTEXITCODE
    if ($actual -ne $case.Expected -or $output -notmatch 'VERDICT: STOP' -or $output -match 'VERDICT: GO') {
        throw "$($case.Name): expected exit $($case.Expected) and STOP, got $actual.`n$output"
    }
    Write-Output "PASS: $($case.Name) (exit $actual)"
}
