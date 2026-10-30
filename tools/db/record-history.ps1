<#
.SYNOPSIS
    Read-only: a queued record's current state and its call history (ENG-826, J2).

.DESCRIPTION
    Prints `-- record-history`, then CSV: the record's row in Phoenix_Queue (state, times called,
    retry time), then its Phoenix_Statistics rows, oldest first. Both are SELECTs; nothing is written.
    Phoenix_Statistics.QueueID -> Phoenix_Queue.ID is name_inferred in
    nub_documents/database/schema-reference.md, so confirm a row's Telephone matches before relying on it.

.PARAMETER ConnectionString
    A read-only connection string for the tenant's database, read from Key Vault at run time.
    Never put it in a file.

.PARAMETER QueueId
    One or more Phoenix_Queue IDs: the IDs the Queue API returned when the records were queued.

.EXAMPLE
    pwsh tools/db/record-history.ps1 -ConnectionString $cs -QueueId 1201,1202
#>
param(
    [Parameter(Mandatory)] [string] $ConnectionString,
    [Parameter(Mandatory)] [int[]] $QueueId
)

$ErrorActionPreference = 'Stop'

# The IDs are ints, so joining them cannot inject SQL.
$ids = ($QueueId | ForEach-Object { [int]$_ }) -join ','

$query = @"
SELECT 'queue' AS Source, q.ID AS QueueID, q.OBCampaign_ID, q.State, q.Times_Called, q.Retry_Time,
       NULL AS EventTime, NULL AS Result, NULL AS Duration, q.Telephone
FROM dbo.Phoenix_Queue q
WHERE q.ID IN ($ids)
UNION ALL
SELECT 'statistics', s.QueueID, s.OBCampaign_ID, NULL, NULL, NULL,
       s.EventTime, s.Result, s.Duration, s.Telephone
FROM dbo.Phoenix_Statistics s
WHERE s.QueueID IN ($ids)
ORDER BY QueueID, Source, EventTime;
"@

Write-Output '-- record-history'
Invoke-Sqlcmd -ConnectionString $ConnectionString -Query $query -ApplicationIntent ReadOnly |
    ConvertTo-Csv -NoTypeInformation
