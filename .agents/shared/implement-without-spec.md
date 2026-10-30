# Implement without a published spec

Read from `implement` step 4 only after a successful lookup returns **not found**. An unavailable source or unresolved local copy does not enter this branch.

Assess the card's scope against the repo (lightest safe workflow: simple bugfix → direct change; minor feature → short plan). If it plausibly needs design decisions, cross-repo changes, or new behaviour with edge cases, recommend `spec-draft <KEY>` and stop. Otherwise announce minor-work mode and continue — don't ask anything here; `implement` steps 5–6 happen before the delivery authorization but commit nothing, push nothing, and open no PR (`implement` step 5 may still create the card branch and update Jira, as it always has), and the single authorization comes at `implement` step 7a, once the scope is stated:

> ⚠ No spec found for `<KEY>`. Proceeding in minor-work mode (`<one-line reason>`) — authorization question follows once I've grounded and stated the steps.

Record nothing — the durable "spec not required" reason is captured in the PR body by `create-pr`.
