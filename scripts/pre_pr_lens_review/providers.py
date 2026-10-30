"""Fresh reviews through installed CLIs, using their normal cached logins."""
from __future__ import annotations

import codecs
import io
import json
import os
import shutil
import signal
import subprocess
from pathlib import Path
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from .activity import ActivityParser, codex_spawn_failure, retain_line
from .cycle import BoundaryError, Controller, PROVIDERS, ReviewError, validate_report, digest
from . import process_lock
from .cursor_output import parse_cursor
from .progress import NullProgress
from .snapshot import content_digest, SnapshotError

# Per-reviewer wall-clock limit. Measured evidence for the default: on this repository's
# own branch (a ~3,700-line diff, two exported trees) a Cursor reviewer took 1034s and the
# Claude and Codex reviewers 722s and 740s, so 1200s leaves little headroom on a larger
# change. preflight reports the effective value so it appears in the run record.
REVIEWER_TIMEOUT_SECONDS = 1200
# Bounded tail retained from an oversized reviewer stream, counted in characters because
# streams are decoded incrementally as UTF-8. Every provider now streams events, and the lines
# that echo a reviewer's inputs back (Claude tool results, Codex command output, Cursor completed
# tool calls) are dropped before retention (activity.retain_line), so what remains is the
# reviewer's own events and its final result: a probe-sized Claude stream measured 36KB with
# those lines, about 4KB without. This stays a runaway guard, not a working limit.
REVIEWER_OUTPUT_CHAR_LIMIT = 4 * 1024 * 1024
# A complete tool-result frame can exceed the retained-output limit and then be
# discarded. Bound its pending input separately so large echoes still work.
REVIEWER_FRAME_CHAR_LIMIT = 16 * 1024 * 1024

CODEX_DISABLED = ('apps', 'auth_elicitation', 'browser_use', 'browser_use_external',
                  'browser_use_full_cdp_access', 'computer_use', 'hooks', 'image_generation',
                  'in_app_browser', 'memories', 'multi_agent', 'multi_agent_v2', 'plugins',
                  'remote_plugin', 'skill_mcp_dependency_install', 'skill_search',
                  'tool_suggest', 'workspace_dependencies', 'shell_snapshot')


CODEX_SANDBOX_SETUP_FAILED = 'setup refresh had errors'


def codex_sandbox_blocked(stdout):
    """Why a Codex reviewer's commands could not start, or None when nothing says so.

    On Windows, Codex refreshes its sandbox's file permissions before every command, and
    exits zero with a report even when every refresh failed and it read nothing. The cause
    observed is another Codex session holding node_repl.exe open; see the README.
    """
    for line in (stdout or '').splitlines():
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        failure = codex_spawn_failure(event)
        if failure and CODEX_SANDBOX_SETUP_FAILED in failure:
            return ("codex's Windows sandbox could not start its commands ('setup refresh had "
                    "errors'), so it could not read the review pack. This usually means another "
                    'Codex session is running node_repl.exe, part of Codex\'s computer-use runtime. '
                    'Close that session (an interactive Codex CLI was observed starting it), end any '
                    'node_repl.exe left in Task Manager, and run again. See "Codex on Windows: setup '
                    'refresh had errors" in scripts/pre_pr_lens_review/README.md')
    return None


def parse_result(provider, stdout, result_path=None, *, stdout_complete=True):
    if provider == 'codex':
        if result_path is None or not result_path.is_file():
            raise ReviewError('Codex did not write a final structured result')
        with result_path.open(encoding='utf-8') as stream:
            final = stream.read(REVIEWER_OUTPUT_CHAR_LIMIT + 1)
        if len(final) > REVIEWER_OUTPUT_CHAR_LIMIT:
            raise ReviewError('Codex final result exceeds the output limit')
        return json.loads(final)
    if not stdout_complete and not stdout.endswith('\n'):
        raise ReviewError('Reviewer output is incomplete: no complete result frame before pipe drain ended')
    if provider == 'cursor':
        return parse_cursor(stdout)
    if provider == 'claude':
        return _claude_result(stdout)
    document = json.loads(stdout)
    if isinstance(document, dict) and isinstance(document.get('result'), str):
        if document.get('is_error'):
            raise ReviewError(f'{provider} reported an execution error')
        result = document['result'].strip()
        return json.loads(result)
    raise ReviewError(f'{provider} returned no structured result')


def _claude_result(stdout):
    """The structured report from Claude's stream-json output: its final `result` event.

    A single JSON document (the older json output mode) is still accepted, so a recorded
    or hand-written document parses the same way.
    """
    try:
        documents = [json.loads(stdout)]
    except ValueError:
        documents = []
        for line in stdout.splitlines():
            if not line.strip().startswith('{'):
                continue                     # a stray banner or warning is not the review
            try:
                documents.append(json.loads(line))
            except ValueError:
                continue
    if not documents:
        raise ValueError('Claude returned no JSON output')
    results = [d for d in documents if isinstance(d, dict) and
               (d.get('type') == 'result' or 'structured_output' in d or 'result' in d)]
    if not results:
        raise ReviewError('Claude did not return a terminal result event')
    document = results[-1]
    if document.get('is_error'):
        raise ReviewError('Claude reported an execution error')
    if 'structured_output' in document:
        return document['structured_output']
    if isinstance(document.get('result'), str):
        return json.loads(document['result'].strip())
    raise ReviewError('claude returned no structured result')


class ReviewProcessError(ReviewError):
    """A reviewer failed during execution. Carries partial output for diagnosis."""

    def __init__(self, message, result):
        super().__init__(message)
        self.result = result


class ReviewTimeout(ReviewProcessError):
    """The supervised invocation did not exit within its execution deadline."""


class ReviewTerminationError(ReviewProcessError):
    """The supervised process may still be running; another invocation must not start."""


OUTPUT_TRUNCATION_MARKER = '[earlier output truncated]\n'
PROCESS_CLEANUP_SECONDS = 2


def bounded(stream):
    """Retain a marked tail within the character limit."""
    if stream is None or len(stream) <= REVIEWER_OUTPUT_CHAR_LIMIT:
        return stream, False
    keep = REVIEWER_OUTPUT_CHAR_LIMIT - len(OUTPUT_TRUNCATION_MARKER)
    return OUTPUT_TRUNCATION_MARKER + stream[-keep:], True


class _OutputTail:
    """Bound retained output and pending input frames separately, plus one read chunk."""

    def __init__(self, on_output=None, on_text=None, retain=None):
        self.text = ''
        self.truncated = False
        self.error = None
        self.finished = False
        self.lock = threading.Lock()
        self._on_output = on_output
        self._on_text = on_text
        self._retain = retain          # per complete line: keep it in the retained tail?
        self._partial = ''
        self._partial_truncated = False

    def append(self, text, *, final=False):
        retained = text
        if self._retain is not None:
            # Line-buffered retention: echoed inputs are dropped before they can count
            # against the limit. A trailing partial line is kept as is at the end so an
            # incomplete final frame is still detectable.
            self._partial += text
            *lines, self._partial = self._partial.split('\n')
            kept = []
            for line in lines:
                oversized = self._partial_truncated or len(line) > REVIEWER_FRAME_CHAR_LIMIT
                if oversized or self._retain(line):
                    kept.append((OUTPUT_TRUNCATION_MARKER if oversized else '') + line + '\n')
                self.truncated |= oversized
                self._partial_truncated = False
            clipped = len(self._partial) > REVIEWER_FRAME_CHAR_LIMIT
            if clipped:
                # No marker here: its newline would manufacture a frame delimiter.
                self._partial = self._partial[-REVIEWER_FRAME_CHAR_LIMIT:]
            self._partial_truncated |= clipped
            self.truncated |= clipped
            if final and self._partial:
                kept.append((OUTPUT_TRUNCATION_MARKER if self._partial_truncated else '') + self._partial)
                self._partial = ''
                self._partial_truncated = False
            retained = ''.join(kept)
        with self.lock:
            self.text, clipped = bounded(self.text + retained)
            self.truncated |= clipped
        if text:
            # The observer learns that output arrived, and the activity parser sees the raw
            # event stream to extract what the reviewer is doing; neither may fail the read.
            for callback, argument in ((self._on_output, None), (self._on_text, text)):
                if callback is None:
                    continue
                try:
                    callback() if argument is None else callback(argument)
                except Exception:
                    # Observability callbacks are best-effort and must not interrupt stream capture.
                    pass

    def read(self, stream):
        # Match Popen(text=True)'s universal newlines, including a CR/LF split
        # across reads, while decoding and retaining only a bounded tail.
        decoder = io.IncrementalNewlineDecoder(
            codecs.getincrementaldecoder('utf-8')(errors='replace'), translate=True)
        try:
            with stream:
                while chunk := stream.read1(16384):
                    self.append(decoder.decode(chunk))
                self.append(decoder.decode(b'', final=True), final=True)
        except (OSError, ValueError) as exc:
            with self.lock:
                self.error = str(exc)
        finally:
            with self.lock:
                self.finished = True

    def snapshot(self):
        with self.lock:
            return self.text, self.truncated, self.finished, self.error


def _stop_cli(process):
    """Best-effort tree cleanup must itself finish, including on Windows."""
    if os.name == 'nt':
        try:
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False, timeout=PROCESS_CLEANUP_SECONDS)
        except (OSError, subprocess.TimeoutExpired):
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=PROCESS_CLEANUP_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        pass


class _AttemptMonitor:
    """Forward one reviewer's process lifecycle and activity to the progress channel.

    Bound to the attempt it observed starting, so a reader thread that outlives its
    process cannot attribute late output to a later attempt of the same reviewer.
    """

    def __init__(self, progress, reviewer, provider=None, workspace=None):
        self.progress, self.reviewer, self.provider = progress, reviewer, provider
        self.key = None
        self.parser = (ActivityParser(provider, workspace, self._activity)
                       if provider and progress.enabled else None)

    def retain(self, line):
        return retain_line(self.provider, line) if self.provider else True

    def started(self, pid):
        self.key = self.progress.attempt_running(self.reviewer, pid)

    def output(self):
        self.progress.attempt_output(self.reviewer, key=self.key)

    def text(self, chunk):
        if self.parser is not None:
            self.parser.feed(chunk)

    def _activity(self, kind, target):
        self.progress.attempt_activity(self.reviewer, kind, target, key=self.key)

    def exited(self, code):
        if self.parser is not None:
            self.parser.finish()
        self.progress.attempt_exited(self.reviewer, code, key=self.key)


def reviewer_environment(provider):
    """The environment a reviewer starts with; None inherits the caller's unchanged.

    On Windows, Cursor wraps each user hook in a PowerShell script but runs it with bash
    whenever MSYSTEM is set, which Git Bash sets itself. Every hook then fails and blocks
    the tool call it guards, so the reviewer cannot read the pack. Claude and Codex start
    with user hooks off (`--setting-sources ''`, `--disable hooks`); the Cursor CLI has no
    such switch, so its reviewer starts without MSYSTEM instead.
    """
    if provider != 'cursor' or os.name != 'nt':
        return None
    # Windows os.environ keys are already upper-case, so an exact match suffices.
    return {k: v for k, v in os.environ.items() if k != 'MSYSTEM'}


def run_cli(argv, cwd, *, prompt=None, timeout=REVIEWER_TIMEOUT_SECONDS, monitor=None,
            repository=None, lease_details=None, env=None):
    """Launch with cached-auth environment and bounded pipe buffers.

    `env`, when given, replaces the inherited environment for the CLI, and for its
    lifetime supervisor, whose reviewer inherits it in turn.

    Daemon readers/writer let the deadline hold even if an escaped descendant keeps a
    pipe open. Only those threads close their streams: closing a buffered pipe from
    here could block forever on the reader's lock.

    `monitor`, when given, hears started(pid), output() per chunk read on either pipe and
    exited(code) once, with None when the deadline passed before an exit was observed.
    Repository-bound invocations report the lifetime supervisor's PID; its lease remains
    held while it waits for the reviewer if the controller process disappears.
    """
    launch_argv, lease = argv, None
    if repository is not None:
        guard_directory = Controller.registry(Path(repository)).with_suffix('.reviewers')
        launch_argv, lease = process_lock.prepare(guard_directory, argv,
                                                timeout + PROCESS_CLEANUP_SECONDS, lease_details)
    try:
        process = subprocess.Popen(launch_argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
            start_new_session=os.name != 'nt',
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP
                           if os.name == 'nt' and lease is not None else 0))
    except OSError as exc:
        raise ReviewError('Could not start the configured CLI; check its executable path') from exc
    if lease is not None:
        try:
            process_lock.await_ready(process, lease, timeout)
        except BaseException as exc:
            _stop_cli(process)
            try:
                _, stderr = process.communicate(timeout=PROCESS_CLEANUP_SECONDS)
                detail = stderr[-4096:].decode('utf-8', errors='replace').strip()
            except (OSError, subprocess.TimeoutExpired):
                detail = 'supervisor output could not be recovered'
            finally:
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()
            if isinstance(exc, ReviewError):
                raise ReviewError(f'{exc}; supervisor stderr: {detail}') from exc
            raise
    if monitor is not None:
        monitor.started(process.pid)
    on_output = monitor.output if monitor is not None else None
    on_text = getattr(monitor, 'text', None) if monitor is not None else None
    retain = getattr(monitor, 'retain', None) if monitor is not None else None
    tails = [_OutputTail(on_output, on_text, retain), _OutputTail(on_output)]    # events arrive on stdout

    # Record whether the prompt was actually handed over, so a failed write cannot be
    # swallowed and then accepted as a review of the full change.
    #
    # What 'complete' establishes, stated narrowly because the name invites a stronger
    # reading: the prompt bytes were written and the stream closed without error. That does
    # NOT prove the CLI consumed them. A live child that never reads a prompt small enough
    # for the pipe buffer still closes cleanly and is recorded complete; proving consumption
    # would need an acknowledgement from the CLI, which no provider here offers.
    written = {'complete': False, 'bytes': 0, 'error': None}

    def write_prompt():
        payload = b'' if prompt is None else prompt.encode('utf-8')
        try:
            with process.stdin:
                if lease is not None:
                    process.stdin.write(b'\x01')
                if payload:
                    process.stdin.write(payload)
            # Set only after close, because a buffered write can succeed while the
            # flush it defers to close fails against a pipe the CLI has already shut.
            written['bytes'] = len(payload)
            written['complete'] = True
        except (OSError, ValueError) as exc:
            written['error'] = f'{type(exc).__name__}: {exc}'

    threads = [threading.Thread(target=tail.read, args=(stream,), daemon=True)
               for tail, stream in zip(tails, (process.stdout, process.stderr))]
    threads.append(threading.Thread(target=write_prompt, daemon=True))
    deadline = time.monotonic() + timeout
    timed_out = False
    exit_code = None
    reviewer_exit_observed = False

    def drain():
        drain_deadline = time.monotonic() + PROCESS_CLEANUP_SECONDS
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=max(0, drain_deadline - time.monotonic()))

    try:
        for thread in threads:
            thread.start()
        remaining = max(0, deadline - time.monotonic())
        if lease is None:
            exit_code = process.wait(timeout=remaining)
        else:
            exit_code, reviewer_exit_observed = process_lock.wait_reviewer(process, lease, remaining)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        _stop_cli(process)
        if isinstance(exc, KeyboardInterrupt):
            drain()
            if monitor is not None:
                monitor.exited(None)
            raise
        timed_out = True
    drain()
    if monitor is not None:
        # After the bounded drain, so a final chunk read as the process exits still reaches
        # the activity parser before the attempt is marked exited.
        monitor.exited(exit_code)
    if not timed_out and lease is None and any(thread.is_alive() for thread in threads):
        # A successful parent may leave descendants holding its pipes. Cleanup has a
        # separate bounded budget and cannot erase the already observed exit status.
        _stop_cli(process)
        drain()
    if lease is not None and process.poll() is None:
        # The native reviewer has exited, but descendants can retain its pipes.
        # End the supervisor's process tree after the bounded drain so the next
        # command never inherits a successful review's active lease.
        _stop_cli(process)
        drain()
    stdout, clipped, stdout_complete, stdout_error = tails[0].snapshot()
    stderr, clipped_err, stderr_complete, stderr_error = tails[1].snapshot()
    result = subprocess.CompletedProcess(argv, exit_code, stdout, stderr)
    result.stdout_truncated, result.stderr_truncated = clipped, clipped_err
    result.stdout_complete = stdout_complete
    result.stderr_complete = stderr_complete
    result.stdin_complete = written['complete'] and not threads[2].is_alive()
    result.stdin_bytes = written['bytes']
    result.stdin_error = written['error']
    result.execution_timed_out = timed_out
    result.pid = process.pid
    result.process_kind = 'supervisor' if lease is not None else 'reviewer'
    result.reviewer_exit_observed = reviewer_exit_observed
    result.supervisor_exit_confirmed = process.poll() is not None if lease is not None else None
    result.parent_exit_confirmed = exit_code is not None
    if timed_out:
        try:
            result.parent_exit_confirmed = process.poll() is not None
        except OSError:
            result.parent_exit_confirmed = False
        if not result.parent_exit_confirmed:
            raise ReviewTerminationError(
                f'Reviewer exceeded its {timeout}s limit and could not confirm exit of '
                f'{result.process_kind} PID '
                f'{process.pid}; stop and inspect the process before another invocation', result)
        raise ReviewTimeout(f'Reviewer CLI exceeded its {timeout}s limit before returning a '
                            f'result; its partial output is retained', result)
    if stdout_error or stderr_error:
        raise ReviewProcessError('Reviewer CLI output could not be fully read; its partial output '
                            'is retained', result)
    if lease is not None and not result.supervisor_exit_confirmed:
        raise ReviewTerminationError('Reviewer exited but its lifetime supervisor could not '
                                     'confirm exit; inspect the process before another invocation',
                                     result)
    return result


def runtime_command(runtime):
    command = [runtime['executable']]
    if runtime.get('entrypoint'):
        command.append(runtime['entrypoint'])
    return command


def commands(provider, runtime, role, snapshot, scratch, request):
    output = scratch / 'result.json'
    identity = {k: request[k] for k in ('run', 'pass', 'reviewer', 'input')}
    document = json.loads((snapshot / 'review.schema.json').read_text(encoding='utf-8'))
    # These values identify this invocation; they are not choices for the reviewer.
    # Derive a provider schema without changing the shared immutable pack schema.
    for key, value in identity.items():
        document['properties'][key]['enum'] = [value]
    schema = json.dumps(document)
    prompt = ((snapshot / 'instructions.md').read_text(encoding='utf-8') + '\nInvocation identity: ' + json.dumps(identity)
              + '\nRead pack.json, change.patch, source/ and base/ in ' + str(snapshot)
              + '\nOutput schema: ' + schema)
    if provider == 'claude':
        # stream-json (which needs --verbose in print mode) reports each tool use as it
        # happens, so the activity feed can show what the reviewer is reading; the final
        # `result` event carries the same structured_output the json mode returned.
        argv = runtime_command(runtime) + ['-p', '--safe-mode', '--restricted',
                '--tools', 'Read,Glob,Grep', '--permission-mode', 'dontAsk',
                '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                '--setting-sources', '', '--disable-slash-commands', '--no-session-persistence',
                '--model', role['model'], '--effort', role['effort'],
                '--verbose', '--output-format', 'stream-json', '--json-schema', schema]
    elif provider == 'codex':
        (scratch / 'schema.json').write_text(schema, encoding='utf-8')
        # Codex reads the pack through shell commands, and on Windows it runs them
        # under a restricted-token sandbox it will not start unless `windows.sandbox`
        # is set. --ignore-user-config drops that setting with the rest of the
        # developer's config, and Codex then reports read-only and refuses every
        # command whatever --sandbox asked for. Supplying the mode explicitly keeps
        # read-only reviews working on Windows while that config stays ignored - and
        # it must stay ignored, because Codex otherwise adds each disposable pack
        # directory to the developer's project trust list. The disposable copy and
        # post-run digest bound input mutation and fail closed if a reviewer changes
        # its inputs.
        # --json prints each item (commands run, messages) as a JSONL event for the activity
        # feed; the final report still arrives through --output-last-message.
        argv = runtime_command(runtime) + ['exec', '--json', '--ignore-user-config', '--ignore-rules',
                '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only',
                '-c', 'approval_policy="never"', '-c', 'web_search="disabled"',
                '-c', 'mcp_servers={}', '-c', 'model_reasoning_effort=' + json.dumps(role['effort']),
                '-c', 'project_doc_max_bytes=0', '-m', role['model'],
                '--output-schema', str(scratch / 'schema.json'),
                '--output-last-message', str(output), '--color', 'never']
        if os.name == 'nt':
            # `elevated`, not `unelevated`: the pack copy lives in a tempfile directory,
            # which is owner-only, and the sandbox's restricted token is not its owner.
            # Only the elevated setup can grant that token read access to it; under
            # `unelevated` the reviewer runs commands but every pack read is denied.
            argv.extend(['-c', 'windows.sandbox="elevated"'])
        for feature in CODEX_DISABLED:
            argv.extend(['--disable', feature])
        argv.append('-')
    else:
        # Cursor encodes effort in the concrete model slug. Never silently add or
        # replace an effort suffix selected by the developer.
        if role['effort'] not in ('encoded-in-model', 'provider-default'):
            raise ReviewError('Cursor effort must be encoded in its selected model slug, or provider-default when not configurable')
        argv = runtime_command(runtime) + ['-p', '--mode', 'ask', '--trust',
                '--model', role['model'], '--output-format', 'stream-json', '--workspace', str(snapshot),
                ''.join(('Read review-request.md and perform the review described there. ',
                         'Return one raw JSON object matching its schema, without introductory prose or Markdown fences. ',
                         'Do not escape the whole object as a string: use ordinary JSON property quotes. ',
                         'Keep each finding, including its remedy, inside one claims array object.'))]
    return argv, output, prompt


class ProviderRunner:
    def __init__(self, config, repository, artifacts, progress=None):
        runtimes = {}
        for name, role in config.items():
            provider = PROVIDERS[name]
            if role['model'] in {'auto', 'default', *PROVIDERS}:
                raise ReviewError(f'{name}: select a concrete model ID, not a moving alias')
            # Reject a launch-time-invalid role here, before any reviewer is paid for.
            # This check used to live in commands(), which a pass-1 role reaches but a
            # pass-2 role does not, so a bad grok effort first surfaced after pass 1 had
            # run, then consumed its retry against a configuration frozen at start.
            if provider == 'cursor' and role['effort'] not in ('encoded-in-model', 'provider-default'):
                raise ReviewError(f'{name}: Cursor effort must be encoded in its selected model slug, '
                                  'or provider-default when not configurable')
            runtime = role.get('runtime', {'executable': {'claude': 'claude', 'codex': 'codex', 'cursor': 'cursor-agent'}[provider]})
            if not isinstance(runtime, dict):
                raise ReviewError(f'{name}: runtime must describe its installed command')
            if provider in runtimes and runtimes[provider] != runtime:
                raise ReviewError(f'{provider}: both roles must use the same installed command')
            runtimes[provider] = runtime
        self.config = config
        self.runtimes = runtimes
        self.artifacts = Path(artifacts)
        self.repository = Path(repository)
        self.validated = False
        self.progress = progress if progress is not None else NullProgress()

    def _launch(self, argv, cwd, prompt, reviewer, provider):
        # The monitor also carries the retention policy, so echoed inputs are dropped from
        # the retained tail whether or not progress is enabled.
        return run_cli(argv, cwd, prompt=prompt,
                       monitor=_AttemptMonitor(self.progress, reviewer, provider, cwd),
                       repository=self.repository,
                       lease_details={'artifacts': str(self.artifacts), 'reviewer': reviewer},
                       env=reviewer_environment(provider))

    def failure(self, provider, request, result, reason):
        """Retain failed CLI output for diagnosis; it is never an accepted review.

        The observation channel learns where the record was saved, or that it could not
        be; it never receives the retained output itself.
        """
        directory = self.artifacts / 'errors'
        stdout, clipped = bounded(result.stdout)
        stderr, clipped_err = bounded(result.stderr)
        record = json.dumps({
            'provider': provider, 'model': request['config']['model'],
            'identity': {k: request[k] for k in ('run', 'pass', 'reviewer', 'input')},
            'exit_code': result.returncode, 'stdout': stdout, 'stderr': stderr,
            'stdout_truncated': clipped or getattr(result, 'stdout_truncated', False),
            'stderr_truncated': clipped_err or getattr(result, 'stderr_truncated', False),
            'execution_timed_out': getattr(result, 'execution_timed_out', False),
            'pid': getattr(result, 'pid', None),
            'process_kind': getattr(result, 'process_kind', None),
            'supervisor_exit_confirmed': getattr(result, 'supervisor_exit_confirmed', None),
            'parent_exit_confirmed': getattr(result, 'parent_exit_confirmed', None),
            'stdout_complete': getattr(result, 'stdout_complete', True),
            'stderr_complete': getattr(result, 'stderr_complete', True),
            'reason': reason
        }, indent=2)
        try:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / (uuid.uuid4().hex + '.json')
            path.write_text(record, encoding='utf-8')
        except OSError as exc:
            self.progress.attempt_diagnostics(request['reviewer'], None, error=str(exc))
            return ReviewError(f'{reason}; diagnostics could not be saved: {exc}')
        self.progress.attempt_diagnostics(request['reviewer'], path)
        return ReviewError(f'{reason}; CLI response saved at {path}')

    def preflight(self):
        """Resolve installed commands and record versions. Authentication stays in each CLI."""
        installed = {}
        # A launched CLI's working directory is this tree, and on Windows an exiting
        # process still holding it makes removal fail. Cleanup is best-effort so it
        # cannot turn a completed check into a failure; whatever is still locked stays
        # in the system temporary directory.
        with tempfile.TemporaryDirectory(prefix='eng353-version-',
                                         ignore_cleanup_errors=True) as temporary:
            for provider, configured in self.runtimes.items():
                runtime = dict(configured)
                executable = runtime.get('executable')
                if not isinstance(executable, str) or not executable.strip():
                    raise ReviewError(f'{provider}: runtime.executable must name its installed CLI')
                executable = shutil.which(os.path.expanduser(executable))
                if not executable:
                    raise ReviewError(f'{provider}: CLI not found; install it or configure its executable path')
                # Batch shims invoke cmd.exe's parser. Use the native Windows CLI
                # (or node.exe + an explicit entrypoint), never shell-quote review text.
                if Path(executable).suffix.lower() in {'.cmd', '.bat'}:
                    raise ReviewError(f'{provider}: select its native .exe or node.exe and entrypoint, not a batch shim')
                runtime['executable'] = str(Path(executable).resolve())
                if 'entrypoint' in runtime:
                    entrypoint = Path(runtime['entrypoint']).expanduser().resolve()
                    if not entrypoint.is_file():
                        raise ReviewError(f'{provider}: configured entrypoint does not exist')
                    runtime['entrypoint'] = str(entrypoint)
                result = run_cli(runtime_command(runtime) + ['--version'], Path(temporary), timeout=30)
                version = result.stdout.strip()
                if result.returncode or not version:
                    raise ReviewError(f'{provider}: could not read CLI version')
                if runtime.get('version') and runtime['version'] not in version.split():
                    raise ReviewError(f'{provider}: installed version differs from the configured version')
                installed[provider] = {'command': runtime_command(runtime), 'version': version}
                self.runtimes[provider] = runtime
        self.validated = True
        return {'installed': installed, 'authentication': 'CLI-managed cached login',
                'access': 'Native CLI review restrictions; no additional OS isolation',
                'reviewer_timeout_seconds': REVIEWER_TIMEOUT_SECONDS,
                'reviewer_output_limit_chars': REVIEWER_OUTPUT_CHAR_LIMIT,
                'runtime_digest': digest(installed)}

    def probe(self):
        """Exercise each pinned provider on generated source before any real source is sent.

        This establishes that the configured CLI flags, cached login and structured
        response work together. It does not establish an OS access boundary.
        """
        if not self.validated:
            raise ReviewError('Run CLI preflight first')
        with tempfile.TemporaryDirectory(prefix='eng353-provider-probe-') as temporary:
            snapshot = Path(temporary).resolve() / 'pack'
            snapshot.mkdir()
            (snapshot / 'source').mkdir()
            (snapshot / 'base').mkdir()
            (snapshot / 'source/example.py').write_text('def add(a, b):\n    return a - b\n')
            (snapshot / 'base/example.py').write_text('def add(a, b):\n    return a + b\n')
            (snapshot / 'change.patch').write_text('-    return a + b\n+    return a - b\n')
            (snapshot / 'pack.json').write_text(json.dumps({
                'intent': {'requirement': 'add must return the sum of its two arguments'},
                'checks': {'status': 'unavailable', 'evidence': 'Generated adapter fixture, not product validation'},
                'snapshot': {'symlinks': {'source': [], 'base': []}, 'submodules': []}}))
            for filename in ('review.schema.json',):
                (snapshot / filename).write_bytes(Path(__file__).with_name(filename).read_bytes())
            (snapshot / 'instructions.md').write_bytes(Path(__file__).with_name('reviewer.md').read_bytes())
            identity = content_digest(snapshot)
            requests = [{'run': 'provider-preflight', 'pass': 1, 'pass_id': 'provider-preflight',
                         'reviewer': name, 'input': identity, 'snapshot': str(snapshot),
                         'config': self.config[name]} for name in ('sonnet', 'luna', 'composer')]
            for request in requests:
                self.progress.attempt_launched(request['reviewer'], PROVIDERS[request['reviewer']], 1)
            reports, first_error = {}, None
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {pool.submit(self, request): request for request in requests}
                # Publish each provider's outcome as it settles, not in submission order: a
                # fast failure must not wait behind a slow peer to become visible.
                for future in as_completed(futures):
                    request = futures[future]
                    try:
                        reports[request['reviewer']] = future.result()
                        self.progress.attempt_validated(request['reviewer'])
                    except Exception as exc:
                        self.progress.attempt_failed(
                            request['reviewer'], str(exc),
                            next_action='probe fails; fix that provider and run probe again')
                        # A boundary failure must not be masked by a faster ordinary one.
                        if first_error is None or (isinstance(exc, BoundaryError) and
                                                   not isinstance(first_error, BoundaryError)):
                            first_error = exc
            if first_error is not None:
                raise first_error
            return {'config_digest': digest(self.config),
                    'reports': [reports[request['reviewer']] for request in requests],
                    'scope': 'Generated fixture only; not a review of the caller change'}

    def __call__(self, request):
        if not self.validated:
            raise ReviewError('CLI preflight must pass before any reviewer launch')
        provider = PROVIDERS[request['reviewer']]
        snapshot = Path(request['snapshot'])
        try:
            before = content_digest(snapshot)
        except (OSError, ValueError, SnapshotError) as exc:
            raise BoundaryError('Reviewer inputs became unreadable before launch') from exc
        if before != request['input']:
            raise BoundaryError('Reviewer pack mutated before launch')
        # See preflight: the reviewer's own working directory can outlive its exit on
        # Windows, and a validated review must not be discarded by that race. What is
        # left behind is this pack copy, so residue can include caller source.
        with tempfile.TemporaryDirectory(prefix='eng353-invocation-',
                                         ignore_cleanup_errors=True) as temporary:
            scratch = Path(temporary).resolve()
            workspace = scratch / 'review'
            shutil.copytree(snapshot, workspace)
            if content_digest(workspace) != before:
                raise BoundaryError('Reviewer inputs changed while copying the pack')
            argv, output, prompt = commands(provider, self.runtimes[provider], request['config'],
                                            workspace, scratch, request)
            if provider == 'cursor':
                # Project permissions avoid replacing Cursor's global config/auth directory.
                (workspace / '.cursor').mkdir()
                (workspace / '.cursor/cli.json').write_text(json.dumps({
                    'permissions': {'allow': ['Read(**)'],
                                    'deny': ['Shell(*)', 'Write(**)', 'WebFetch(*)', 'Mcp(*:*)']}}),
                    encoding='utf-8')
                (workspace / 'review-request.md').write_text(prompt, encoding='utf-8')
            workspace_identity = content_digest(workspace)
            execution_error = None
            try:
                result = self._launch(argv, workspace, None if provider == 'cursor' else prompt,
                                      request['reviewer'], provider)
            except ReviewProcessError as exc:
                result, execution_error = exc.result, exc
            # Validate before classifying any process outcome or disposing of its pack.
            # A timeout/oversized stream must not hide mutation and consume a retry.
            try:
                if content_digest(snapshot) != before or content_digest(workspace) != workspace_identity:
                    raise BoundaryError('Reviewer pack mutated during invocation')
            except (OSError, ValueError, SnapshotError, BoundaryError) as exc:
                reason = str(exc) if isinstance(exc, BoundaryError) else 'Reviewer pack became unreadable during invocation'
                if execution_error:
                    reason += f'; execution also failed: {execution_error}'
                raise BoundaryError(str(self.failure(provider, request, result, reason))) from exc
            if execution_error:
                if isinstance(execution_error, ReviewTerminationError):
                    raise BoundaryError(str(self.failure(provider, request, result,
                                                         str(execution_error)))) from execution_error
                raise self.failure(provider, request, result, str(execution_error)) from execution_error
            stdout, clipped = bounded(result.stdout)
            stderr, clipped_err = bounded(result.stderr)
            if (clipped or clipped_err or getattr(result, 'stdout_truncated', False) or
                    getattr(result, 'stderr_truncated', False)):
                raise self.failure(provider, request, result,
                                   f'{provider} produced more than {REVIEWER_OUTPUT_CHAR_LIMIT} characters '
                                   f'of output; only its tail is retained')
            # Before the exit code: Codex exits zero here, and the cause matters more than
            # any exit code that accompanies it.
            blocked = codex_sandbox_blocked(result.stdout) if provider == 'codex' else None
            if blocked:
                raise self.failure(provider, request, result, blocked)
            if result.returncode != 0:
                raise self.failure(provider, request, result,
                                   f'{provider} exited {result.returncode}')
            if not getattr(result, 'stdin_complete', True):
                # The prompt write itself failed, so what the reviewer was handed is
                # incomplete. Exiting zero with a parseable report does not repair that.
                # This rejects a failed handover only; it does not claim to detect a CLI
                # that received the whole prompt and ignored part of it.
                detail = getattr(result, 'stdin_error', None)
                raise self.failure(provider, request, result,
                                   f'{provider} was not sent the whole review prompt: the write failed'
                                   + (f' ({detail})' if detail else ''))
            try:
                report = parse_result(provider, result.stdout, output,
                                      stdout_complete=getattr(result, 'stdout_complete', True))
            except (ReviewError, ValueError, OSError) as exc:
                # ReviewError is caught deliberately. parse_result raises it for a
                # well-formed error envelope, a missing final message file and a
                # structurally valid document with no result field; unparseable output
                # raises ValueError instead. All of those exit zero, so this is the only
                # path that can retain their stdout/stderr. Catching ReviewError cannot
                # swallow a BoundaryError: every pack-mutation check runs above this block.
                raise self.failure(provider, request, result,
                                   f'{provider} returned invalid structured output: {exc}') from exc
            try:
                validate_report(report, request)
            except ReviewError as exc:
                raise self.failure(provider, request, result,
                                   f'{provider} returned an invalid review: {exc}') from exc
            return report
