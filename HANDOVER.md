# ENG-824 agent handover

Read `DECISIONS.md`, `consolidation-status.json` and the canonical spec/grill record
before editing. `progress-summary.html` is the human-readable view of that snapshot.
Hermes session `local-b0d496ad7076604228db7bbacda5c75b9d6c95f257bd137a954cf5b0e255ca0d`
has exited; do not resume it as a second writer against the same checkout.

## Source of truth

The spec source revision is stored in `consolidation-status.json` under
`sources.spec.commit`. Use its pinned links, then check whether newer approved
decisions exist. The transcript export stays outside this public repository; use the
decision/grill records for accepted outcomes rather than copying raw session data.

## Repositories and branches

| Repository | Local sibling / branch | Current role |
| --- | --- | --- |
| `nub_verification` | this checkout; `add-answers-artifact` | Consolidated PoC and report; PR #2, not merged |
| `nub_specs` | `../nub_specs`; `main` | Spec, grill record and Stream B plan; direct-to-main docs policy |
| `nub_web_reportmanager` | `../rpm_clone`; `fix/skip-gate-video-trace` | Existing harness changes at PR #267, open |
| `nub_web_usermanagement` | `../um_clone`; `main` | Context only; no upgrade work authorized here |

Do not create a branch or PR in `nub_specs`. Do not merge PR #267 or #2, force-push,
use an admin override, or enable automatic merging as part of resuming this handover.
Continue normal review under each owning repository's golden path.

## Settled; do not ask again

Contoso-first/Fabrikam-final; independent work may proceed while Kim's resources and
expected values are pending; four minimum J1 reads are in scope; existing product
harness and Sarah's supported read-only checks are reused; Angular/isolation/GrokBot
and new TEFT tooling are outside this implementation.

## Resume order

1. Check Git status and current PR state before editing. Preserve unrelated changes.
   Read the model repository's canonical `spec-grill` instructions for spec work.
2. Resolve OQ-3 from actual schema and owning code: identifiers, complete attempt
   history, state/recycle semantics and outcome mapping. The README's candidate
   `Phoenix_*` tables are not an approved query design. Then implement only the four
   parameterized read tools. A matching Contoso read-only connection is also missing.
3. Preserve the verified CODEOWNERS routing. GitHub returned no branch errors after
   push for `KimConstantine`, `sandramaced`, `HeyGirardi` and `Sarah461-sys`;
   no permissions changed. Recheck if account access or ownership rules change.
4. Complete Doctor's exact-build checks and Sarah integration using her current
   `-SettingsFile` / supported `-Only` signature and actual result contract. The current
   skeleton deliberately exits 2 for blockage; script existence is not readiness.
5. Finish spec-grill and obtain final scope approval. Formal `implement ENG-824`
   runs from the owning code repo against a published approved spec; it has not been
   evidenced as started through the golden path. Existing PoC code predates that gate.
6. In ENG-645, review PR #267 and resolve its runner/vault/URL prerequisites. Existing
   preflight failure is evidence of visible missing configuration, not a passing suite
   or proof that video/success traces are retained. Keep its code in the product repo.
7. Run the selected checks on Contoso, with intended builds and explicit per-check
   outcomes; retain evidence for pass/fail and a representative deliberately bad case.
   Preserve the historical baseline, including its failures. Do not fix Data Import
   fixtures or session isolation under ENG-824.
8. Obtain Kim's reserved campaign/list/agent/numbers and agreed J1 values, record her
   agreement/date, and have Sandra review the draft wording. Then perform final
   Fabrikam verification with all required evidence. Unsupported Stream A legs remain
   visible as BLOCKED/NOT RUN rather than silently becoming a complete journey.
9. Request re-review of the consolidated PR under the normal process. The existing
   CHANGES_REQUESTED decision is not waived by this handover. Use `review-code` and
   the owning code repo's PR skills where applicable; no `create-pr` in `nub_specs`.

## Evidence and validation

The historical run is `results/20261026T130500Z-verification-run/`; read `audit.md`
before using its counts or evidence links. Raw TRX files remain in the product
checkout, not this public repo. Never commit credentials, local auth settings,
authenticated browser traces or the raw Hermes transcript to make a handover portable.

The consolidation report lists validation separately from live product verification.
Regenerate it with `python scripts/render-progress.py` after editing its JSON source.
Keep the report's snapshot time honest; a static page does not track GitHub automatically.
