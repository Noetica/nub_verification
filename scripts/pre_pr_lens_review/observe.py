"""Read-only observation of a run from another terminal or agent.

Observation never takes the controller lock, never writes under the run directory or the
ownership registry, never validates the caller tree and never consumes an attempt. It reads
state.json (authoritative, integrity-checked) and progress.json (the runner's last
observation) and reports what each supports. A recorded ready phase is still evidence
only: `handoff_eligible` is always False here, and only `handoff` can authorise a tree.

Freshness is judged from the runner's last wall-clock update, not from a stored label:
  live         a runner command updated within STALE_AFTER_SECONDS
  stale        a runner command was active but has not updated for longer; activity is
               unconfirmed - not proof of a hang, and never a reason to restart anything
  ended        the last runner command recorded its end (author/human wait or stop)
  unavailable  no readable observation: older run, no command observed yet, or damaged file
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

from .cycle import Controller, ReviewError
from .progress import (ACTIVITY_RECENT, EVENT_LIMIT, PREFIX, STALE_AFTER_SECONDS, STALE_REMINDER_SECONDS, hms, iso,
                       parse_iso)
from .snapshot import SnapshotError

STALE_WARNING = 'Updates stale—activity unconfirmed'
READ_ATTEMPTS = 5


def _local(stamp):
    try:
        return time.strftime('%H:%M:%S', time.localtime(parse_iso(stamp)))
    except (TypeError, ValueError):
        return str(stamp)


def read_json(path, attempts=READ_ATTEMPTS):
    """Read a JSON file a writer may be replacing: (document, problem). Absent is (None, None)."""
    problem = None
    for attempt in range(attempts):
        try:
            return json.loads(path.read_text(encoding='utf-8')), None
        except FileNotFoundError:
            return None, None
        except (OSError, ValueError) as exc:
            problem = f'{type(exc).__name__}: {exc}'
            if attempt + 1 < attempts:
                time.sleep(0.05)
    return None, problem


def _timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        return math.isfinite(parse_iso(value))
    except (TypeError, ValueError, OverflowError, OSError):
        return False


def _integer(value):
    return type(value) is int and value >= 0


def _duration(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def _optional(check):
    return lambda value: value is None or check(value)


def _shape(value, fields):
    return isinstance(value, dict) and all(key in value and check(value[key])
                                          for key, check in fields.items())


def _activity(value):
    event = lambda item: _shape(item, {'kind': lambda x: isinstance(x, str),
                                      'target': lambda x: isinstance(x, str), 'at': _timestamp})
    return (_shape(value, {
        'count': _integer, 'latest': _optional(event),
        'last_seen_age_seconds': _optional(_duration),
        'recent': lambda x: isinstance(x, list) and len(x) <= ACTIVITY_RECENT and all(map(event, x)),
        'source': lambda x: x in ('stream', 'output-age'),
    }) and ((value['count'] == 0 and value['latest'] is None and not value['recent']) or
            (value['count'] > 0 and value['latest'] is not None and value['recent'] and
             value['recent'][-1] == value['latest'] and len(value['recent']) <= value['count'])))


def _attempt(value):
    text = lambda x: isinstance(x, str)
    if not _shape(value, {
        'key': lambda x: text(x) and bool(x),
        'attempt': lambda x: _integer(x) and x > 0,
        'stage': text, 'pass': _optional(lambda x: _integer(x) and x > 0),
        'state': lambda x: x in ('launching', 'running', 'exited', 'validated', 'failed', 'discarded'),
        'pid': _optional(lambda x: _integer(x) and x > 0),
        'started_at': _optional(_timestamp), 'ended_at': _optional(_timestamp),
        'elapsed_seconds': _duration, 'output_observed': lambda x: type(x) is bool,
        'last_output_age_seconds': _optional(_duration),
        'exit_code': _optional(lambda x: type(x) is int),
        'reason': _optional(text), 'diagnostics': _optional(text),
        'diagnostics_error': _optional(text), 'next_action': _optional(text),
        'disposition': lambda x: x in (None, 'accepted', 'rejected', 'discarded'),
        'activity': _activity,
    }):
        return False
    if value['state'] == 'running':
        return value['started_at'] is not None and value['ended_at'] is None
    if value['state'] == 'launching':
        return value['started_at'] is None and value['ended_at'] is None
    return value['ended_at'] is not None


def _well_formed(document):
    """Validate the emitted observation shape, including nested attempt evidence."""
    text = lambda x: isinstance(x, str)
    texts = lambda x: isinstance(x, list) and all(map(text, x))
    event = lambda x: _shape(x, {'at': _timestamp, 'text': text})
    reviewer = lambda x: _shape(x, {'provider': text, 'attempts': lambda a:
                                    isinstance(a, list) and bool(a) and all(map(_attempt, a))})
    if not _shape(document, {
        'version': lambda x: type(x) is int and x == 1,
        'run': text, 'command': text, 'pid': lambda x: _integer(x) and x > 0,
        'started_at': _timestamp, 'observed_at': _timestamp, 'sequence': _integer,
        'stage': text, 'detail': text,
        'phase': lambda x: x in (None, 'review', 'triage', 'fixing', 'ready', 'stopped'),
        'pass': _optional(lambda x: _integer(x) and x > 0), 'waiting_for': text,
        'events': lambda x: isinstance(x, list) and len(x) <= EVENT_LIMIT and all(map(event, x)),
        'problems': lambda x: texts(x) and len(x) <= EVENT_LIMIT,
        'reviewers': lambda x: isinstance(x, dict) and all(text(k) and reviewer(v) for k, v in x.items()),
        'ended': _optional(lambda x: _shape(x, {'at': _timestamp, 'outcome': text, 'reason': text})),
        'stopped': _optional(lambda x: _shape(x, {'at': _timestamp, 'reason': text, 'still_running': texts})),
    }):
        return False
    keys = [a['key'] for r in document['reviewers'].values() for a in r['attempts']]
    return document['sequence'] >= len(document['events']) and len(keys) == len(set(keys))


def observe(root, *, clock=time.time):
    root = Path(root).resolve()
    problems = []
    result = {'observation_only': True, 'handoff_eligible': False, 'observed_at': iso(clock()),
              'state_dir': str(root), 'run': None, 'recorded_phase': None, 'recorded_action': None,
              'recorded_reason': None, 'waiting_for': None, 'ownership': 'unknown',
              'freshness': 'unavailable', 'runner': None, 'stage': None, 'pass': None,
              'reviewers': {}, 'passes': [], 'stopped': None, 'events': [], 'note': None,
              'problems': problems}
    if not root.is_dir():
        problems.append(f'run directory missing: {root}')
        return result
    state = None
    controller = failure = None
    for attempt in range(READ_ATTEMPTS):
        # The authoritative file gets the same bounded retry as progress.json: a Windows
        # reader can collide with the controller's replace and must not call a busy run damaged.
        try:
            controller = Controller(root)      # integrity-checked read; no lock, no write
            break
        except ReviewError as exc:
            failure = exc
            if attempt + 1 < READ_ATTEMPTS:
                time.sleep(0.05)
    try:
        if controller is None:
            raise failure
        state = controller.state
        result.update(run=state['run'], recorded_phase=state['phase'],
                      recorded_action=controller.next_action(),
                      recorded_reason=state['reason'] or None,
                      waiting_for=controller.waiting()[1],
                      passes=[{'number': p['number'], 'reviewers': p['reviewers'],
                               'complete': p['complete'], 'attempts': dict(sorted(p['attempts'].items())),
                               'results': sorted(p['results']), 'errors': dict(sorted(p['errors'].items()))}
                              for p in state['passes']])
        try:
            registry = Controller.registry(Path(state['repository']), create=False)
            owner = json.loads(registry.read_text(encoding='utf-8'))['root']
            result['ownership'] = 'current' if owner == str(root) else 'historical'
        except (OSError, ValueError, KeyError, SnapshotError) as exc:
            problems.append('ownership unknown: registry record unreadable or caller repository '
                            f'unavailable ({type(exc).__name__})')
    except ReviewError as exc:
        problems.append(f'state.json unreadable: {exc}')
    document, problem = read_json(root / 'progress.json')
    if problem:
        problems.append(f'progress.json unreadable: {problem}')
        return result
    if document is None:
        result['note'] = ('no live observation recorded: the run predates progress publication, '
                          'or no command has run with --progress yet')
        return result
    if not _well_formed(document):
        problems.append('progress.json unreadable: unexpected document shape or version')
        return result
    if state is not None and document.get('run') != state['run']:
        problems.append(f"progress.json belongs to run {document.get('run')}, not {state['run']}")
        return result
    try:
        age = clock() - parse_iso(document['observed_at'])
    except ValueError as exc:
        problems.append(f'progress.json unreadable: bad observed_at ({exc})')
        return result
    clock_ahead = age < 0
    age = max(0.0, age)
    ended = document.get('ended')
    stopped = document.get('stopped')
    if state is not None and (stopped or (ended or {}).get('outcome') == 'stop') and state['phase'] != 'stopped':
        # The runner persists its stop before announcing it, but a reader that landed between an
        # older state read and the announcement re-reads once rather than reporting a mixed view.
        try:
            controller = Controller(root)
            state = controller.state
            result.update(recorded_phase=state['phase'], recorded_action=controller.next_action(),
                          recorded_reason=state['reason'] or None, waiting_for=controller.waiting()[1])
        except ReviewError:
            # Keep the first valid state; the mismatch warning below still reports uncertainty.
            pass
        if state['phase'] != 'stopped':
            problems.append('progress.json records a stop that state.json does not yet show; '
                            'a transition may be in flight, re-read before acting')
    result['runner'] = {'command': document.get('command'), 'pid': document.get('pid'),
                        'started_at': document.get('started_at'),
                        'last_update_at': document['observed_at'], 'age_seconds': round(age, 1),
                        'sequence': document.get('sequence'), 'ended': ended,
                        'problems': document.get('problems', [])}
    result['freshness'] = 'ended' if ended else 'stale' if clock_ahead or age >= STALE_AFTER_SECONDS else 'live'
    reviewers = json.loads(json.dumps(document['reviewers']))
    now = clock()
    for record in reviewers.values():
        for attempt in record.get('attempts', []):
            # Recorded values are as of the runner's last update. An attempt whose end is
            # not recorded has a known start, so its elapsed time is measured from that
            # start, and the runner's silence is added to its last-output age. Neither
            # says whether the process is alive; both are simply current.
            if attempt.get('started_at') and not attempt.get('ended_at'):
                try:
                    attempt['elapsed_seconds'] = round(max(attempt['elapsed_seconds'],
                                                          now - parse_iso(attempt['started_at'])), 1)
                except (TypeError, ValueError):
                    continue
                if attempt.get('output_observed') and attempt.get('last_output_age_seconds') is not None:
                    attempt['last_output_age_seconds'] = round(attempt['last_output_age_seconds'] + age, 1)
                activity = attempt.get('activity')
                if isinstance(activity, dict) and activity.get('last_seen_age_seconds') is not None:
                    activity['last_seen_age_seconds'] = round(activity['last_seen_age_seconds'] + age, 1)
    result.update(stage=document.get('stage'), stopped=document.get('stopped'),
                  reviewers=reviewers, events=document.get('events', []),
                  **{'pass': document.get('pass')})
    if result['waiting_for'] is None or not ended:
        result['waiting_for'] = document.get('waiting_for') or result['waiting_for']
    if result['freshness'] == 'stale':
        timing = ('the runner timestamp is ahead of this observer clock; update age is unconfirmed'
                  if clock_ahead else f'the runner last updated {hms(age)} ago')
        result['note'] = (f'{STALE_WARNING}: {timing}. Recorded '
                          'outcomes are retained; whether the runner or its reviewers are alive '
                          'is not established by this observation.')
    return result


def follow(root, *, out=print, clock=time.time, sleep=time.sleep, poll=1.0, ticks=None,
           stay=False, idle_timeout=None):
    """Print new runner events as they appear; while the runner is silent, remind.

    The reminders confirm only that this observer is operating. Age is recomputed from the
    wall clock on every tick, so an observer that was suspended reassesses on resumption.
    Returns when a command it watched live records its end, unless `stay` keeps it following
    across commands (the observer window). An observer attached after the last command had
    already ended waits for the next one rather than exiting at once. Window
    observers also close after ``idle_timeout`` seconds without a new runner
    event; stale reminders do not reset that timer.
    """
    seen = None
    identity = None
    reattached = False
    watched_live = False          # saw this command before it ended: its end may end the watch
    announced_end = None          # identity whose end has already been printed
    stale_since = None
    last_reminder = None
    said_unavailable = False
    last_activity = clock()
    while True:
        snapshot = observe(root, clock=clock)
        runner = snapshot['runner']
        stamp = time.strftime('%H:%M:%S', time.localtime(clock()))
        if runner is not None:
            current = (runner.get('pid'), runner.get('started_at'), runner.get('command'))
            if seen is not None and (current != identity or (runner['sequence'] or 0) < seen):
                # A replacement command started (fresh document, sequence from 1): re-attach
                # rather than waiting for its sequence to pass the dead command's.
                out(f"{PREFIX}{stamp} new runner command {runner['command']} (pid {runner['pid']}) replaced "
                    'the previous observation; showing its retained events')
                seen = None
                reattached = True
                watched_live = False
                stale_since = last_reminder = None
                last_activity = clock()
            identity = current
            if snapshot['freshness'] != 'ended':
                watched_live = True
        if runner is None:
            if not said_unavailable:
                text = snapshot['note'] or '; '.join(snapshot['problems']) or 'no observation available'
                phase = snapshot['recorded_phase']
                out(f'{PREFIX}{stamp} {text}' + (f' · recorded phase {phase}' if phase else '')
                    + ' · observation only; waiting for a runner command with --progress')
                said_unavailable = True
        else:
            was_unavailable = said_unavailable
            said_unavailable = False
            if snapshot['freshness'] != 'stale' and stale_since is not None:
                out(f'{PREFIX}{stamp} runner updates resumed after {hms(clock() - stale_since)}; '
                    'stale warning cleared')
                stale_since = last_reminder = None
            sequence = runner['sequence'] or 0
            if seen is None or sequence > seen:
                last_activity = clock()
                events = snapshot['events']
                if seen is None:
                    # Attaching to an existing command shows its latest event. An observer
                    # waiting before startup (or for a replacement) replays the retained tail.
                    new = events if reattached or was_unavailable else events[-1:]
                    reattached = False
                    out(f"{PREFIX}{stamp} observing run {snapshot['run']} · runner command "
                        f"{runner['command']} · freshness {snapshot['freshness']} · recorded phase "
                        f"{snapshot['recorded_phase']} · observation only")
                else:
                    delta = sequence - seen
                    if delta > len(events):
                        # The document keeps a bounded tail; say what this observer missed
                        # rather than silently skipping it.
                        out(f'{PREFIX}{stamp} {delta - len(events)} earlier runner event(s) not shown; '
                            f'progress.json retains only the last {len(events)}')
                    new = events[-delta:] if delta <= len(events) else events
                for event in new:
                    out(f"{PREFIX}{_local(event['at'])} {event['text']}")
                seen = sequence
            if snapshot['freshness'] == 'stale':
                now = clock()
                if stale_since is None or now < last_reminder or now - last_reminder >= STALE_REMINDER_SECONDS:
                    out(f"{PREFIX}{stamp} {snapshot['note']} This observer is running "
                        f"(runner pid {runner['pid']}, recorded phase {snapshot['recorded_phase']}) "
                        'and starts nothing.')
                    stale_since = stale_since or now
                    last_reminder = now
            else:
                if snapshot['freshness'] == 'ended' and announced_end != identity:
                    announced_end = identity
                    ended = runner['ended']
                    leaving = watched_live and not stay
                    tail = ' · observer exiting' if leaving else ' · waiting for the next runner command. This window observes only and may be closed'
                    if ended.get('outcome') == 'failed':
                        out(f"{PREFIX}{stamp} runner command {runner['command']} failed"
                            + (f" — {ended['reason']}" if ended.get('reason') else '')
                            + f" · recorded phase {snapshot['recorded_phase']}, recorded next action "
                            f"{snapshot['recorded_action']}" + tail)
                    else:
                        out(f"{PREFIX}{stamp} runner command {runner['command']} ended · next action "
                            f"{ended['outcome']}" + (f" — {ended['reason']}" if ended.get('reason') else '')
                            + f" · waiting for: {snapshot['waiting_for']}" + tail)
                    if leaving:
                        return 0
        if idle_timeout is not None and clock() - last_activity >= idle_timeout:
            out(f'{PREFIX}{stamp} no new runner events for {hms(idle_timeout)}; '
                'observer window closing. The review run is unchanged')
            return 0
        if ticks is not None:
            ticks -= 1
            if ticks <= 0:
                return 0
        sleep(poll)


def observer_command(state):
    """The follow observer as an argument vector, runnable from anywhere."""
    script = Path(__file__).resolve().parents[1] / 'pre-pr-lens-review.py'
    # --stay follows the next command; ten minutes of silence closes the window.
    return [sys.executable, str(script), 'observe', '--follow', '--stay',
            '--idle-timeout', '600', '--state', str(Path(state).resolve())]


def open_window(state, *, platform=None, which=shutil.which, popen=subprocess.Popen, run=subprocess.run):
    """Open a terminal window running the follow observer, so the developer sees the feed
    without pasting anything. Best effort: reports `unavailable` with the command to paste
    when no terminal can be opened here (a headless host, an unknown emulator).
    """
    command = observer_command(state)
    platform = platform or ('nt' if os.name == 'nt' else sys.platform)
    try:
        if platform == 'nt':
            popen(command, creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0))
            return {'window': 'opened', 'via': 'new console', 'command': command}
        if platform == 'darwin':
            # A .command file opened with Terminal needs no Automation consent (osascript's
            # "do script" does, and stalls on the consent dialog); it is left in the temp
            # directory so Terminal can still read it after this process has returned.
            handle, path = tempfile.mkstemp(prefix='lens-review-observer-', suffix='.command')
            with os.fdopen(handle, 'w', encoding='utf-8') as script:
                script.write('#!/bin/sh\nexec ' + ' '.join(shlex.quote(a) for a in command) + '\n')
            os.chmod(path, 0o700)
            result = run(['open', '-a', 'Terminal', path], capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                return {'window': 'opened', 'via': 'Terminal', 'command': command, 'script': path}
            return {'window': 'unavailable', 'reason': (result.stderr or 'open failed').strip(),
                    'command': command}
        for emulator, prefix in (('x-terminal-emulator', ['-e']), ('gnome-terminal', ['--']),
                                 ('konsole', ['-e']), ('xterm', ['-e'])):
            if which(emulator):
                popen([emulator, *prefix, *command])
                return {'window': 'opened', 'via': emulator, 'command': command}
        return {'window': 'unavailable', 'reason': 'no terminal emulator found', 'command': command}
    except (OSError, subprocess.SubprocessError) as exc:
        return {'window': 'unavailable', 'reason': f'{type(exc).__name__}: {exc}', 'command': command}
