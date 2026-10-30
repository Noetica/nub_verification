"""Runner observations of an active command: terminal lines and a saved snapshot.

An observation is evidence about execution, never review acceptance: state.json stays the
authoritative record and `progress.json` beside it is a bounded, additive view of what the
runner has seen. The document carries runner-controlled metadata, concise failure reasons
and each attempt's activity feed as parsed by activity.py: the tool or command, its
pack-relative target or command text, and the short notes a CLI emits as discrete events,
clipped with best-effort credential redaction. Notes may quote source text for the developer;
raw tool results and input prompt events are excluded by activity.py.

Two clocks: wall-clock ISO timestamps let another process judge freshness; the monotonic
clock measures elapsed time inside this process. An attempt's elapsed time stops growing
once its end is known.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time

HEARTBEAT_SECONDS = 30          # a concise heartbeat at least this often while a command is active
STALE_AFTER_SECONDS = 60        # an observer treats a runner silent for this long as unconfirmed
STALE_REMINDER_SECONDS = 30     # and repeats that warning this often while it stays silent
PUBLISH_BOUND_SECONDS = 2       # known transitions are published within this bound of detection
EVENT_LIMIT = 50                # bounded event tail retained in the document
REPLACE_BUDGET_SECONDS = 2      # bounded retry for os.replace against a concurrent Windows reader
PREFIX = '[review] '            # every terminal line starts with this; consumers filter on it
TERMINAL_QUEUE_LIMIT = 256      # lines held for a slow terminal before further lines are dropped
ACTIVITY_LINE_SECONDS = 10      # at most one activity line per reviewer this often; heartbeats carry the rest
ACTIVITY_RECENT = 5             # recent activities retained per attempt


def iso(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat(timespec='seconds')


def parse_iso(text):
    return datetime.fromisoformat(text).timestamp()


def hms(seconds):
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f'{hours}:{minutes:02d}:{secs:02d}' if hours else f'{minutes}:{secs:02d}'


def replace_retrying(source, target, *, replace=None, budget=REPLACE_BUDGET_SECONDS):
    """os.replace that tolerates a concurrent reader holding the target open on Windows.

    CPython opens files without FILE_SHARE_DELETE, so an observer that happens to have the
    target open at the instant of replacement makes os.replace raise PermissionError. The
    reader is transient, so a short bounded retry lets the write succeed; the last error is
    raised when the budget is spent so a stuck target is never reported as written.
    """
    replace = replace or os.replace      # resolved at call time so tests can patch os.replace
    deadline = time.monotonic() + budget
    while True:
        try:
            return replace(source, target)
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)


def _write_stream(stream, text):
    """Write UTF-8 without holding a buffered standard-stream lock during shutdown.

    FileIO and WindowsConsoleIO are unbuffered; the latter accepts UTF-8 and writes
    Unicode to the console. A blocked daemon may stay in the OS write until process
    exit, but cannot deadlock Python's final flush of its TextIOWrapper/BufferedWriter.
    In-memory/injected streams keep their normal text interface.
    """
    raw = getattr(getattr(stream, 'buffer', None), 'raw', None)
    if raw is None:
        stream.write(text)
        stream.flush()
        return
    data = text.encode('utf-8', errors='backslashreplace')
    while data:
        written = raw.write(data)
        if not written:
            raise OSError('output stream accepted no bytes')
        data = data[written:]


def _stderr(line):
    _write_stream(sys.stderr, line + '\n')


class _TerminalWriter:
    """Deliver lines to a possibly slow terminal without ever blocking the runner.

    A daemon thread drains a bounded queue. When the consumer stops reading, the queue
    fills, later lines are dropped and the drop is reported as a visibility problem; the
    runner's execution and cleanup never wait on the terminal beyond a bounded flush.
    """

    def __init__(self, sink, limit=TERMINAL_QUEUE_LIMIT):
        self._sink = sink
        self._queue = queue.Queue(maxsize=limit)
        self._pending = 0
        self._lock = threading.Lock()
        self.error = None
        self.closed = False
        self._thread = threading.Thread(target=self._drain, name='review-terminal', daemon=True)
        self._thread.start()

    def _drain(self):
        while True:
            line = self._queue.get()
            if line is None:
                return
            try:
                if not self.closed:      # a line dequeued after sealing is dropped, not written
                    self._sink(line)
            except Exception as exc:
                self.error = f'{type(exc).__name__}: {exc}'
            finally:
                with self._lock:
                    self._pending -= 1

    def seal(self):
        """No further line reaches the sink; a write already inside the sink finishes."""
        self.closed = True

    def write(self, line):
        with self._lock:
            try:
                self._queue.put_nowait(line)
            except queue.Full:
                return False
            self._pending += 1
            return True

    def flush(self, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if self._pending == 0:
                    return True
            time.sleep(0.01)
        return False

    def discard(self):
        """Drop lines still queued; returns how many. A write already in progress finishes."""
        dropped = 0
        with self._lock:
            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
                self._pending -= 1
                dropped += 1
        return dropped

    def close(self, timeout):
        self.flush(timeout)
        self.seal()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            # Closing stays bounded: a saturated daemon queue must not delay runner shutdown.
            pass


class NullProgress:
    """The disabled channel: every observation call is accepted and dropped."""

    enabled = False

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def snapshot(self):
        return None

    problems = ()

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return lambda *args, **kwargs: None


class Progress:
    """Publish what the runner observes, immediately on change and on a heartbeat between."""

    enabled = True

    def __init__(self, root, *, run, command, sink=None, clock=time.time,
                 monotonic=time.monotonic, interval=HEARTBEAT_SECONDS, bounded=None,
                 terminal_limit=TERMINAL_QUEUE_LIMIT):
        # root may be None until bind(): the channel then reaches the terminal only, so a
        # new run's capture is observable before its directory and identity exist.
        self.root = Path(root) if root is not None else None
        self.path = self.root / 'progress.json' if self.root is not None else None
        self._sink = sink or _stderr
        # The real terminal goes through the bounded writer; an injected sink is delivered
        # synchronously unless asked otherwise, so tests can assert lines as they happen.
        bounded = (sink is None) if bounded is None else bounded
        self._writer = _TerminalWriter(self._sink, terminal_limit) if bounded else None
        self._clock, self._monotonic, self._interval = clock, monotonic, interval
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self._started = monotonic()
        self._last_publish = self._started
        self._attempt_clocks = {}      # attempt key -> {'started', 'ended', 'output', ...}
        self._records = 0              # attempt records issued; the source of unique keys
        self._document = {
            'version': 1, 'run': run, 'command': command, 'pid': os.getpid(),
            'started_at': iso(clock()), 'observed_at': iso(clock()), 'sequence': 0,
            'stage': '', 'detail': '', 'phase': None, 'pass': None, 'waiting_for': '',
            'reviewers': {}, 'stopped': None, 'events': [], 'problems': [], 'ended': None,
        }

    # -- lifecycle -----------------------------------------------------------------------

    def __enter__(self):
        return self.start()

    def start(self):
        """Begin the heartbeat; idempotent."""
        if self._thread is None:
            self._thread = threading.Thread(target=self._beat, name='review-heartbeat', daemon=True)
            self._thread.start()
        return self

    def __exit__(self, exc_type, exc, _tb):
        if self._document['ended'] is None:
            if exc_type is KeyboardInterrupt:
                self.ended('interrupted', 'command interrupted')
            elif exc is not None:
                self.ended('error', str(exc) or exc_type.__name__)
            else:
                self.ended('closed', 'command finished')
        self.close()
        return False

    def close(self):
        self._stop.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=PUBLISH_BOUND_SECONDS)
            self._thread = None
        if self._writer is not None:
            self._writer.close(PUBLISH_BOUND_SECONDS)

    def flush(self, timeout=PUBLISH_BOUND_SECONDS):
        """Give queued terminal lines a bounded chance to land, e.g. before the final JSON."""
        return self._writer.flush(timeout) if self._writer is not None else True

    def discard_pending(self):
        """Drop terminal lines still queued so nothing follows a final result; recorded."""
        if self._writer is None:
            return 0
        dropped = self._writer.discard()
        if dropped:
            with self._lock:
                self._note_problem(f'{dropped} progress line(s) discarded: the terminal did not accept '
                                   'them before the final result')
        return dropped

    def seal(self):
        """Drop future terminal lines; an in-flight OS write may still finish."""
        if self._writer is not None:
            self._writer.seal()

    def result(self, text, stream, *, terminal_flushed, timeout=PUBLISH_BOUND_SECONDS):
        """Bound final delivery, without colliding with an in-flight stderr write.

        An undeliverable result cannot change the command's exit code. The ended reason
        and delivery problem remain in progress.json when this channel is bound/writable.
        """
        if stream is sys.stderr and not terminal_flushed:
            self.problem('final JSON not delivered: stderr remained blocked after the progress flush')
            return
        writer = _TerminalWriter(lambda value: _write_stream(stream, value))
        try:
            writer.write(text + '\n')
            if not writer.flush(timeout):
                self.problem('final JSON delivery timed out; output may be incomplete')
            elif writer.error:
                self.problem(f'final JSON delivery failed: {writer.error}')
        finally:
            writer.close(0)

    def identify(self, run):
        """Name the run on a channel that is not yet bound to its directory."""
        with self._lock:
            self._document['run'] = run

    def bind(self, root, run):
        """Attach a channel created before the run existed to its directory and identity."""
        with self._lock:
            if self.root is not None:
                return
            self.root = Path(root)
            self.path = self.root / 'progress.json'
            self._document['run'] = run
            self._persist()

    def _beat(self):
        while not self._stop.wait(self.seconds_until_heartbeat()):
            with self._lock:
                active = self._document['ended'] is None
            if active:
                self.heartbeat()

    def seconds_until_heartbeat(self):
        with self._lock:
            return max(0.0, self._interval - (self._monotonic() - self._last_publish))

    # -- observations --------------------------------------------------------------------

    def stage(self, name, *, waiting_for='', detail=''):
        with self._lock:
            self._document.update(stage=name, waiting_for=waiting_for, detail=detail)
            text = name + (f': {detail}' if detail else '')
            if waiting_for:
                text += f' · waiting for {waiting_for}'
            self._publish(text)

    def phase(self, phase, pass_number=None, *, waiting_for=None):
        with self._lock:
            self._document.update(phase=phase, **{'pass': pass_number})
            if waiting_for is not None:
                self._document['waiting_for'] = waiting_for
            self._publish(f'phase {phase}' + (f' · pass {pass_number}' if pass_number else ''))

    def attempt_launched(self, reviewer, provider, attempt):
        with self._lock:
            record = self._document['reviewers'].setdefault(reviewer, {'provider': provider, 'attempts': []})
            record['provider'] = provider
            self._records += 1
            record['attempts'].append({
                # `key` is unique within the document: a probe attempt 1 and a pass-1 attempt 1
                # of the same reviewer are different records, and a monitor stays bound to its own.
                'key': f'{reviewer}#{self._records}',
                'attempt': attempt, 'stage': self._document['stage'], 'pass': self._document['pass'],
                'state': 'launching', 'pid': None, 'started_at': None,
                'ended_at': None, 'elapsed_seconds': 0, 'output_observed': False,
                'last_output_age_seconds': None, 'exit_code': None, 'reason': None,
                'diagnostics': None, 'diagnostics_error': None, 'next_action': None,
                'disposition': None,
                # What the reviewer is doing, from its CLI's event stream. 'source' says which
                # signal this attempt has: a parsed stream, or output age alone.
                'activity': {'count': 0, 'latest': None, 'last_seen_age_seconds': None,
                             'recent': [], 'source': 'output-age'}})
            self._publish(f'{self._pass_prefix()}{reviewer} ({provider}) attempt {attempt} launching')

    def attempt_running(self, reviewer, pid, *, key=None):
        """Mark the attempt running; returns its unique key so a monitor stays bound to it."""
        with self._lock:
            record = self._locate(reviewer, key)
            if record is None:
                return None
            record.update(state='running', pid=pid, started_at=iso(self._clock()))
            self._clock_for(reviewer, record)['started'] = self._monotonic()
            self._publish(f"{self._pass_prefix()}{reviewer} attempt {record['attempt']} running"
                          + (f' process pid {pid}' if pid else ''))
            return record['key']

    def attempt_output(self, reviewer, *, key=None):
        with self._lock:
            record = self._locate(reviewer, key)
            if record is None or record['state'] not in ('running', 'launching'):
                return
            record['output_observed'] = True
            self._clock_for(reviewer, record)['output'] = self._monotonic()

    def attempt_activity(self, reviewer, kind, target, *, key=None):
        """One parsed activity event, including permitted source quotations in notes.

        The first activity of an attempt is published at once; later ones at most every
        ACTIVITY_LINE_SECONDS per reviewer, with every heartbeat carrying the latest.
        """
        with self._lock:
            record = self._locate(reviewer, key)
            # Activity read as the process exits still belongs to this attempt.
            if record is None or record['state'] not in ('running', 'launching', 'exited'):
                return
            now = self._monotonic()
            clocks = self._clock_for(reviewer, record)
            activity = record['activity']
            activity['count'] += 1
            activity['source'] = 'stream'
            activity['latest'] = {'kind': kind, 'target': target, 'at': iso(self._clock())}
            activity['recent'] = (activity['recent'] + [activity['latest']])[-ACTIVITY_RECENT:]
            clocks['activity'] = now
            last_line = clocks.get('activity_line')
            if last_line is None or now - last_line >= ACTIVITY_LINE_SECONDS:
                clocks['activity_line'] = now
                self._publish(f"{self._pass_prefix()}{reviewer} {self._activity_text(record)}")

    def attempt_exited(self, reviewer, exit_code, *, key=None):
        with self._lock:
            attempt = self._locate(reviewer, key)
            if attempt is None or attempt['state'] not in ('launching', 'running'):
                return
            self._end(reviewer, attempt)
            attempt.update(state='exited', exit_code=exit_code)
            code = 'without a confirmed exit' if exit_code is None else f'{exit_code}'
            self._publish(f"{self._pass_prefix()}{reviewer} attempt {attempt['attempt']} exited {code} "
                          f"after {hms(attempt['elapsed_seconds'])}; validating its report")

    def attempt_validated(self, reviewer):
        with self._lock:
            attempt = self._latest(reviewer)
            if attempt is None:
                return
            self._end(reviewer, attempt)
            attempt.update(state='validated', disposition='accepted')
            self._publish(f"{self._pass_prefix()}{reviewer} attempt {attempt['attempt']} validated "
                          f"after {hms(attempt['elapsed_seconds'])}")

    def attempt_diagnostics(self, reviewer, path, *, error=None):
        """Where the failed CLI response was retained, or why it could not be."""
        with self._lock:
            attempt = self._latest(reviewer)
            if attempt is None:
                return
            attempt['diagnostics'] = str(path) if path else None
            attempt['diagnostics_error'] = error

    def attempt_failed(self, reviewer, reason, *, next_action):
        with self._lock:
            attempt = self._latest(reviewer)
            if attempt is None:
                return
            self._end(reviewer, attempt)
            attempt.update(state='failed', reason=reason, next_action=next_action, disposition='rejected')
            where = (f" · diagnostics: {attempt['diagnostics']}" if attempt['diagnostics'] else
                     ' · diagnostics could not be saved' +
                     (f" ({attempt['diagnostics_error']})" if attempt['diagnostics_error'] else ''))
            self._publish(f"{self._pass_prefix()}{reviewer} attempt {attempt['attempt']} FAILED after "
                          f"{hms(attempt['elapsed_seconds'])}: {reason}{where} · next: {next_action}")

    def attempt_discarded(self, reviewer):
        with self._lock:
            attempt = self._latest(reviewer)
            if attempt is None or attempt['disposition'] == 'accepted':
                return
            self._end(reviewer, attempt)
            attempt['disposition'] = 'discarded'
            if attempt['state'] in ('launching', 'running', 'exited'):
                attempt['state'] = 'discarded'      # a terminal state, so the record is self-consistent
            self._publish(f"{self._pass_prefix()}{reviewer} attempt {attempt['attempt']} finished after "
                          'the stop; its result is discarded, not accepted')

    def stop_recorded(self, reason, *, still_running=()):
        with self._lock:
            names = sorted(still_running)
            self._document['stopped'] = {'at': iso(self._clock()), 'reason': reason,
                                         'still_running': names}
            self._document['waiting_for'] = ('launched reviewers to finish; results discarded'
                                             if names else '')
            text = f'STOP recorded: {reason}'
            if names:
                text += f" · still running: {', '.join(names)} (results will be discarded, not accepted)"
            self._publish(text)

    def problem(self, text):
        with self._lock:
            self._note_problem(text)
            self._publish(f'visibility problem: {text}')

    def heartbeat(self):
        with self._lock:
            self._publish(self._heartbeat_text())

    def ended(self, outcome, reason=''):
        with self._lock:
            if self._document['ended'] is not None:
                return
            self._document['ended'] = {'at': iso(self._clock()), 'outcome': outcome, 'reason': reason}
            self._document['waiting_for'] = ''
            if outcome == 'failed':
                # The command failed without stopping the run: the recorded next action stands.
                self._publish('command failed' + (f' — {reason}' if reason else ''))
            else:
                self._publish(f'command ended · next action {outcome}' + (f' — {reason}' if reason else ''))
        self._stop.set()

    def snapshot(self):
        with self._lock:
            self._refresh()
            return json.loads(json.dumps(self._document))

    @property
    def problems(self):
        with self._lock:
            if self._writer is not None and self._writer.error:
                # An asynchronous sink failure is evidence too, even with no later publication.
                self._note_problem(f'terminal write failed: {self._writer.error}')
            return list(self._document['problems'])

    # -- internals -----------------------------------------------------------------------

    def _pass_prefix(self):
        number = self._document['pass']
        return f'pass {number} · ' if number else ''

    def _latest(self, reviewer):
        record = self._document['reviewers'].get(reviewer)
        return record['attempts'][-1] if record and record['attempts'] else None

    def _locate(self, reviewer, key=None):
        """The attempt record with this unique key, or the reviewer's latest when key is None."""
        if key is None:
            return self._latest(reviewer)
        record = self._document['reviewers'].get(reviewer)
        return next((a for a in record['attempts'] if a['key'] == key), None) if record else None

    def _clock_for(self, reviewer, attempt):
        return self._attempt_clocks.setdefault(attempt['key'],
                                               {'started': None, 'ended': None, 'output': None})

    @staticmethod
    def _activity_text(record):
        activity = record['activity']
        latest = activity['latest']
        count = activity['count']
        noun = 'activity' if count == 1 else 'activities'
        if latest['kind'] == 'note':
            return f"says: \"{latest['target']}\" ({count} {noun})"
        return f"{latest['kind']} {latest['target']} ({count} {noun})"

    def _end(self, reviewer, attempt):
        clocks = self._clock_for(reviewer, attempt)
        if clocks['ended'] is None:
            clocks['ended'] = self._monotonic()
            attempt['ended_at'] = iso(self._clock())
        self._refresh_attempt(attempt, clocks)

    def _refresh_attempt(self, attempt, clocks):
        now = self._monotonic()
        if clocks['started'] is not None:
            end = clocks['ended'] if clocks['ended'] is not None else now
            attempt['elapsed_seconds'] = round(max(0.0, end - clocks['started']), 1)
        if clocks['output'] is not None and clocks['ended'] is None:
            attempt['last_output_age_seconds'] = round(max(0.0, now - clocks['output']), 1)
        elif clocks['output'] is not None:
            attempt['last_output_age_seconds'] = round(max(0.0, clocks['ended'] - clocks['output']), 1)
        seen = clocks.get('activity')
        if seen is not None:
            end = clocks['ended'] if clocks['ended'] is not None else now
            attempt['activity']['last_seen_age_seconds'] = round(max(0.0, end - seen), 1)

    def _refresh(self):
        for reviewer, record in self._document['reviewers'].items():
            for attempt in record['attempts']:
                self._refresh_attempt(attempt, self._clock_for(reviewer, attempt))

    def _heartbeat_text(self):
        self._refresh()
        parts = []
        stage = self._document['stage']
        if self._document['pass']:
            parts.append(f"pass {self._document['pass']} {stage}".strip())
        elif stage:
            parts.append(stage)
        parts.append(f'{hms(self._monotonic() - self._started)} elapsed')
        for reviewer, record in self._document['reviewers'].items():
            attempt = record['attempts'][-1]
            state = attempt['state']
            text = f"{reviewer} {state}"
            if attempt['attempt'] > 1:
                text += f" (attempt {attempt['attempt']})"
            if state in ('running', 'exited', 'validated', 'failed', 'discarded'):
                text += f" {hms(attempt['elapsed_seconds'])}"
            if state == 'running':
                activity = attempt['activity']
                if activity['latest'] is not None:
                    text += (f" · {activity['latest']['kind']} {activity['latest']['target']} "
                             f"{hms(activity['last_seen_age_seconds'])} ago ({activity['count']} activities)")
                else:
                    text += (' (no activity seen yet; ' +
                             (f"output {hms(attempt['last_output_age_seconds'])} ago)"
                              if attempt['output_observed'] else 'no output yet)'))
            if attempt['disposition'] == 'discarded' and state != 'discarded':
                text += ' (discarded)'
            parts.append(text)
        if self._document['stopped']:
            parts.append('stop recorded')
        if self._document['waiting_for']:
            parts.append(f"waiting for: {self._document['waiting_for']}")
        return ' · '.join(parts)

    def _note_problem(self, text):
        problems = self._document['problems']
        if text not in problems:
            problems.append(text)
            del problems[:-EVENT_LIMIT]

    def _publish(self, text):
        """Refresh derived values, persist the document, print one line. Never raises."""
        now = self._clock()
        self._last_publish = self._monotonic()
        self._document['observed_at'] = iso(now)
        self._document['sequence'] += 1
        self._document['events'].append({'at': iso(now), 'text': text})
        del self._document['events'][:-EVENT_LIMIT]
        self._refresh()
        persisted = self._persist()
        line = PREFIX + datetime.fromtimestamp(now).strftime('%H:%M:%S') + ' ' + text
        if not persisted:
            line += ' · [visibility: progress.json could not be written; run state is unaffected]'
        if self._writer is not None:
            if not self._writer.write(line):
                self._note_problem('terminal output backed up; progress lines dropped (run state is unaffected)')
            elif self._writer.error:
                self._note_problem(f'terminal write failed: {self._writer.error}')
            return
        try:
            self._sink(line)
        except Exception as exc:      # the terminal is best-effort; the run must not depend on it
            self._note_problem(f'terminal write failed: {exc}')

    def _persist(self):
        if self.root is None:
            return True               # not bound to a run yet: terminal only
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(dir=self.root, prefix='.write-')
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                    json.dump(self._document, stream, sort_keys=True)
                replace_retrying(temporary, self.path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            return True
        except OSError as exc:
            self._note_problem(f'progress.json could not be written: {exc}')
            return False
