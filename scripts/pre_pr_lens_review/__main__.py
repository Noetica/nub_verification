"""Local review command interface; judgement and edits remain in the authoring session."""
import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import sys

from .cycle import BoundaryError, Controller, ReviewError, digest, INTERRUPTED_PROVIDER_REASON
from .progress import NullProgress, Progress
from .snapshot import capture, SnapshotError, git


def read(path, expected=dict):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, expected):
        raise ReviewError(f'Expected a JSON {expected.__name__} in {path}')
    return value


def prestart_progress(args):
    """Observe a new run's capture before its directory or identity exists (terminal only)."""
    if not getattr(args, 'progress', False):
        return NullProgress()
    progress = Progress(None, run='pending', command=args.command).start()
    progress.stage('start', detail='capturing the caller tree and freezing the run inputs; '
                                   'the run identity follows')
    return progress


def attach_progress(controller, args, progress=None):
    """Enable the additive observation channel for this command, or leave it disabled.

    The first update identifies the run and command before any lengthy work begins; a
    channel opened by prestart_progress is bound to the run instead of replaced. A resumed
    command's channel stays terminal-only until Controller.locked() binds it. The caller
    retains that lock through final publication and cleanup, so a refused contender
    never overwrites the live command's progress.json.
    """
    if not getattr(args, 'progress', False):
        return NullProgress()
    if progress is None or not progress.enabled:
        progress = Progress(None, run=controller.state['run'], command=args.command).start()
    progress.identify(controller.state['run'])
    controller.progress = progress
    progress.stage(args.command, detail=f"run {controller.state['run']} at {controller.root} · recorded phase "
                                        f"{controller.state['phase']}")
    return progress


def emit(output, progress, *, stream=None, outcome=None, reason='', indent=2):
    """Record the end and deliver JSON; progress-mode output has a bounded wait."""
    if progress.enabled:
        progress.ended(outcome if outcome is not None else output.get('action', 'done'), reason)
        terminal_flushed = progress.flush()
        if not terminal_flushed:
            progress.discard_pending()
        progress.seal()
        problems = progress.problems
        if problems:
            output['observability_problems'] = problems
        progress.result(json.dumps(output, indent=indent), stream if stream is not None else sys.stdout,
                        terminal_flushed=terminal_flushed)
        return
    print(json.dumps(output, indent=indent), file=stream)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--progress', action='store_true',
                        help='publish runner observations to stderr (prefixed lines) and to '
                             'progress.json beside the run state; adds observability_problems '
                             'to the JSON result only if progress reporting fails')
    commands = parser.add_subparsers(dest='command', required=True)
    snapshot = commands.add_parser('snapshot', help='Capture source without changing the real index')
    snapshot.add_argument('--repo', required=True)
    # Named --base for historical reasons but it takes the target: capture derives the
    # review base as the merge base of HEAD and this commit.
    snapshot.add_argument('--base', required=True, metavar='TARGET',
                          help='target commit, normally origin/main; the merge base is derived')
    snapshot.add_argument('--destination', required=True)
    start = commands.add_parser('start')
    start.add_argument('--repo', required=True)
    start.add_argument('--base', required=True, metavar='TARGET',
                       help='target commit, normally origin/main; the merge base is derived')
    start.add_argument('--state', required=True)
    start.add_argument('--intent', required=True)
    start.add_argument('--checks', required=True)
    start.add_argument('--config', required=True)
    run = commands.add_parser('run', help='The normal entry point: start or resume a run, then '
                              'sequence preflight, the fixture probe and permitted reviews, '
                              'returning at the next author/human boundary')
    run.add_argument('--state', help='saved run directory; new runs default to temporary storage grouped by Jira key')
    for name in ('repo', 'intent', 'checks', 'config'):
        run.add_argument('--' + name, help='fresh inputs enable automatic recovery and compatibility checks')
    run.add_argument('--base', metavar='TARGET', help='pinned target for a new run or compatibility check')
    observer = commands.add_parser('observe', help='Read-only view of a run from another terminal '
                                   'or agent: no lock, no writes, no tree validation')
    observer.add_argument('--state', required=True)
    observer.add_argument('--follow', action='store_true',
                          help='keep printing runner events and stale reminders until the '
                               'runner command ends')
    observer.add_argument('--stay', action='store_true',
                          help='with --follow: keep following across runner commands instead of '
                               'exiting when the watched command ends')
    observer.add_argument('--window', action='store_true',
                          help='with --follow: open a terminal window running the observer for '
                               'the developer and return; prints the command if no window can be opened')
    observer.add_argument('--idle-timeout', type=float, default=None,
                          help='with --follow: exit after this many seconds without a new runner event')
    for name in ('status', 'preflight', 'probe', 'review', 'triage', 'answer', 'sensitive',
                 'begin-fix', 'finish-fix', 'handoff', 'compare-pr-head'):
        command = commands.add_parser(name)
        command.add_argument('--state', required=True)
        if name in ('triage', 'answer', 'sensitive'):
            command.add_argument('--file', required=True)
        if name == 'finish-fix':
            command.add_argument('--checks', required=True)
            command.add_argument('--token', required=True)
    args = parser.parse_args(argv)
    if args.progress or (args.command == 'observe' and args.follow):
        # Native Windows consoles support Unicode, but redirected/legacy streams may
        # otherwise inherit cp1252. Ordinary JSON-only invocations keep their encoding.
        for stream in (sys.stdout, sys.stderr):
            if callable(getattr(stream, 'reconfigure', None)):
                stream.reconfigure(encoding='utf-8', errors='replace')
    controller = None
    progress = NullProgress()
    command_lock = ExitStack()
    command_finished = False
    try:
        if args.command == 'snapshot':
            output = capture(Path(args.repo), args.base, Path(args.destination))
        elif args.command == 'observe':
            from .observe import follow, observe, open_window
            if args.window:
                outcome = open_window(args.state)
                print(json.dumps(outcome, indent=2))
                return 0 if outcome['window'] == 'opened' else 2
            try:
                if args.follow:
                    return follow(args.state, out=lambda line: print(line, flush=True),
                                  stay=args.stay, idle_timeout=args.idle_timeout)
                output = observe(args.state)
            except KeyboardInterrupt:
                # Detaching a read-only observer changes nothing and is not a stop.
                print('observer detached; the run is unchanged', flush=True)
                return 0
            print(json.dumps(output, indent=2))
            return 2 if output['recorded_phase'] is None and output['runner'] is None else 0
        elif args.command == 'start':
            progress = prestart_progress(args)
            controller = Controller.start(args.state, args.repo, args.base, read(args.intent),
                                          read(args.checks), read(args.config))
            progress = attach_progress(controller, args, progress)
            command_lock.enter_context(controller.locked())
            output = controller.summary()
        elif args.command == 'run':
            from .providers import ProviderRunner
            start_inputs = ('repo', 'base', 'intent', 'checks', 'config')
            supplied = [name for name in start_inputs if getattr(args, name) is not None]
            if supplied and len(supplied) != len(start_inputs):
                missing = [name for name in start_inputs if name not in supplied]
                raise ReviewError('A new run needs --repo, --base, --intent, --checks and --config; '
                                  'missing: ' + ', '.join('--' + name for name in missing))
            progress = prestart_progress(args)
            controller, resumed, recovery = command_lock.enter_context(Controller.open_run(
                args.state, args.repo, args.base, read(args.intent) if args.intent else None,
                read(args.checks) if args.checks else None, read(args.config) if args.config else None))
            progress = attach_progress(controller, args, progress)
            command_lock.enter_context(controller.locked())
            if resumed:
                progress.stage('resume', detail='existing run; frozen inputs govern' +
                               (', supplied inputs are compatible' if supplied else ''))
            elif recovery:
                progress.stage('recovery', detail=recovery + f'; fresh run at {controller.root}')
            runner = ProviderRunner(controller.state['config'], controller.state['repository'],
                                    controller.root, progress)
            permitted = False
            if controller.next_action() == 'review':
                with controller.locked():
                    # Decide under the lock, on the reloaded record: a stop or answer recorded by
                    # another controller a moment ago must not be followed by provider work.
                    pending = [e['path'] for e in controller.current['snapshot']['sensitive']
                               if e not in controller.state['exceptions']]
                    if pending and controller.next_action() == 'review':
                        # A human boundary, not automatic work: no provider is launched or paid for.
                        raise ReviewError('Sensitive paths need exact human exceptions before review: '
                                          + ', '.join(pending) + '. Record them with `sensitive --state <dir> '
                                          '--file <json>` (entries copied from pending_sensitive in status), then run again.')
                    permitted = controller.next_action() == 'review'
                    if permitted:
                        progress.stage('preflight', detail='resolving reviewer CLIs and versions')
                        preflight = runner.preflight()
                        previous = controller.state.get('preflight')
                        if previous and previous['runtime_digest'] != preflight['runtime_digest']:
                            raise ReviewError('Reviewer command or CLI version changed since first preflight')
                        controller.state['preflight'] = preflight
                        controller._save()
                        probe = controller.state.get('provider_probe')
                        if not probe or probe['config_digest'] != digest(controller.state['config']):
                            progress.stage('probe', detail='authenticated fixture probe on generated source',
                                           waiting_for='sonnet, luna, composer')
                            try:
                                controller.state['provider_probe'] = runner.probe()
                            except BoundaryError as exc:
                                controller._set_stopped(str(exc))
                                controller._persist()
                                raise
                            controller._save()
                        else:
                            progress.stage('probe', detail='valid probe already recorded for the frozen '
                                                           'configuration; not repeated')
                    else:
                        progress.stage('resume', detail='recorded state no longer permits automatic work')
                # Nested operations reuse command ownership and recheck the boundary.
                # Fixing, triage, human waits and stops return control.
                while permitted and controller.next_action() == 'review':
                    progress.stage('review')
                    controller.review(runner)
            output = controller.summary()
            output['resumed'] = resumed
            if recovery:
                output['recovery'] = recovery
        else:
            controller = Controller(args.state)
            progress = attach_progress(controller, args)
            try:
                if args.command != 'status' or not controller._historical():
                    command_lock.enter_context(controller.locked())
            except ReviewError:
                # Historical status remains a read-only inspection, even while the new
                # owner is busy. Its terminal-only channel cannot replace old evidence.
                if args.command != 'status' or not controller._historical():
                    raise
            if args.command in ('preflight', 'probe', 'review'):
                from .providers import ProviderRunner
                runner = ProviderRunner(controller.state['config'], controller.state['repository'],
                                        controller.root, progress)
                with controller.locked():
                    progress.stage('preflight', detail='resolving reviewer CLIs and versions')
                    preflight = runner.preflight()
                    previous = controller.state.get('preflight')
                    if previous and previous['runtime_digest'] != preflight['runtime_digest']:
                        raise ReviewError('Reviewer command or CLI version changed since first preflight')
                    controller.state['preflight'] = preflight
                    controller._save()
                    if args.command == 'probe':
                        progress.stage('probe', detail='authenticated fixture probe on generated source',
                                       waiting_for='sonnet, luna, composer')
                        try:
                            controller.state['provider_probe'] = runner.probe()
                        except BoundaryError as exc:
                            controller._set_stopped(str(exc))
                            controller._persist()
                            raise
                        controller._save()
                if args.command == 'review':
                    probe = controller.state.get('provider_probe')
                    if not probe or probe['config_digest'] != digest(controller.state['config']):
                        raise ReviewError('Authenticated provider fixture probe must pass before reviewing caller source')
                    progress.stage('review')
                    controller.review(runner)
                    output = controller.summary()
                elif args.command == 'probe':
                    output = controller.state['provider_probe']
                else:
                    output = preflight
            elif args.command == 'triage':
                controller.triage(read(args.file, list))
                output = controller.summary()
            elif args.command == 'answer':
                controller.answer(read(args.file))
                output = controller.summary()
            elif args.command == 'sensitive':
                answer = read(args.file)
                controller.approve_sensitive(answer['entries'], answer['text'])
                output = controller.summary()
            elif args.command == 'begin-fix':
                output = {'token': controller.begin_fix(), 'action': 'fix',
                          'batch': controller.state['fix_batch']}
            elif args.command == 'finish-fix':
                controller.finish_fix(read(args.checks), args.token)
                output = controller.summary()
            elif args.command in ('handoff', 'compare-pr-head'):
                if args.command == 'compare-pr-head':
                    # Compare before handoff records readiness. handoff() saves phase
                    # 'ready', so comparing afterwards left a ready run recorded even when
                    # the fetched head did not match the handed-off tree.
                    actual = git(Path(controller.state['repository']), 'rev-parse',
                                 '--verify', 'FETCH_HEAD^{tree}').decode().strip()
                    if actual != controller.head['tree']:
                        raise ReviewError('Fetched PR head differs from the handed-off tree')
                output = controller.handoff()
                if args.command == 'compare-pr-head':
                    output['pr_head_matches'] = True
            else:
                output = controller.status()
        command_finished = True
        reason = controller.waiting()[1] if controller is not None and progress.enabled else ''
        # preflight/probe results carry no action; the run's real next action is still known.
        outcome = output.get('action') or (controller.next_action() if controller is not None else 'done')
        emit(output, progress, outcome=outcome, reason=reason)
        return 0 if output.get('action') != 'stop' else 2
    except BoundaryError as exc:
        # unchanged() persists the stop before raising. Keep the recorded findings and
        # partial peer evidence visible through the CLI, as with a stop during review.
        output = controller.summary()
        output.update(action='stop', reason=str(exc))
        emit(output, progress, stream=sys.stderr, outcome='stop', reason=str(exc))
        return 2
    except KeyboardInterrupt:
        # Stop interrupted provider work, not an inspection or delivery of a saved result.
        # `action: stop` ends this CLI command; recorded_phase reports the persisted run.
        reason = INTERRUPTED_PROVIDER_REASON
        if controller is None:
            # Through emit(): a pre-start channel may already be publishing, and nothing may
            # follow the result on its stream.
            text = ('Command cancelled before its controller was available. '
                    'Check for saved state before retrying.')
            emit({'action': 'stop', 'interrupted': True, 'reason': text}, progress, stream=sys.stderr,
                 outcome='interrupted', reason=text)
            return 2
        try:
            if not command_finished and args.command in ('preflight', 'probe', 'review', 'run'):
                with controller.locked():
                    if controller.state['phase'] not in ('stopped', 'ready'):
                        controller._set_stopped(reason)
                        controller._save()
            controller.state = controller._read()
            phase = controller.state['phase']
            output = controller.summary()
            output.update(action='stop', interrupted=True, recorded_phase=phase,
                          handoff_eligible=False,
                          reason=controller.state['reason'] if phase == 'stopped' else
                                 'Command cancelled; saved run state preserved. '
                                 'Inspect status before continuing; this is not a handoff.')
        except (ReviewError, SnapshotError, OSError, ValueError, KeyError) as exc:
            output = {'action': 'stop', 'interrupted': True,
                      'reason': f'Interrupted; could not establish the saved run state: {exc}'}
        emit(output, progress, stream=sys.stderr, outcome='interrupted', reason=output['reason'])
        return 2
    except (ReviewError, SnapshotError, OSError, ValueError, KeyError) as exc:
        # Compact, as before this channel existed: the failure contract is unchanged. The
        # observation distinguishes a failed command from a stopped run: unless the run's
        # recorded phase is 'stopped', its recorded next action still stands.
        outcome, reason = 'failed', str(exc)
        if controller is not None:
            try:
                phase = controller._read()['phase']
            except ReviewError:
                phase = None
            if phase == 'stopped':
                outcome = 'stop'
            else:
                try:
                    reason = f'{exc} · recorded next action {controller.next_action()}: {controller.waiting()[1]}'
                except Exception:
                    # Diagnostic enrichment is optional; retain the original failure reason.
                    pass
        emit({'action': 'stop', 'reason': str(exc)}, progress, stream=sys.stderr,
             outcome=outcome, reason=reason, indent=None)
        return 2
    finally:
        try:
            progress.close()
        finally:
            command_lock.close()


if __name__ == '__main__':
    sys.exit(main())
