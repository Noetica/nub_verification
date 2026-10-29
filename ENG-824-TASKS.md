# ENG-824 completion sequence

Use this list as the ordered work queue. Update each item only when its evidence
exists. The spec and grill remain authoritative for scope and decisions; this list
tracks execution. Keep the approval order from grill G-009: schema research, final
spec approval, then implementation.

## Ordered tasks

1. **Finish the current feedback round for `nub_verification` PR #2.** Complete the
   selected Light local review, commit and push the validated fixes, then reply to and
   resolve only the feedback covered by this round after checking the PR head. Do not
   merge without the required reviews, checks, and explicit human confirmation.
2. **Complete the ENG-824 spec grill.** Preserve the completed schema and owning-code
   research: IDs, joins, attempt-history shape, state/recycle semantics, and outcome
   mapping. Keep Kim's reserved resources and agreed expected values open until confirmed.
   Treat Contoso identity/connection validation as post-deployment work, not a pre-merge
   access prerequisite. Record remaining questions rather than guessing.
3. **Publish the agreed spec and grill record.** Update `nub_specs` directly on `main`
   under its documentation-only policy, obtain and record final scope approval, and
   capture the published revision. Keep the spec status accurate.
4. **Start `/implementation` through the golden path.** Run `implement ENG-824` from
   the owning `nub_verification` repository against the published, approved spec;
   create or resume its implementation plan and preserve the scope boundary.
5. **Complete the ENG-824 implementation.** Build the four agreed parameterized,
   read-only J1 query tools; complete Doctor's exact-build checks and Sarah's supported
   integration; finish the map, J1 journey, plain-English scenario entry point, and
   evidence handling. Keep unsupported Stream A coverage explicitly blocked or not
   run. Do not add new TEFT capabilities or tenant writes.
6. **Complete the ENG-645 Report Manager dependency.** Resolve PR #267's runner,
   vault, and URL prerequisites in the owning product repository and follow its review
   and delivery process. Keep this work separate from ENG-824 code changes.
7. **Validate on Contoso.** Run the selected checks against the intended builds, record
   each agreed outcome, retain video/trace evidence with cleanup, and include a
   representative deliberately failing case. Preserve historical failures honestly.
8. **Run code review and address findings.** Review the implementation against the
   approved spec and repository standards. Use the available `review-code` runner or
   its authorized documented fallback; resolve material findings before proposing the
   implementation PR.
9. **Create and groom the implementation PR.** Open it as a draft through the golden
   path, link ENG-824 and its spec/evidence, run the full required suite, and make the
   resulting review state clear to the human approver.
10. **Complete implementation PR feedback and merge.** Process all human and bot
    feedback, checks, and per-round review requirements. Merge only after required
    approvals and checks pass and the human explicitly confirms the merge at the
    current head; then deploy through the normal process.
11. **Verify finally on Fabrikam.** With Kim's agreed resources and expected values,
    perform the final verification on Fabrikam, retain the required artifacts, and
    record the human verdict. Complete ENG-824 only when its acceptance criteria are
    evidenced.

## Current position

- For Task 1, PR #2 contains the prior feedback fixes and supporting evidence. Use the
  live PR state to decide any further reply or resolution; this handover is not approval
  to merge.
- Tasks 2–11 are pending. Contoso-first and Fabrikam-final, the four read-only tools,
  and the current scope exclusions are settled. Schema/owning-code research is recorded;
  final spec approval and Kim's campaign details remain open. Verify Contoso's deployed
  identity and connection after CI deployment; this is not a pre-merge blocker. The
  documented Fabrikam source is available, with live retrieval/SQL connectivity still
  to be validated in its intended execution context.
