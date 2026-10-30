# Implementation delivery approval

Read from `implement` step 7a when delivery authority or reviewer-sharing consent is missing, or an exclusion needs the local-only/stop alternatives. The caller keeps the authority and exclusions already established; this resource supplies the dialog and its outcomes.

Before either question, resolve `<providers>` and explain the sharing decision using `review-code`'s **Invocation and scope**.

## Full question

> Do you authorise implementation, testing, independent review and fixes, commits/push, and a draft PR with Jira updates? This includes sending the source and diff, relevant Jira/spec text and test evidence to the configured `<providers>` reviewers. Yes / No.

## Sharing-only question

> Your delivery instruction already covers the rest of the work. Do you also consent to sending the source and diff, relevant Jira/spec text and test evidence to the configured `<providers>` reviewers? Yes / No.

**For either question:** Yes supplies the missing authority and makes the run **PR-authorised**: checkpoint commits (per completed plan section, or after verification for no-plan minor work), push, `review-code`, and `create-pr` with its Jira updates. No uses the alternatives below. No answer grants nothing: wait; never choose an answer or a stopping point from silence.

## Alternatives after No or a conflicting exclusion

Offer local-only or stop, and wait for the developer's choice unless they have already given it. Explain why another combination is outside this automatic flow: `create-pr` requires accepted review evidence; `pre-pr-review` is only the developer's explicit fallback choice, and partial delivery needs their own instructions for its steps. Preserve existing exclusions and authority: commit or push authority the developer gave separately, in this conversation or their own client or user-level configuration, still applies to a local-only run. Neither No nor this menu silently chooses a new scope or undoes completed work.
