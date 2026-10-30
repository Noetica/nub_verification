# Local pre-PR review loop

## Contents

- [Repository use and configuration](#repository-use-and-configuration)
- [Find and resume a saved run](#find-and-resume-a-saved-run)
- [Command flow](#command-flow)
- [Review interruptions and input mutation](#review-interruptions-and-input-mutation)
- [Triage and fix commands](#triage-and-fix-commands)
- [Handoff and PR-head comparison](#handoff-and-pr-head-comparison)
- [Publishing to an open PR](#publishing-to-an-open-pr)
- [Progress, observation and freshness](#progress-observation-and-freshness)
- [Recovery and tests](#recovery-and-tests)
- [Diagnostic handoff](#diagnostic-handoff)
- [Tests](#tests)

Synced to every downstream repository. The authoring session uses the dispatcher skill
and this Python runner to review, verify claims, edit clear in-scope defects of any severity and review again.
The standalone review-triage skill is a separate, fleet-synced human-selection workflow.

The runner launches the installed Claude, Codex and Cursor CLIs as ordinary subprocesses on
macOS and Windows. Each CLI uses its normal cached login and handles credential refresh itself.
There is no runner-owned keychain access, token extraction, authentication proxy or OS sandbox.
Snapshot separation and native review restrictions do not prove
that a reviewer process cannot read other files on the machine.

## Repository use and configuration

Requires Python 3.12+, Git, and the installed CLIs. Log in once using each CLI's normal login flow.
Use the same account/environment as your authoring session; the runner preserves HOME,
USERPROFILE, CODEX_HOME and provider configuration/auth environment variables. Expired credentials
are handled by the CLI, with its usual login flow if refresh fails. The runner does not add its
own credential approval on every run. Normal OS or provider prompts can still occur.

On Windows, resolve prerequisites and cached-login status from the developer's ordinary interactive
PowerShell session. A helper process running under a different sandbox identity can have a different
PATH, Python launcher inventory and credential view; do not install tools or repeat login solely
because that helper reports them missing. Use the ordinary shell to resolve the concrete native
commands, then put only required runtime overrides in the local configuration.

From the caller repository root, use `python scripts/pre-pr-lens-review.py --help` (or
`python3` at 3.12+). From its `scripts` directory, `python -m pre_pr_lens_review --help` is also
supported. All commands below use either prefix. The authoring session creates the JSON inputs.
No hub checkout or personal skill installation is needed. Use the repository dispatcher at
`.agents/skills/review-code/SKILL.md` or the Claude adapter under
`.claude/skills/review-code/`, following `SHARED-AGENT-GUIDANCE.md`.

The developer-facing skill is `review-code`; the script, Python package, personal configuration
and saved-run paths use `pre-pr-lens-review` or `pre_pr_lens_review` as shown below.

**Prerequisites and partial sync.** The checkout needs both skill files, the entry script, all
package Python modules and these package resources: `reviewer.md`, `review.schema.json`,
`diagnostic-handoff.md`, `README.md` and `reviewer-models.json`. Python 3.12+, Git and the three
configured provider commands must be available. Skills and runner files may not have arrived
together. Repair a failed sync first, then wait for the complete sync and pull `main` again.
`create-pr` reports missing
prerequisites and start/preflight/probe failures, then follows its step 2 recovery policy.
Missing, damaged or incompatible saved evidence is recoverable under the existing review
authorisation when fresh inputs are supplied, as described below. Other failures stop: fix the cause and re-run, or explicitly choose
`pre-pr-review`; it never falls back automatically. The loop is unsupported in
cloud dev environments where the local CLIs cannot authenticate.

**Reviewer selection.** `reviewer-models.json` beside this README is the team's committed default,
updated by a reviewed hub PR and propagated by sync. The dispatcher uses a personal override at
`~/.config/noetica/pre-pr-lens-review/reviewer-models.json` when present (on Windows, `~` is the
user's home directory), or a different file explicitly selected by the developer. An unreadable or
invalid override is a configuration failure, not a reason to silently use the team default.
The override has the same shape as the complete team file, including all six roles. Record the
selected absolute file path as `reviewer_config` in intent JSON and pass that file to `start
--config`; its contents are frozen into the run. An existing run keeps its frozen selection.
This selects external reviewers, not the model running the authoring skill.

Supply exactly six roles: sonnet, luna, composer, opus, sol, grok. Each requires a concrete
`model` ID and `effort`. The runner never substitutes a model. Cursor encodes effort in its model
slug; use `effort: "encoded-in-model"` where supported, or `effort: "provider-default"` for models
without configurable effort. The committed file is the source for current IDs; do not infer them
from role names.

Cursor's `cursor-agent models` catalogue is the authority for its CLI selectors.
Before starting a run, confirm that each configured Cursor model is available to the
account used by the configured CLI. The fixture probe exercises Composer; Grok first
runs in pass 2, so that probe alone does not confirm access to the selected Grok model.
Grok 4.7 selectors omit the older `cursor-` prefix.

For example, a Claude role has this shape (replace the model placeholder before use):

```json
{"model": "<selected-sonnet-model-id>", "effort": "high"}
```

Commands default to `claude`, `codex` and `cursor-agent` on PATH. An optional per-role `runtime`
overrides the command, e.g. `{"executable": "C:\\Tools\\claude.exe"}` or
`{"executable": "agent"}` if that is your Cursor installation. Confirm that `agent` is Cursor:
other products also install that command. Node installations can supply `executable: "node"` and
an absolute `entrypoint` path. On Windows use a native executable or node.exe plus entrypoint,
not a `.cmd`/`.bat` shim. Prompts go through stdin or a workspace file, not a shell command string.
Both roles of a provider must select the same command. An optional `version` demands an exact
version token; otherwise preflight records the installed version and resolved command for the run.
If either changes during a run, later reviewer commands fail; see *Keep reviewer CLIs unchanged*
below. No platform-specific installation paths are hard-coded.

A complete role with a runtime override looks like this; both roles of that provider carry the
same `runtime`:

```json
{"model": "<selected-sonnet-model-id>", "effort": "high",
 "runtime": {"executable": "node", "entrypoint": "<absolute path to the CLI's JavaScript entrypoint>"}}
```

To find what to configure on Windows, run `where.exe <command>` and look at what PATH resolves.
Preflight rejects a `.cmd` or `.bat` result. Open that shim to see what it launches: if it runs
`node` with a JavaScript file, configure `node` (or node.exe's absolute path) as `executable` and
that file as `entrypoint`; if it launches an `.exe`, configure the `.exe`. Preflight records the
resolved path with symlinks followed, so a launcher that points into a versioned installation
records that build. A configured path containing a version number pins one build, and stops
resolving when an upgrade removes it; preflight then reports the CLI as not found, the configured
entrypoint as missing, or its version as unreadable.

**Keep reviewer CLIs unchanged for the length of a run.** Every command that launches reviewers
repeats preflight and compares the result with the run's first one. A different version or resolved
command for any configured provider fails the command with `Reviewer command or CLI version changed
since first preflight`, even when that provider has no reviewer left in the schedule. The saved
run is not stopped, so every retry fails the same way until the recorded build is available again.
The runner has no way to accept a new version into an existing run. A run that spans a fix batch
can last long enough for an automatic update to land, so hold updates while it runs: for Claude
Code set `DISABLE_AUTOUPDATER=1` in the environment that launches the runner, and use each other
CLI's own update setting where it has one. If a version has already changed, either make the
recorded build resolvable again, or record a stop with `answer` and begin a new run with `start`
and a new `--state` directory; the new run schedules every pass again.

Installed CLIs must support the adapter flags; an unsupported
flag fails rather than silently falling back. Model selection remains independent of CLI version.

Each invocation gets a fresh copy of the review pack, with no shared Git metadata or prior
reports. Git symlinks become link text, never links into the caller tree. Claude uses restricted
Read/Glob/Grep tools, safe mode and empty MCP configuration. Codex ignores user configuration/rules
and disables additional tools. It uses its native read-only sandbox on every platform. On Windows
that sandbox is a restricted token Codex will not start unless `windows.sandbox` is set, and
ignoring user configuration drops it, so the adapter supplies the mode explicitly; user
configuration stays ignored because Codex otherwise records every disposable pack directory in the
developer's project trust list.
The reviewer works in the disposable pack copy; post-run content-digest validation rejects
a changed copy. This detects changed inputs after execution; it does not prevent writes or prove
that the process cannot read other local files. Removing that copy afterwards is best-effort,
because on Windows an exiting reviewer can still hold its own working directory and a completed
review must not be lost to that; a copy that stays locked is left in the system temporary
directory rather than raising.
Cursor trusts only its newly generated review workspace (`--trust`), uses ask mode and project
permissions denying shell, writes, web fetches and MCP calls. Its normal global login is retained;
there is no claim that all inherited Cursor customisations or MCP startup are disabled.
On Windows the Cursor reviewer starts without `MSYSTEM`, which Git Bash sets: with it set, Cursor
runs each user hook's PowerShell wrapper with bash, every hook fails, and each blocked tool call
leaves the reviewer unable to read the pack. Its CLI offers no switch to disable user hooks.
Cursor uses non-partial `stream-json`: the last complete assistant message after tool activity is
the answer, and a terminal success event from the same session is required. The terminal event's
`result` text concatenates earlier progress and is not used to select the answer. Earlier messages
can quote configuration, invocation metadata or example reports. The final message must contain one
bare JSON document or one JSON fence, optionally surrounded by plain prose. Surrounding prose
must not contain backticks, braces or square brackets, which could introduce competing structured
content. Multiple documents and malformed JSON still fail; the adapter never repairs findings,
unescapes an entire report, or infers missing fields. Schema and invocation-identity validation
still apply to the decoded report. Cursor's stream format structures the transport, not the
model's answer; its CLI does not expose the schema-enforcement flags used for Claude and Codex.
There is no fallback that searches progress text for report-shaped objects. The pack is checked for
mutation on successful and failed execution paths before an operational retry is allowed. These are review restrictions and integrity checks,
not an additional OS isolation guarantee. Never enable permission bypass to make a review run.

The invocation's known run, pass, reviewer and input identity are restricted to their exact values
in the schema supplied to Claude and Codex. The shared pack schema stays unchanged. Cursor receives
the same constraints in its prompt, but its streaming CLI does not enforce an output schema.
Every returned report still undergoes exact identity validation; a mismatched identity is rejected
and retained, never corrected after generation.

### Codex on Windows: setup refresh had errors

**Symptom.** A Codex reviewer (`luna`, `sol`) fails with "codex's Windows sandbox could not start
its commands ('setup refresh had errors')". Its saved CLI response shows each command ending
`Failed to create unified exec process: helper_unknown_error: setup refresh had errors`, and
`~/.codex/.sandbox/sandbox.<date>.log` shows `The process cannot access the file because it is
being used by another process. (os error 32)` against a `node_repl.exe` path.

**What `node_repl.exe` is.** Part of Codex's own computer-use runtime, installed under
`%LOCALAPPDATA%\OpenAI\Codex\runtimes\cua_node\<version>\bin\` beside a bundled `node.exe`.
It is not the Node.js you installed and not part of this repository. An interactive Codex CLI
session was observed starting it as the session opened; other Codex clients may start it too.

**Cause.** Before every command, Codex 0.161 updates its sandbox's permissions on that runtime,
including `node_repl.exe`. While another Codex session is running it, the file is locked, the
update fails, and Codex refuses to start any command. The reviewer then cannot read the review
pack, and Codex still exits zero with a report, so the runner rejects the attempt rather than
accept a review that read nothing. The review pack's location is not the cause.

**Fix.** Close the Codex session that started it (usually an interactive Codex CLI), end any
`node_repl.exe` left in Task Manager, then run again. A Codex app-server from the VS Code
extension was running during successful runs, so closing that was not needed. Do not switch
`windows.sandbox` to `unelevated` to get around this: it cannot read the owner-only pack copy, and
under it the read-only sandbox was observed allowing deletes that `elevated` denies.

Provider references: [Claude cached authentication](https://code.claude.com/docs/en/authentication),
[Cursor authentication](https://cursor.com/docs/cli/reference/authentication), and
[Cursor permissions](https://cursor.com/docs/cli/reference/permissions), and
[Cursor output protocol](https://cursor.com/docs/cli/reference/output-format).

## Find and resume a saved run

Before `run` (or the lower-level `start`), locate this repository's ownership record using the
installed runner. From the caller root, on either platform:

```python
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "scripts"))
from pre_pr_lens_review.cycle import Controller
record = Controller.registry(Path.cwd(), create=False)
print(record)
if record.exists():
    print(json.loads(record.read_text(encoding="utf-8"))["root"])
```

Run `status --state <root>` on the saved directory (or `observe --state <root>` for a read-only look
that takes no lock). A record alone is discovery, never review
acceptance: only a fresh successful `handoff` can authorise the current tree. A restarted session
can resume the current valid active run, keeping its frozen intent/config and all evidence.
A saved JSON record is a discovery pointer, not proof that a process is still running. A live
command lock covers the repository and its worktrees; reviewer lifetime guardians keep recovery
blocked while launched reviewer work remains active, even if the controller exits. Report the
runner's blocking reason and wait for that work to end; do not delete records to bypass it.
An older discovery record containing only `root` is accepted when that saved run is valid;
the next locked command upgrades it with the run ID. An incompatible or damaged old run is
retained as history while fresh inputs select a new one.

With all fresh inputs (`--repo`, `--base`, `--intent`, `--checks`, `--config`), `run` checks
the repository/worktree, target, intent, configuration, checks and source identity before resuming.
Valid compatible evidence retains its frozen configuration,
stable finding IDs, completed passes, decisions and spent attempts. Missing, unreadable, corrupt or incompatible
evidence instead starts a fresh run under the existing review authorisation, preserving old
artifacts. Automatic replacement uses a unique directory under the system temporary directory:
`pre-pr-lens-review-<uid>/<Jira-key-or-unkeyed>/<uuid>` on Unix, or
`pre-pr-lens-review/<Jira-key-or-unkeyed>/<uuid>` on Windows. `--state` is optional; always use
the returned `root` for later commands and observation because recovery may select a different directory.
A state-only invocation can resume valid evidence; if evidence is missing or damaged, supply
fresh inputs rather than asking permission to restart. A historical or superseded ready record
cannot be accepted, and recovery never replaces the fresh `handoff` validation.
For the same tree, a changed check status starts a new run; revised wording in passing
check evidence can resume the saved run, whose original check record remains frozen.

An interrupted author fix returns an author boundary. Inspect the actual current diff and run
appropriate checks on that tree; include a nonempty `inspection` string describing that inspection
and naming the interrupted run's `input` digest shown by `status`
in the fresh checks JSON, alongside `tree`, `status` and `evidence`. Then invoke `run` with all
fresh inputs to review the resulting tree afresh. Never replay uncertain edits or recover a
`finish-fix` token. Ask the human only when inspection exposes a decision that needs them.
Explicit human stops, exhausted reviewer retries and exhausted review capacity remain stops
for compatible work; recovery must not erase those limits. Changed requirements or source
after a stop need fresh inputs and a distinct run.

If the developer explicitly chooses legacy review, stop the run this attempt created or reused
with `answer --state <root> --file <outside-answer.json>`, where the JSON is
`{"kind":"stop","text":"<the developer's actual choice>"}`. Confirm the recorded phase is
`stopped`, retaining the run directory and evidence. This also applies after a session restart,
and permits a later explicitly started loop without an active-run refusal. If stopping fails,
resolve it before proceeding. An upfront legacy choice with no attempt needs no run or preflight.
Record `pre-pr-review` and the declined/unavailable reason in the PR's `Testing` section.

## Command flow

All artifacts live in a fresh directory **outside** the caller repository. The runner preserves
the caller's index and working files. Untracked non-ignored files block capture; the developer must
include them with intent-to-add or ignore them before continuing. A split index and
assume-unchanged flags are supported.

**Leave the repository alone while a runner command is running.** Most commands capture the caller's
state into a private copy: `snapshot`, `start`, `run`, `review`, `finish-fix`, `triage`,
`sensitive`, `begin-fix`, `handoff`, `compare-pr-head`, `answer` other than a stop, exception or
changed requirement, and `status` outside the fixing and stopped phases. If HEAD, the branch, the
index, the intended tree or the set of untracked files changes during that capture, the capture
fails with `Caller changed during snapshot capture`. Where the command rechecks a saved run
(`review`, including the review inside `run`, and `triage`, `sensitive`, `begin-fix`, `status`,
`handoff`, `compare-pr-head` and the rechecking `answer` kinds) that failure stops the run, even
when the content is identical, so a commit, `git add`, checkout, edit or new file made alongside a
running command can cost the whole run. When `run` is resuming with fresh inputs, a failed recheck
instead sets the saved evidence aside and starts a replacement run. `snapshot` and `finish-fix` only
fail and can be repeated once the change settles. Let each command finish and read its result first.
Between commands the run compares only the branch, the merge base with the target and the tree:
committing or pushing unchanged content is safe and preserves the review, while a content edit, a
branch switch, or a rebase or merge that moves the merge base invalidates it.

A submodule (Gitlink) is a commit pointer, not complete source, so a change to one cannot be
reviewed from the pack. Capture compares every Gitlink in the merge base with the intended tree,
which includes staged changes and a different commit checked out inside the submodule. A submodule
the change adds, removes or repoints, or swaps with a regular file, stops capture with each path
and reason named. A missing submodule directory is recorded by Git as a removal and stops too;
an empty directory from an uninitialised submodule does not. A submodule pinned to the same commit
on both sides is outside the change: it is left out of `base/` and `source/`, and listed with its
commit under `submodules` in the snapshot result, `pack.json` and the run summary. Uncommitted
content inside a submodule is never captured, because the caller could not commit it from this
repository either.

1. Fetch the target once, then pin its full commit SHA. Fetch card/comments and linked spec once.
2. `snapshot --repo <repo> --base <target-sha> --destination <outside-dir>` produces a tree identity.
   Pass a `--destination` that does not exist yet: the runner creates it, and refuses an existing
   path so earlier evidence is never overwritten. Use a new name for every capture, including the
   one after a fix batch.
   Despite its name, `--base` takes the **target** commit, normally `origin/main`'s tip: capture
   derives the actual review base itself as the merge base of HEAD and that target. Passing a
   merge-base commit here would silently narrow the reviewed change.
3. Run appropriate checks on that tree: scoped checks that cover the changed modules and the
   invariants they touch, not the full suite. The full suite runs once per PR head, in CI on the
   draft PR (or once locally before the ready flip where no CI job runs it), and `create-pr`
   reports its result before offering the ready flip. Create checks JSON
   with `tree` (the snapshot's full tree SHA), `status` (`passed`, `failed` or `unavailable`), and
   `evidence` (a non-empty **string**, not an array or object, describing commands/results rather
   than just a pass count). The evidence begins with `scoped` or `full`, followed by the exact
   command, its duration, and the count of skipped tests with their reasons. A scoped pass
   satisfies this check requirement; it is never described as a full pass in a handoff summary,
   PR body or report. For example, substitute the captured tree and actual results in:

   ```json
   {
     "tree": "<tree from snapshot>",
     "status": "passed",
     "evidence": "scoped: python -m unittest -f pre_pr_lens_review.tests.test_snapshot (102s; 40 tests, 1 skipped: Windows symlink privilege). OK.\ngit diff --check: passed."
   }
   ```
4. Create intent JSON with `key`, `card`, `spec_url`, `spec`, `requirement`. For work without a card,
   key/card/spec may be empty; a key discovered in the branch still requires card text.
5. `--progress run --repo <repo> --base <target-sha> --intent <json>
   --checks <json> --config <json>` is the normal entry point (`--progress` is a global flag and
   goes before the subcommand). For a new run it captures and
   freezes the inputs exactly as `start` does (and refuses concurrent live work for that repository),
   then sequences preflight, the authenticated fixture probe on generated source, and review
   passes while the policy permits, returning the structured summary at the next `ask`, `fix`,
   `ready` or `stop`. An optional `--state <outside-dir>` suggests the new-run directory; use the
   returned `root` thereafter. Only after all three providers complete the probe does it send caller source.
6. Follow the summary's next action (`triage`, `answer`, `begin-fix`/`finish-fix`, `handoff`),
   then `--progress run --state <dir>` again. Resuming respects the saved phase, frozen inputs,
   completed passes, spent attempts and a valid recorded probe. Supplying all fresh inputs also
   checks compatibility and enables the recovery policy above; `resumed: true` means compatible
   evidence was retained. A state-only invocation cannot create replacement evidence.
7. `start`, `preflight`, `probe`, `review` and `status --state <dir>` remain available for
   explicit step-by-step control with their existing results. The dispatcher owns evidence-based
   judgement; the runner owns identities, completion and limits. Live updates and the read-only
   observer are described under [Progress, observation and freshness](#progress-observation-and-freshness).

### Review interruptions and input mutation

The schedule is pass 1 Sonnet/Luna/Composer, pass 2 Opus/Sol/Grok, then at most two Grok-only repair
checks. The stronger pass always runs. Reviewers within a pass run concurrently, one per provider.
Each fresh invocation applies all four lenses. Failed reviewers retry once on unchanged inputs;
completed peers are retained. Attempts are saved before launch, so interruption consumes an attempt. An interrupt during a
review records the interruption: after live work ends, `run` can resume compatible evidence
with the same spent attempts. Like the mutation stop, it is a disposition and not a kill.
The reviewers already launched are not cancelled and run to completion, so the command returns
only once the slowest of them finishes or reaches its deadline, and one that overruns is ended
by the ordinary timeout rather than by the interrupt.
Cancelling an inspection such as `status`, or printing a completed command's result, preserves
the saved run. Interrupted CLI output uses `action: stop` to end the command and `recorded_phase`
to identify the saved run phase; it is not a fresh handoff or a claim that readiness was rechecked.
Read `recorded_phase` and inspect status before continuing.
Interrupting active `preflight`, `probe` or `review` work records an interruption; the recovery
policy above still applies once no command or reviewer remains active.
Detected input mutation stops without retry and schedules no further reviewer. That stop is a
disposition, not a kill: the reviewers already launched in that pass are not cancelled, so the
command returns only after the slowest of them finishes or reaches its timeout, and the results of
those still in flight are discarded. A peer report already recorded when the mutation is detected
is retained, and the pass stays incomplete, so that report is never a partial review.
Each reviewer has an execution deadline and a retained-output limit; `preflight` reports both
effective values. After the parent exits, pipe draining gets a separate short budget, followed by
bounded best-effort cleanup and another short drain. A held pipe cannot erase an observed exit code.
A zero exit with a complete, valid result can succeed even if a descendant keeps a pipe open; a
stdout result then needs its complete newline-terminated frame, while Codex uses its final result
file. The supervisor records the native CLI exit separately. If the controller dies, its lease
remains held while reviewer work continues. A live controller ends the supervisor's process
tree after a bounded drain and confirms its exit before returning a completed report.
On Windows its job object also ends remaining child processes when the supervisor exits.
Truncated streams, incomplete results, wrong identities, nonzero exits and true execution
timeouts remain failures. stdout/stderr tails and the Codex final result are bounded; the stream
limit counts every provider's protocol events, after the lines that echo a reviewer's inputs back
(Claude tool results, Codex command output, Cursor completed tool calls) have been dropped from the
retained tail; those are never needed by the result or activity parsers. Pending input frames
have a separate 16 MiB character ceiling, allowing large tool-result echoes to be discarded
without retaining them as results; exceeding it marks the stream truncated and rejects the
attempt. The activity parser drops frames above its 4 MiB character ceiling and resumes at
the next newline. Live progress is described
under [Progress, observation and freshness](#progress-observation-and-freshness).
An execution timeout is retryable only after the parent CLI's exit is confirmed. If termination
cannot be confirmed, the run stops without retry and records the PID and partial output for
inspection. Descendant cleanup remains best-effort; this does not prove cancellation at the vendor.

### Triage and fix commands

`triage --state <dir> --file <json>` takes a list of decisions:

```json
[{"id":"F-001","verification":"confirmed","action":"fix","evidence":"path:line; trigger, wrong outcome and remedy verified against the requirement"}]
```

Verification is confirmed/refuted/unclear; action is fix/none/ask. Every claim needs author
verification, including minors. Queue clear, confirmed in-scope defects as `fix` without per-finding
human selection, subject to the accepted-minor-limitations exception below; severity does not gate
that authority. Unverified claims and queued fixes block
readiness. `ask` is for a decision or an uncertainty that remains after investigation, such as
contradictory requirements or an unclear remedy. Refutations need evidence and stay visible. Claims
retain separate stable IDs; the author may fix a proven common root cause once while recording every
affected ID. A confirmed minor advisory may use `none` with evidence explaining why the captured
requirement needs no change. The sole exception for a clear minor defect is
[review-code's accepted minor limitations rule](../../.agents/skills/review-code/SKILL.md#accepted-minor-limitations),
which owns the judgement and what `evidence` records; the runner records it through its existing
`confirmed`/`none` decision. An impossible trigger instead refutes the finding. Fixes of any
severity need fresh review and share the existing pass limit, except the single minor-only batch
after the final pass described under `begin-fix`.

`answer --state <dir> --file <json>` records the human's actual `text` and `kind`: clarify,
changed_requirement, exception, stop, request_minor (with `ids`, retained for older callers; no longer
required to fix a minor), or checks_unavailable. A changed
requirement, accepted material defect, or stop ends the run. Clarification is followed by the
corresponding evidence-based triage; it does not itself remove a finding. An unavailable check may
be explicitly resolved; a failing check cannot be waived as unavailable.

`sensitive --state <dir> --file <json>` takes `entries` copied from the snapshot's detected sensitive
list and the human's approval `text`. Each entry binds an exact path and before/after blob identity.
Changed content needs a new exception. The path checks cover the patterns in snapshot.py; unchanged
baseline matches remain advisory, and ordinary files may still contain credentials.

`begin-fix --state <dir>` validates current inputs and remaining capacity, saves a fixing marker,
and returns a batch token. Apply the selected edits without staging. If the fix adds a file, run
`git add -N <path>` or ignore it before capturing: an untracked, non-ignored file blocks the
post-fix snapshot. Run scoped checks recorded as
in step 3 above (not the full suite, which runs once per PR head), capture the new tree, then
`finish-fix --state <dir> --checks <json> --token <token>` schedules its review (after the fourth
pass it records an unreviewed delta instead, as below). Use the token only
for that uninterrupted author batch. After a crash, follow the interrupted-fix inspection and
fresh-check procedure above; never recover the token from state and blindly replay
or finalise uncertain edits.
An observed branch change during fix completion stops durably; switching back cannot reuse its token.

After the fourth pass no review remains. If every outstanding fix is minor, `begin-fix` is still
permitted once, and `finish-fix` records the batch as `unreviewed_delta` in the summary (finding
IDs, the new tree, input and checks, and the last reviewed tree) instead of scheduling a review. Its
findings are marked `unreviewed` and no further triage is accepted. Successful `handoff` and
`compare-pr-head` commands validate the delta's tree. `status` validates it only for the current
run while it is not stopped; stopped or historical runs return recorded state without rechecking
the snapshot or caller tree. The delta's checks are its only verification, so they must
pass: a failed or unavailable result stops the run, and `checks_unavailable` cannot waive it. That
stop is final for the run; with no pass or batch left, the way forward is a new run. A sensitive
path the delta touches needs the exact human exception before readiness. A material finding at the
fourth pass, or anything left after that batch, exhausts review capacity as before.

### Handoff and PR-head comparison

`handoff --state <dir>` rechecks the live branch/tree and returns a structured Testing summary.
Before accepting review, `create-pr` commits intended repairs under its existing commit authority,
pushes, and successfully runs `git fetch origin <branch>`. It calls `compare-pr-head --state <dir>`
and requires readiness and a matching tree. After opening the draft, it repeats the successful
fetch against `pull/<number>/head` and the comparison, recording both results in `Testing`.
To compare an actual PR head, first run `git fetch origin pull/123/head` in the caller repository.
After a successful fetch, run `compare-pr-head --state <dir>` through the Python module. It checks
FETCH_HEAD against the handed-off tree (the reviewed tree, or the `unreviewed_delta` tree) and
revalidates readiness. A failed fetch must stop the comparison. Committing unchanged content is allowed;
later content edits invalidate review. The result contains all required reviewer completion,
findings/refutations/minors, human decisions, check evidence, sensitive exceptions and excluded
unchanged submodules. It never
publishes the PR. Call `handoff` again immediately before invoking `create-pr` or recommending
a draft be marked ready. If either workflow leads to edits, those need fresh loop review.

### Publishing to an open PR

After **ready**, follow the canonical
[publishing contract in `review-code`](../../.agents/skills/review-code/SKILL.md#publishing-to-an-open-pr)
for commit authority, handoff validation, the single push and reporting a failed remote comparison.

## Progress, observation and freshness

Observations are evidence about execution, never review acceptance. `state.json` stays the
authoritative record; everything in this section is additive and changes no verdict, attempt
count, pass limit or handoff rule.

**Authoring session.** Before the first `run` of a session, open the developer's observer window
against the known run directory with
`python scripts/pre-pr-lens-review.py observe --follow --window --state <dir>`. Tell the developer
the window opened and what it shows; for a new explicit directory it waits for the first
observation. If the command reports `window: unavailable`, give the developer its returned
`command` to paste into a terminal. If recovery selects another `root`, or the runner allocates
one automatically, open the observer against that returned root as soon as it is known. Reuse
the observer for later commands on that run.

Always invoke the runner with `--progress` before the subcommand. As soon as your host lets you
respond, report a failed reviewer and attempt, the concise reason, the diagnostics path and the
runner's next permitted action, and report any recorded human-input need. Investigate without
waiting to be asked. Author verification is not a question already put to the human. If the host
buffers output until completion, say so once and point to
`python scripts/pre-pr-lens-review.py observe --follow --state <dir>` in a second terminal.
If bounded output delivery leaves JSON absent or incomplete, inspect the retained run; missing
JSON is not a verdict. `observe` authorises nothing; `status`, `handoff` and `compare-pr-head`
keep the validation role.

**`--progress`** is a global flag placed before the subcommand (`python scripts/pre-pr-lens-review.py
--progress run ...`). The repository dispatcher always passes it. Without it every command's stdout,
stderr and exit code are exactly as before. With it the JSON result is unchanged except for one
additive field, `observability_problems`, present only when the channel itself failed (see below);
`snapshot` builds no controller and prints no progress lines. With it:

- Human-readable updates go to **stderr**, one per line, each starting with `[review] HH:MM:SS `.
  The JSON result preserves the verdict and exit semantics, with the failure-only warning field
  described above. A successful command's JSON is on stdout; on a failure it follows the progress
  lines on stderr. Drop the prefixed lines from whichever stream carries the result before parsing
  it. If a stream stops accepting
  output, delivery is bounded: final JSON may be absent or incomplete. The original exit
  code is preserved, cleanup releases the controller lock, and the ended reason and delivery
  problem remain in `progress.json` when the channel is bound and that file is writable.
- A new run's first update announces the capture before it begins, and the run identity as soon
  as it exists; a resumed run's first update names the run and command. A failed start still ends
  with its reason. Preflight, the probe and each review pass are stages. Every reviewer attempt is reported as it changes: `launching`, `running`
  (with pid), `exited N; validating its report`, `validated`, or `FAILED` with a concise reason, the
  saved diagnostics path (or that it could not be saved) and the next permitted action under the
  existing retry policy: retry once after the remaining reviewers in the pass finish, retry once
  now, or retry limit reached and the run stops. A stop names the reviewers still running and
  says their results will be discarded, not accepted; when they finish they are marked discarded.
  An exited process is never called validated until its report and identity checks pass.
- **What each reviewer is doing.** Every reviewer runs in its CLI's streaming mode (Claude
  `stream-json`, Codex `exec --json`, Cursor `stream-json`) and the runner parses the event stream
  into an activity feed: the tool or command (`read`, `glob`, `grep`, `command`, a short `note`
  when the reviewer says something, `report` when it writes its result) and the target, shown
  relative to the review pack (`opus read scripts/pre_pr_lens_review/cycle.py (14 activities)`).
  The first activity of an attempt is printed at once; later ones at most every ten seconds per
  reviewer, with the latest carried by every heartbeat. Raw tool results and input prompt events
  are excluded; commands are shown without their output. Short notes may quote source text for
  the developer. Each
  attempt records the count, the latest activity, when it was seen and the signal `source`
  (`stream`, or `output-age` for a CLI whose stream gave nothing). Activity proves a reviewer is
  working, not that the work is useful.
- Between changes a one-line heartbeat is printed at least every 30 seconds: stage, elapsed time,
  each reviewer's state and elapsed time, and for a running reviewer its latest activity and how
  long ago (`read cycle.py 0:06 ago (14 activities)`), or `no activity seen yet` with the output
  age or `no output yet`. None of these values proves a hang. Elapsed time stops growing once an
  attempt's end is known.
- The command's last line records how it ended: the next action and what the run now waits for,
  derived from recorded transitions only. A command that fails without stopping the run (a missing
  CLI, a refused start, a lock held by another command) ends with `command failed — <reason> ·
  recorded next action <action>`; `stop` is reserved for a recorded stop. `ask` is reported as author verification (not a human
  question yet) unless a triage recorded `ask` or an unavailable check needs a decision; an
  interrupted fix batch is named as such. No heartbeat process outlives the command.
- Terminal lines pass through a bounded queue drained by a background thread. If the terminal
  stops accepting output the queue fills, later lines are dropped and the drop is reported as a
  visibility problem. Finalisation allows a two-second progress flush, a separate two-second
  final-result delivery, and a two-second cleanup flush. An in-flight stderr write that misses
  its flush prevents final JSON delivery to that same stream; no competing write is started.
  Standard-stream writes bypass Python's buffered writer so a stalled background write cannot
  hold its lock during interpreter shutdown.
- Updates carry runner-controlled metadata, the activity feed and concise failure
  classifications. Notes and targets are clipped and credential-shaped values are redacted on
  a best-effort basis; this is not a guarantee that arbitrary text contains no secret.
  The retained CLI response stays in `errors/`, linked by path, not streamed.
- The same observations are saved atomically to `progress.json` beside `state.json`: bounded
  (last 50 events), attributable to the run, and never a substitute for the state record. If it
  cannot be written or the terminal cannot be written to, the command reports
  `observability_problems` in its result and continues; a visibility failure never changes a
  review verdict, reruns a reviewer or blocks execution or cleanup.

**`observe --state <dir>`** is the independent, read-only view for a second terminal or an agent
while the controller owns its lock. It takes no lock, writes nothing under the run directory or the
ownership registry, does not validate the caller tree, consumes no attempt and authorises nothing.
It prints one JSON snapshot (`--follow` prints prefixed text lines instead) with
`observation_only: true` and `handoff_eligible: false`, also for
a recorded `ready` phase; only `handoff`/`compare-pr-head` validate the current tree. It reports
the recorded phase, next action, passes and what the run waits for from `state.json`, the runner's
last observation from `progress.json`, `ownership` (`current`, `historical`, or `unknown` when the
registry or the caller repository is unavailable; an archived run stays readable after its
repository has moved), and a `freshness` label judged from the runner's own wall-clock timestamp,
never from a stored `running` label. Recorded per-attempt values are as of the runner's last
update; for an attempt with no recorded end, `observe` measures elapsed time from its start
timestamp and adds the runner's silence to its last-output age and last-activity age, so all three
stay current without claiming the process is alive:

| `freshness` | Meaning |
|---|---|
| `live` | the runner command updated within the last 60 seconds |
| `stale` | a runner command was active but has been silent for 60 seconds or more, or its timestamp is ahead of the observer's clock: *Updates stale—activity unconfirmed*. Clock discrepancies are named and ages never go negative. Recorded outcomes are retained; this is not proof that the runner or a reviewer is hung or dead, and never a reason to start anything |
| `ended` | the last command recorded its end (an author/human wait or a stop); this never becomes stale |
| `unavailable` | no readable observation: a run from before this feature, no command run with `--progress` yet, or a damaged file. `problems` names the source (`state.json unreadable`, `progress.json unreadable`, another run's progress, missing directory). Damaged evidence is never shown as an empty, healthy or completed run |

`observe --follow --state <dir>` keeps a terminal observer attached: it prints each new runner
event including activity lines (saying how many it missed if more than the retained 50 arrived
between polls), and while the runner is silent prints the stale warning after 60 seconds and repeats it every
30 seconds with the age of the last update. Those reminders confirm only that the observer is
running. A fresh runner update clears the warning; a recorded command end prints the outcome and
exits, unless the observer attached only after that end (it then waits for the next runner command)
or was started with `--stay`, which keeps it following across commands. An optional
`--idle-timeout <seconds>` closes a follow observer when no new runner event arrives for that long;
stale reminders do not reset the timer. Age is recomputed from the wall clock on every tick, so an observer whose host was suspended
reassesses on resumption rather than continuing a count. The one-shot form returns within a couple
of seconds; repeated reminders need the `--follow` session to stay open. Ctrl-C detaches the
observer with `observer detached; the run is unchanged`; it is not a stop.

`observe --follow --window --state <dir>` opens that observer, with `--stay`, in a terminal window
of its own and returns at once: macOS through Terminal (a `.command` script, which needs no
Automation consent), Windows in a new console, Linux through the default terminal emulator. It can
be opened before the run exists; the observer waits for the first observation, and stays open
across commands while they produce events. The window closes automatically after ten minutes
without a new runner event, including while waiting for the first run, or the developer can close it earlier.
When no window can be opened (a headless host, no known emulator) it prints
`window: unavailable` with the exact command to paste instead, so the feed is on screen without
anyone pasting anything.

**Authoring clients.** Claude Code, Codex CLI and the Codex VS Code extension on macOS and Windows
receive these updates in their tool output on a best-effort basis: a host that buffers a command's
output until it completes shows the progress lines only at the end (Claude Code's Bash tool does).
That is a recorded limitation, not a defect in the runner, and it is why the dispatcher opens the
observer window before it starts a run. The fallback in every client is the read-only query or
`observe --follow` in an ordinary second terminal.

## Recovery and tests

state.json is the single authoritative record, atomically replaced with a content-integrity digest.
Current-run validation and fix completion also recheck every distinct retained snapshot against
its recorded digest. Damaged or missing earlier evidence cannot support readiness, even when the
latest caller tree is valid; `run` with fresh inputs follows the recovery policy above.
Historical inspection remains an evidence read without live checks.
Summaries include `retained_reports` for accepted reviewers in incomplete passes, with pass/input
provenance. These remain evidence only; they enter the triage findings ledger once, when the pass
completes. A stopped summary also supplies `diagnostic_handoff` with the template and evidence
locations; its `required` flag identifies exhausted review capacity with unresolved actionable work.
Every rejected reviewer response saves its stdout/stderr under the run directory’s `errors/` folder,
with the path in the recorded error and in `diagnostics` when the run has stopped: a failed exit,
malformed or unparseable output, a well-formed error envelope, a document that fails schema or
identity validation, a reviewer that exceeded its wall-clock limit (its partial output is retained),
and one that exceeded the retained-output limit (its tail is retained).
**Before upgrading the runner, stop all old runs and their reviewer processes. Do not operate old
and new runner versions concurrently.** The discovery record for the current run
lives at `~/.eng353-controllers/<digest>.json`, deliberately outside the temporary
directory so a different `TMPDIR`/`TEMP` cannot silently produce a second registry.
A missing run directory or failed integrity check permits recovery with fresh
inputs once no live command or reviewer remains. Old artifacts remain diagnostic evidence, never accepted
review results. They may contain reviewed source; keep them local with the other run artifacts.
The runner does not dump environment variables or read credential stores to create diagnostics.
A repository-wide live command lock serialises controllers across worktrees; reviewer guardians
retain separate lifetime locks while provider processes remain active. Snapshots and reports are
external working artifacts; do not commit them. Recovery needs fresh inputs and existing review
authorisation, and cannot overlap active work. Stopped/ready historical records remain inspectable.
Historical inspection does not acquire the new owner's controller lock, compare today's caller
tree or rewrite the archived record. Its summary has `historical: true`, the recorded `phase` and
`recorded_action`, and an effective `action: stop` with `handoff_eligible: false` (CLI exit 2).
It is an evidence read, not a new handoff. Current-run status still checks live inputs and records
observed mutation as terminal; restoring the old bytes does not revive readiness.

### Diagnostic handoff

When the review budget ends with unresolved actionable work, the dispatcher prepares a diagnostic
brief and a copyable prompt for a fresh human-selected agent using
[diagnostic-handoff.md](diagnostic-handoff.md). Save the handoff outside the caller tree, alongside
the retained run artifacts. Include the exact run and revision, requirement and settled decisions,
every pass's evidence, verified findings and refutations, fixes with their resulting snapshots,
remaining uncertainty, and actual test results. Separate the runner's recorded facts from the
author's assessment; mark unproven root causes as hypotheses. Preserve the old record and its
limits, distinguishing repair regressions from newly discovered old defects. Unlike ordinary
independent reviewers, the diagnostic agent needs the repair history to challenge the approach.
This handoff proposes diagnosis; it neither launches another agent nor authorises more edits
or a replacement run.

### Tests

From `scripts`, run `python -m unittest discover -s pre_pr_lens_review/tests -t .` on either platform.
On macOS/Linux, `bash scripts/pre_pr_lens_review/run-tests.sh` from the repository root is equivalent.
That is the full suite, which the hub's CI runs on each PR head that touches its declared paths
(below). While iterating and in repair rounds, run only the test modules that cover the change:
name them on the command line, and add `-f` (`--failfast`) to stop at the first failure and show
its traceback. From `scripts`, a typical one-module change to `snapshot.py` needs, on Windows and
on macOS/Linux respectively:

```
python -m unittest -f pre_pr_lens_review.tests.test_snapshot
python3 -m unittest -f pre_pr_lens_review.tests.test_snapshot
```

That returns in under 2 minutes on Windows. Add a module for each invariant the change touches, for
example `pre_pr_lens_review.tests.test_cycle` for a change to how capture is scheduled. A scoped pass
does not validate unrelated behaviour, so record it as `scoped`, never as a full pass.
In the standards hub only (`nub_model_repository`; this README is synced downstream, that workflow is
not), [`local-review-tests.yml`](https://github.com/Noetica/nub_model_repository/blob/main/.github/workflows/local-review-tests.yml)
runs the Python 3.12 fixtures on macOS, Windows and Linux, triggered only when the runner, its entry
script, the skill bodies or shared resources the docs-lockstep test reads, or the workflow itself
change (that trigger's `paths` list is the authority).
No unit test reads credentials or makes a paid model call. The live owner trial and later cloud
comparison are separate evidence, not simulated by stub results.
`tests/demo_observability.py` (hub-only) is the reusable manual spot check for progress: it builds a
throwaway repository and run, drives `--progress run` with fixture reviewers (one slow and silent,
one that fails and is retried, peers that succeed) to the author-verification boundary, records the
finding as a human question with `triage`, shows that wait through `observe`, and prints
the `observe --follow` command for a second terminal. Try it in a terminal or through an authoring
client and record the client, OS and version, what appeared, and any buffering; variants not tried
are simply untested.

The controller uses OS-released locks on each platform and atomically replaces flushed state files.
On Windows, Python cannot additionally fsync the containing directory through the Windows CRT;
malformed state cannot be accepted as a completed run. Fresh inputs permit automatic recovery;
readiness still requires complete, valid evidence for the current tree.
