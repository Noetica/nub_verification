<!--
Synced from nub_model_repository — which is where this file is edited. It is
overwritten in every downstream repo on every sync run, so an edit made
downstream is silently lost at the next run: repo-specific guidance for coding
agents (Copilot included) belongs in that repo's own AGENTS.md, which the sync
seeds when missing and never overwrites.

The AGENTS.md pointer below is load-bearing, not a courtesy — do not remove it.
Several Copilot surfaces read THIS file but not AGENTS.md: Copilot Chat in
Visual Studio, in JetBrains and on GitHub.com, plus Copilot code review on a
number of clients. Deliberately not enumerated here — GitHub's support matrix is
the authority and it changes as support ships:
docs.github.com/en/copilot/reference/custom-instructions-support
On those surfaces this file is the only channel that reaches Copilot at all, so
without the pointer every repo-specific convention in AGENTS.md is invisible
there — and Visual Studio is the surface most likely in daily use on the legacy
.NET Framework estate.
-->

Read and apply the shared engineering guidance in the /SHARED-AGENT-GUIDANCE.md file at the
repository root. It is the single home for the guidance every agent shares, including the
card-to-merge golden path and the shared workflows, which are available as skills.

Also apply the repo-specific conventions, gotchas and entry points recorded in the /AGENTS.md file at the repository root.

When performing a code review, follow the /.github/copilot-codereview.md file.
