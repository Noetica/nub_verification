# J1 database reads

The four read-only tools below are agreed ENG-824 scope (OQ-2). None of the `.ps1`
files exists yet. This page describes the intended observations, not a working query API.

| Planned tool | Required observation | Current state |
| --- | --- | --- |
| `campaign-records.ps1` | Selected synthetic records in the reserved list, with identifiers | TODO: verify campaign/list/queue identifier mapping |
| `record-history.ps1` | Each selected record's attempts, outcomes and timestamps | TODO: verify the complete attempt-history source |
| `record-final-state.ps1` | Current state, retry eligibility and recycling decision | TODO: verify state semantics and joins |
| `outcome-codes.ps1` | Outcome codes and human-readable meanings used by J1 | TODO: verify the canonical code mapping |

## Verified source and remaining research

Use [the canonical schema reference](https://github.com/Noetica/nub_documents/blob/1e467bd733006a18e70cbf9bfae2181f200f080f/database/schema-reference.md),
then confirm semantics in the owning application code and the intended tenant.

The earlier README's `campaign_lists`, `dial_records`, `call_attempts`,
`attempt_history`, `recycle_rules` and `outcome_codes` names are absent from that
reference. Its numbered-section citations and confidence claims did not establish
usable mappings and must not be used to generate SQL.

Verified candidates, not an approved query design:

- `dbo.Phoenix_Queue` contains `ID`, `OBCampaign_ID`, `Customer_ID`, `State`,
  `Times_Called` and `Retry_Time`; the reference gives its relationship to
  `Phoenix_OBCampaigns.ID` as `join_in_view`.
- `dbo.Phoenix_Recycling` contains `QueueID`, `Result`, `TimesCalled`, `NewState`
  and `RetryTime`. Its `QueueID -> Phoenix_Queue.ID` relationship is only
  `name_inferred`; verify it before relying on it. Recycling rows alone are not
  established as a complete record of every call attempt.
- `Phoenix_PDCallResults` is listed in the reference's table inventory, but that
  reference does not give a detailed column block for it. Do not invent its schema.
- Intended outcomes come from the approved fixture plan, not from observed database
  results. Raw state integers need a verified product-code interpretation.

OQ-3 in the spec tracks this technical research. Cite table/column names, key meanings,
join confidence and the owning-code reference here before implementation. Bound each
query to the selected synthetic fixture IDs and parameterize inputs; return the row
identifiers alongside the observed fields. No free-form SQL fallback, writes, or
stored-procedure execution is added to this PoC.

## Connection sources

Fabrikam's approved source is the runtime Key Vault secret
`FABRIKAM-READONLY-CONNECTION-STRING` in `kv-noetica-dev-uksouth`, using `explorer_ro`.
Its SQL firewall requires the London or Durham VPN. Keep the value out of source,
prompts and logs. A Contoso read-only database source has not been established here;
never label a Fabrikam database read as Contoso evidence. Establish the matching
source before a Contoso data check, or report that check BLOCKED.
