# CLAUDE.md

@AGENTS.md

@SHARED-AGENT-GUIDANCE.md

## What the two imports are

`SHARED-AGENT-GUIDANCE.md` is the single home for the guidance every agent shares — product and
cross-repo orientation, the card-to-merge golden path, YAGNI and shared-package reuse, the
comment-promises-behaviour rule, tool use, and the Jira conventions — written for Codex, Claude Code, Copilot
and Cursor alike. It is imported above so a fresh session *holds* those rules rather than being told
to go and read them. `AGENTS.md` carries this repository's own conventions. Where the two disagree,
`AGENTS.md` wins.

## Claude Code specifics

- Workflows are skills. The canonical bodies live in `.agents/skills/<name>/SKILL.md`; the files
  under `.claude/skills/` are thin adapters that forward to them and hold no workflow prose of
  their own. Edit the canonical body, never the adapter.
- `.claude/settings.json` carries this project's shared Claude Code settings: `additionalDirectories`
  for sibling `nub_specs` / `nub_documents` access and a safe permission allowlist. Personal overrides
  belong in a gitignored `settings.local.json` beside it, which is why no such file is checked in.
