# Database read tools

Named read-only queries for the verification journeys. Each returns the rows
and their IDs. Reads only — no inserts, updates, deletes, or execute (except
parameterised stored-procedure reads). Written against
`nub_documents/database/schema-reference.md` and respecting its
relationship-confidence labels.

## Scripts

### `campaign-records.ps1`
Returns the records in a given campaign list, with their intended outcomes.

```pwsh
<parameter>-CampaignId</parameter>
```

### `record-history.ps1`
Returns the attempt history for a single record: every call, its outcome code,
and its timestamp.

```pwsh
<parameter>-RecordId</parameter>
```

### `record-final-state.ps1`
Returns the final state of a record (completed, retry-eligible, etc.) and its
recycle decision.

```pwsh
<parameter>-RecordId</parameter>
```

### `outcome-codes.ps1`
Lists the outcome codes the dialler can produce and their human-readable names.

```pwsh
# no parameters
```

## Connection

Uses `FABRIKAM-READONLY-CONNECTION-STRING` from Key Vault at runtime. Never
hardcode the connection string. SQL login: `explorer_ro`
(read-only: data reader only).

```pwsh
$cs = az keyvault secret show --vault-name kv-noetica-dev-uksouth `
  --name FABRIKAM-READONLY-CONNECTION-STRING --query value -o tsv
```

## Schema grounding

| Query | Schema entities (confidence) | Source |
|-------|------------------------------|--------|
| campaign-records | `campaign_lists`, `dial_records` (high) | nub_documents/database/schema-reference.md §4.2 |
| record-history | `call_attempts`, `attempt_history` (high) | same §4.3 |
| record-final-state | `dial_records`, `recycle_rules` (medium) | same §4.4 |
| outcome-codes | `outcome_codes` (high) | same §5.1 |

Write queries as `.ps1` files that wrap `sqlcmd` or `Invoke-Sqlcmd`, so they run
without a .NET project. Each must print one header line (`-- <query-name>`) and
the results as CSV.
