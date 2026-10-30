"""Durable review progression. The author supplies evidence and edits, never readiness."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager, nullcontext
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import uuid

if os.name == 'nt':
    import msvcrt
else:
    import fcntl

from .progress import NullProgress, replace_retrying
from .snapshot import capture, content_digest, current_branch, SnapshotError, git

SCHEDULE = (['sonnet', 'luna', 'composer'], ['opus', 'sol', 'grok'], ['grok'], ['grok'])
PROVIDERS = {'sonnet': 'claude', 'opus': 'claude', 'luna': 'codex', 'sol': 'codex',
             'composer': 'cursor', 'grok': 'cursor'}
MATERIAL = {'blocker', 'major'}
CAPACITY_EXHAUSTED = 'Review capacity exhausted with unresolved findings'
INTERRUPTED_PROVIDER_REASON = 'Interrupted provider work; run will validate retained evidence before resuming'


class ReviewError(RuntimeError):
    pass


class BoundaryError(ReviewError):
    """A run boundary cannot be re-established: stop without an operational retry."""


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


@contextmanager
def file_lock(path):
    """Hold one nonblocking controller lock; the OS releases it on process exit."""
    with path.open('a+b') as lock:
        if os.name == 'nt':
            # Windows locks byte ranges. Keep a byte present and always lock offset 0.
            if path.stat().st_size == 0:
                lock.write(b'\0')
                lock.flush()
            lock.seek(0)
        try:
            if os.name == 'nt':
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ReviewError(f'Another controller may be operating on this run, or the lock '
                              f'is unavailable at {path}: {exc}') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.write-')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
        # Bounded retry: a concurrent read-only observer holding the file open on Windows
        # must not turn a controller write into a failure.
        replace_retrying(temporary, path)
        # Python cannot open/fsync a directory with the Windows CRT. The file is
        # flushed above and replacement stays atomic, without POSIX directory fsync.
        if os.name != 'nt':
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_report(report, request):
    required = {'run', 'pass', 'reviewer', 'input', 'coverage', 'claims', 'advisory'}
    if not isinstance(report, dict) or set(report) != required:
        raise ReviewError('Invalid reviewer document fields')
    if type(report['pass']) is not int:
        raise ReviewError('Reviewer pass identity must be an integer')
    if any(report[key] != request[key] for key in ('run', 'pass', 'reviewer', 'input')):
        raise ReviewError('Reviewer result identity mismatch')
    if (not isinstance(report['coverage'], dict) or set(report['coverage']) != set('ABCD') or
            any(v is not True for v in report['coverage'].values())):
        raise ReviewError('Incomplete lens coverage')
    if not isinstance(report['claims'], list) or not isinstance(report['advisory'], list):
        raise ReviewError('Invalid reviewer lists')
    if not all(nonempty(a) for a in report['advisory']):
        raise ReviewError('Invalid advisory')
    seen = set()
    fields = {'id', 'kind', 'severity', 'confidence', 'lenses', 'anchor', 'trigger',
              'outcome', 'evidence', 'remedy'}
    for claim in report['claims']:
        if not isinstance(claim, dict) or set(claim) != fields:
            raise ReviewError('Invalid claim fields')
        if not all(nonempty(claim[k]) for k in ('id', 'trigger', 'outcome', 'evidence', 'remedy')):
            raise ReviewError('Claim lacks trigger, outcome, evidence or remedy')
        if claim['id'] in seen:
            raise ReviewError('Duplicate reviewer claim ID')
        seen.add(claim['id'])
        if (claim['kind'] not in ('finding', 'could_not_verify') or
                claim['severity'] not in MATERIAL | {'minor'} or
                claim['confidence'] not in ('high', 'medium', 'low')):
            raise ReviewError('Invalid claim classification')
        if (not isinstance(claim['lenses'], list) or not claim['lenses'] or
                any(lens not in 'ABCD' or len(lens) != 1 for lens in claim['lenses'])):
            raise ReviewError('Invalid claim lenses')
        anchor = claim['anchor']
        if (not isinstance(anchor, dict) or set(anchor) != {'kind', 'value'} or
                anchor['kind'] not in ('line', 'file', 'base', 'intent', 'change') or
                not nonempty(anchor['value'])):
            raise ReviewError('Invalid claim anchor')
    return report


class Controller:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.state = self._read()
        self._fix_token = None
        # Observation channel; disabled unless the command enables it. Reviewers launched
        # and not yet settled in this process, so a stop can name who is still running.
        self.progress = NullProgress()
        self._in_flight = set()
        self._stop_announcement = None

    def _read(self):
        try:
            record = json.loads((self.root / 'state.json').read_text(encoding='utf-8'))
            state = record['state']
            if record['sha256'] != digest(state) or state['version'] != 1:
                raise ValueError('integrity mismatch')
            if (any(not nonempty(state[name]) for name in
                    ('run', 'repository', 'branch', 'target', 'instructions', 'schema')) or
                    any(not isinstance(state[name], dict) for name in ('intent', 'config')) or
                    any(not isinstance(state[name], list) for name in
                        ('passes', 'findings', 'decisions', 'exceptions')) or
                    not isinstance(state['reason'], str)):
                raise ValueError('invalid saved inputs')
            if not 1 <= len(state['passes']) <= 4 or state['phase'] not in (
                    'review', 'triage', 'fixing', 'ready', 'stopped'):
                raise ValueError('invalid progression')
            for number, review_pass in enumerate(state['passes'], 1):
                if (review_pass['number'] != number or review_pass['reviewers'] != SCHEDULE[number-1]
                        or set(review_pass['attempts']) != set(review_pass['reviewers'])
                        or any(type(a) is not int or not 0 <= a <= 2
                               for a in review_pass['attempts'].values())):
                    raise ValueError('invalid pass state')
                if type(review_pass['complete']) is not bool:
                    raise ValueError('invalid completion marker')
                if review_pass['complete'] and set(review_pass['results']) != set(review_pass['reviewers']):
                    raise ValueError('complete pass is missing a required reviewer')
                if number < len(state['passes']) and not review_pass['complete']:
                    raise ValueError('advanced past an incomplete pass')
                for name, report in review_pass['results'].items():
                    if review_pass['attempts'][name] < 1:
                        raise ValueError('reviewer result has no recorded attempt')
                    validate_report(report, self._request_for(state, review_pass, name))
            if state['phase'] in ('triage', 'fixing', 'ready') and not state['passes'][-1]['complete']:
                raise ValueError('phase requires a complete review')
            if state['phase'] == 'ready' and len(state['passes']) < 2:
                raise ValueError('stronger review missing')
            if (state['phase'] == 'fixing') != (state['fix_batch'] is not None):
                raise ValueError('inconsistent fix-batch marker')
            residual = state.get('residual')
            if residual is not None:
                # Only one author batch may follow the final pass, and only after it completed.
                if (len(state['passes']) != len(SCHEDULE) or not state['passes'][-1]['complete'] or
                        state['phase'] not in ('triage', 'ready', 'stopped') or
                        not isinstance(residual.get('snapshot'), dict) or
                        not isinstance(residual.get('ids'), list) or not residual['ids']):
                    raise ValueError('invalid unreviewed delta')
            return state
        except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, ReviewError) as exc:
            raise ReviewError(f'Run state integrity check failed: {exc}') from exc

    def _save(self):
        atomic(self.root / 'state.json', {'sha256': digest(self.state), 'state': self.state})
        # The authoritative record lands first; only then does the observation announce the
        # stop, so a concurrent observer never pairs a recorded stop with a live phase.
        announcement = self._stop_announcement
        if announcement is not None:
            self._stop_announcement = None
            self.progress.stop_recorded(*announcement[:1], still_running=announcement[1])

    def _persist(self):
        action, reason = self._decision()
        if self.state['phase'] != 'stopped' and action == 'stop':
            self._set_stopped(reason)
        self._save()

    def _set_stopped(self, reason):
        already = self.state['phase'] == 'stopped'
        self.state.update(phase='stopped', reason=reason)
        if self.state['fix_batch'] is not None:
            self.state['interrupted_fix_batch'] = self.state['fix_batch']
            self.state['fix_batch'] = None
        if not already:
            self._stop_announcement = (reason, sorted(self._in_flight))

    @contextmanager
    def locked(self):
        # A CLI command keeps ownership until its final observation is published. Its
        # nested controller operations reuse that lock only on the owning thread and
        # instance; other controllers and worker threads still take the OS lock.
        if getattr(self, '_lock_thread', None) == threading.get_ident():
            if self.progress.enabled and self.progress.root is None:
                self.progress.bind(self.root, self.state['run'])
            yield
            return
        registry = self.registry(Path(self.state['repository']))
        with self.command_lock(Path(self.state['repository'])):
            self.state = self._read()
            try:
                owner = json.loads(registry.read_text(encoding='utf-8'))
                if not isinstance(owner, dict):
                    raise ValueError('invalid discovery record')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                # Without this the loss surfaced as a bare errno from the CLI's catch-all,
                # which reads as a broken run rather than a recoverable missing record.
                raise ReviewError(f'Ownership record missing or unreadable at {registry}; '
                                  'start writes it and it must accompany the run state') from exc
            if (not nonempty(owner.get('root')) or
                    Path(owner['root']).resolve() != self.root or
                    owner.get('run') not in (None, self.state['run'])):
                raise ReviewError('A newer run owns this repository; this run is historical')
            if owner.get('run') is None:
                atomic(registry, {'root': str(self.root), 'run': self.state['run']})
            # Only a command that holds the controller lock may write this run's observation:
            # a refused contender must not replace the live command's progress.json.
            if self.progress.enabled and self.progress.root is None:
                self.progress.bind(self.root, self.state['run'])
            self._lock_thread = threading.get_ident()
            try:
                yield
            finally:
                self._lock_thread = None

    @classmethod
    @contextmanager
    def command_lock(cls, repo):
        registry = cls.registry(repo)
        try:
            with file_lock(registry.with_suffix('.lock')):
                from .process_lock import ensure_idle
                ensure_idle(registry)
                yield
        except ReviewError as exc:
            if 'Another controller' in str(exc):
                try:
                    owner = json.loads(registry.read_text(encoding='utf-8'))
                    detail = (f'; active work: unconfirmed for {repo}; '
                              f"last saved run: {owner.get('root', 'unknown')} (may be superseded)")
                except (OSError, ValueError, AttributeError):
                    detail = f'; active work: unconfirmed for {repo}'
                raise ReviewError(str(exc) + detail) from exc
            raise

    @staticmethod
    def registry(repo, *, create=True):
        """Evidence discovery and stable lock identity, independent of TMPDIR/TEMP.

        Keep the legacy location so existing commands and linked worktrees contend on
        the same lock. The JSON pointer does not establish process liveness.
        """
        root = Path.home() / '.eng353-controllers'
        if create:
            root.mkdir(mode=0o700, parents=True, exist_ok=True)
        return root / (Controller._repository_key(repo) + '.json')

    @staticmethod
    def _repository_key(repo):
        common = git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir').decode().strip()
        return digest(os.path.normcase(str(Path(common).resolve())))

    @classmethod
    def start(cls, root, repo, target, intent, checks, config, *, _locked=False, _run_id=None):
        root, repo = Path(root).resolve(), Path(repo).resolve()
        if root.is_relative_to(repo):
            raise ReviewError('Run state must be outside the caller tree')
        if root.exists():
            raise ReviewError('State directory exists; resume it or explicitly select a new run')
        if set(config) != {'sonnet', 'luna', 'composer', 'opus', 'sol', 'grok'}:
            raise ReviewError('Explicit configuration required for all six reviewer roles')
        if any(not isinstance(v, dict) or not nonempty(v.get('model')) or
               not nonempty(v.get('effort')) for v in config.values()):
            raise ReviewError('Every reviewer needs a concrete model and effort configuration')
        for role in config.values():
            if set(role) - {'model', 'effort', 'runtime'}:
                raise ReviewError('Unknown reviewer configuration field; never put credentials in run configuration')
            if 'runtime' in role and (not isinstance(role['runtime'], dict) or
                    set(role['runtime']) - {'executable', 'entrypoint', 'version'}):
                raise ReviewError('Runtime configuration contains unsupported fields')
        if not isinstance(intent, dict) or not nonempty(intent.get('requirement')):
            raise ReviewError('Missing captured requirement')
        branch = current_branch(repo)
        key = intent.get('key') or next(iter(re.findall(r'[A-Z]+-\d+', branch)), '')
        if key and not nonempty(intent.get('card')):
            raise ReviewError('Jira key exists but card text is missing')
        if intent.get('spec_url') and not nonempty(intent.get('spec')):
            raise ReviewError('Linked spec is unavailable')
        if re.search(r'https?://\S*nub_specs\S*spec\.md', intent.get('card', '')) and not nonempty(intent.get('spec')):
            raise ReviewError('Card links a spec but its text is unavailable')
        registry = cls.registry(repo)
        with (nullcontext() if _locked else cls.command_lock(repo)):
            stale = None
            if registry.exists():
                try:
                    prior = json.loads(registry.read_text(encoding='utf-8'))
                    stale = prior['root']
                except (OSError, ValueError, KeyError, TypeError):
                    stale = 'unreadable saved record'
            root.mkdir(mode=0o700, parents=True)
            instance = object.__new__(cls)
            instance.root = root
            instance._fix_token = None
            instance.progress = NullProgress()
            instance._in_flight = set()
            instance._stop_announcement = None
            run_id = _run_id or uuid.uuid4().hex
            instance.state = {'version': 1, 'run': run_id, 'repository': str(repo),
                              'intent': deepcopy(intent), 'config': deepcopy(config), 'phase': 'review',
                              'passes': [], 'findings': [], 'decisions': [], 'exceptions': [],
                              'reason': '', 'fix_batch': None}
            if stale:
                # Record that a claim was replaced, so a resumed run shows it was not
                # the first for this repository.
                instance.state['decisions'].append(
                    {'kind': 'stale_claim_replaced', 'text': f'Prior evidence at {stale} was '
                     'superseded; no command or reviewer was active.'})
            instance.state['instructions'] = (Path(__file__).with_name('reviewer.md')).read_text(encoding='utf-8')
            instance.state['schema'] = (Path(__file__).with_name('review.schema.json')).read_text(encoding='utf-8')
            try:
                snapshot = instance._capture(target, checks)
                instance.state['branch'] = snapshot['branch']
                instance.state['target'] = snapshot['target']
                instance._new_pass(snapshot)
                instance._persist()
                atomic(registry, {'root': str(root), 'run': instance.state['run']})
            except BaseException:
                # Failed initial capture is left inspectable but has no active-run claim.
                raise
            return instance

    @staticmethod
    def new_run_root(intent, repo):
        key = intent.get('key') or next(iter(re.findall(r'[A-Z]+-\d+', current_branch(repo))), '')
        label = key if isinstance(key, str) and re.fullmatch(r'[A-Z]+-\d+', key) else 'unkeyed'
        namespace = (f'pre-pr-lens-review-{os.getuid()}' if os.name != 'nt'
                     else 'pre-pr-lens-review')
        parent = Path(tempfile.gettempdir()) / namespace
        for directory in (parent, parent / label):
            try:
                directory.mkdir(mode=0o700)
            except FileExistsError:
                pass
            if directory.is_symlink() or not directory.is_dir():
                raise ReviewError(f'Run artifact parent is not a safe directory: {directory}')
            if os.name != 'nt':
                info = directory.stat()
                if info.st_uid != os.getuid():
                    raise ReviewError(f'Run artifact parent is not private to this user: {directory}')
                if info.st_mode & 0o077:
                    directory.chmod(0o700)  # tighten parents created by older runner versions
                if directory.stat().st_mode & 0o077:
                    raise ReviewError(f'Run artifact parent is not private to this user: {directory}')
        return parent / label / uuid.uuid4().hex

    @classmethod
    @contextmanager
    def open_run(cls, root=None, repo=None, target=None, intent=None, checks=None, config=None):
        """Select evidence under the repository command lock and retain it for the command.

        Fresh inputs enable automatic recovery; a state-only invocation can resume valid
        evidence but cannot invent the requirement or check results needed to replace it.
        """
        supplied = all(value is not None for value in (repo, target, intent, checks, config))
        candidate = None
        reason = ''
        if repo is None:
            if root is None:
                raise ReviewError('A new run needs --repo, --base, --intent, --checks and --config; missing: --repo')
            try:
                candidate = cls(root)
                repo = candidate.state['repository']
            except ReviewError as exc:
                raise ReviewError('Saved evidence is unavailable; supply --repo, --base, --intent, '
                                  '--checks and --config to recover automatically') from exc
        repo = Path(repo).resolve()
        with cls.command_lock(repo):
            registry = cls.registry(repo)
            owner = None
            try:
                owner = json.loads(registry.read_text(encoding='utf-8'))
                if not isinstance(owner, dict) or not nonempty(owner.get('root')):
                    raise ValueError('invalid discovery record')
                candidate = cls(owner['root'])
                if owner.get('run') is not None and candidate.state['run'] != owner['run']:
                    raise ReviewError('saved run identity differs from its discovery record')
                if not supplied and root is not None and candidate.root != Path(root).resolve():
                    raise ReviewError('Requested run is superseded; fresh inputs are needed to select current evidence')
            except (OSError, ValueError, ReviewError, KeyError, TypeError) as exc:
                candidate = None
                reason = (f'Saved evidence unavailable: {exc}'
                          if registry.exists() or (root is not None and Path(root).exists()) else '')
                if root is not None and not registry.exists():
                    try:
                        candidate = cls(root)
                    except ReviewError:
                        pass
            if candidate is not None:
                try:
                    if Path(candidate.state['repository']).resolve() != repo:
                        raise ReviewError('saved evidence belongs to another worktree')
                    explicit_stop = any(d['kind'] in ('stop', 'changed_requirement', 'exception')
                                        for d in candidate.state['decisions'])
                    exhausted = (candidate.state['reason'] == CAPACITY_EXHAUSTED or any(
                        attempts >= 2 and name not in candidate.current['results']
                        for name, attempts in candidate.current['attempts'].items()))
                    terminal = (candidate.state['phase'] == 'stopped' and
                                (explicit_stop or exhausted) and
                                current_branch(repo) == candidate.state['branch'])
                    interrupted_fix = candidate.state.get('interrupted_fix_batch') is not None
                    fixing = candidate.state['phase'] == 'fixing'
                    inspected = (supplied and nonempty(checks.get('inspection')) and
                                 candidate.head['input'] in checks['inspection'])
                    awaiting_inspection = (fixing or interrupted_fix) and not inspected
                    if supplied:
                        pinned = git(repo, 'rev-parse', '--verify', target + '^{commit}').decode().strip()
                        if (candidate.state['target'] != pinned or candidate.state['intent'] != intent or
                                candidate.state['config'] != config):
                            raise ReviewError('requirement, target or reviewer configuration changed')
                        if not (fixing or interrupted_fix or terminal):
                            frozen_checks = candidate.head['checks']
                            if (not nonempty(checks.get('evidence')) or
                                    any(frozen_checks.get(key) != checks.get(key)
                                        for key in ('tree', 'status'))):
                                raise ReviewError('check tree or result changed')
                        if terminal and not explicit_stop:
                            candidate._check_unchanged()
                    if not (awaiting_inspection or terminal):
                        candidate._check_snapshots()
                    if terminal:
                        pass
                    elif fixing or interrupted_fix:
                        if not awaiting_inspection:
                            raise ReviewError('interrupted fix inspected and checked; reviewing the resulting tree afresh')
                        # Return an author boundary; never replay edits or recover a fix token.
                    elif not terminal:
                        candidate._check_unchanged()
                        if (candidate.state['phase'] == 'stopped' and
                                candidate.state['reason'].startswith('Interrupted') and
                                not explicit_stop):
                            candidate.state['phase'] = 'triage' if candidate.current['complete'] else 'review'
                            candidate.state['reason'] = ''
                            candidate.state['decisions'].append({'kind': 'interruption_recovered',
                                'text': 'No command or reviewer remains active; retained attempts still apply.'})
                            candidate._persist()
                except (ReviewError, SnapshotError, OSError, KeyError, TypeError) as exc:
                    reason = str(exc)
                    candidate = None
            resumed = candidate is not None
            if candidate is None:
                if not supplied:
                    raise ReviewError(reason + '; a new run needs --repo, --base, --intent, --checks and '
                                      '--config; missing fresh inputs for automatic recovery')
                generated = root is None
                selected = Path(root).resolve() if root is not None else cls.new_run_root(intent, repo)
                if selected.exists() or owner is not None:
                    selected = cls.new_run_root(intent, repo)
                    generated = True
                candidate = cls.start(selected, repo, target, intent, checks, config, _locked=True,
                                      _run_id=selected.name if generated else None)
                if reason:
                    candidate.state['decisions'].append({'kind': 'automatic_recovery', 'text': reason})
                    candidate._save()
            else:
                # Reclaim a lost discovery pointer only after validating retained evidence.
                atomic(registry, {'root': str(candidate.root), 'run': candidate.state['run']})
            candidate._lock_thread = threading.get_ident()
            try:
                yield candidate, resumed, reason if not resumed else ''
            finally:
                candidate._lock_thread = None

    def _capture(self, target, checks):
        path = self.root / 'snapshots' / uuid.uuid4().hex
        info = capture(Path(self.state['repository']), target, path)
        if (not isinstance(checks, dict) or checks.get('tree') != info['tree'] or
                checks.get('status') not in ('passed', 'failed', 'unavailable') or
                not nonempty(checks.get('evidence'))):
            raise ReviewError('Check evidence must identify this tree and its actual result')
        pack = {'snapshot': info, 'intent': self.state['intent'], 'checks': checks}
        (path / 'pack.json').write_bytes(encoded(pack))
        (path / 'pack.json').chmod(0o444)
        (path / 'instructions.md').write_bytes(self.state['instructions'].encode('utf-8'))
        (path / 'instructions.md').chmod(0o444)
        (path / 'review.schema.json').write_bytes(self.state['schema'].encode('utf-8'))
        (path / 'review.schema.json').chmod(0o444)
        info.update(path=str(path), checks=checks, input=content_digest(path))
        return info

    def _new_pass(self, snapshot):
        number = len(self.state['passes']) + 1
        if number > 4:
            raise ReviewError('Review capacity exhausted')
        self.state['passes'].append({'number': number, 'id': uuid.uuid4().hex,
            'snapshot': deepcopy(snapshot), 'reviewers': SCHEDULE[number-1],
            'attempts': {name: 0 for name in SCHEDULE[number-1]}, 'results': {}, 'errors': {},
            'complete': False})
        self.state['phase'] = 'review'

    @property
    def current(self):
        return self.state['passes'][-1]

    @property
    def head(self):
        """The tree the author hands off: the last reviewed snapshot, or the unreviewed
        delta recorded after the final pass."""
        residual = self.state.get('residual')
        return residual['snapshot'] if residual is not None else self.current['snapshot']

    @staticmethod
    def _request_for(state, review_pass, reviewer):
        return {'run': state['run'], 'pass': review_pass['number'], 'pass_id': review_pass['id'],
                'reviewer': reviewer, 'input': review_pass['snapshot']['input'],
                'snapshot': review_pass['snapshot']['path'], 'config': state['config'][reviewer]}

    def unchanged(self):
        """Check under the controller lock; an observed boundary failure is terminal."""
        self._check_snapshots()
        try:
            self._check_unchanged()
        except BoundaryError as exc:
            self._set_stopped(str(exc))
            self._persist()
            raise

    def _check_snapshots(self):
        """Validate retained evidence without comparing the caller during a fix."""
        checked = set()
        residual = self.state.get('residual')
        extra = [{'number': None, 'snapshot': residual['snapshot']}] if residual else []
        for review_pass in self.state['passes'] + extra:
            snapshot = review_pass['snapshot']
            identity = (snapshot['path'], snapshot['input'])
            if identity in checked:
                continue
            try:
                if content_digest(Path(snapshot['path'])) != snapshot['input']:
                    raise SnapshotError('snapshot content does not match its recorded digest')
            except (SnapshotError, OSError) as exc:
                where = (f"pass {review_pass['number']}" if review_pass['number'] is not None
                         else 'the unreviewed delta')
                reason = f"Immutable reviewer inputs changed for {where} at {snapshot['path']}: {exc}"
                self._set_stopped(reason)
                self._persist()
                raise BoundaryError(reason) from exc
            checked.add(identity)

    def _check_unchanged(self):
        previous = self.head
        try:
            with tempfile.TemporaryDirectory(prefix='eng353-compare-') as temporary:
                current = capture(Path(self.state['repository']), self.state['target'], Path(temporary) / 'tree')
        except (SnapshotError, OSError) as exc:
            which = 'unreviewed delta' if self.state.get('residual') is not None else 'reviewed input'
            raise BoundaryError(f'Cannot re-establish the {which} identity: {exc}') from exc
        if any(current[key] != previous[key] for key in ('repository', 'branch', 'base', 'tree')):
            raise BoundaryError('Caller branch or intended tree changed; stop and inspect it')

    def next_action(self):
        return self._decision()[0]

    def _outstanding_findings(self):
        # Severity is not a verification gate. Only a verified minor with an explicit
        # no-change disposition may remain advisory; its triage evidence explains why.
        # Legacy requested_minor flags/events remain audit data, not fix authorisation.
        return [f for f in self.state['findings'] if f['disposition'] == 'open' and not (
            f['severity'] == 'minor' and f['verification'] == 'confirmed' and f['action'] == 'none')]

    def waiting(self):
        """What the run waits for, read from recorded transitions only.

        Returns (kind, text) with kind in reviewers/author/human/handoff/stop. Author
        activity is never inferred: an `ask` whose findings the author has not yet triaged
        is author verification, and only a triage recorded as `ask`, or an unavailable
        check with no recorded decision, is a human question already asked.
        """
        action, reason = self._decision()
        if action == 'stop':
            return 'stop', f'stopped: {reason}'
        current = self.current
        pending = [e['path'] for e in self.head['sensitive'] if e not in self.state['exceptions']]
        if pending and (self.state['phase'] == 'review' or self.state.get('residual') is not None):
            when = 'before handoff' if self.state.get('residual') is not None else 'before review'
            return 'human', (f'human approval required for sensitive paths {when}: ' + ', '.join(pending)
                             + ' (record exact exceptions with the sensitive command)')
        if action == 'review':
            if current['complete']:      # the stronger pass always follows a clean first pass
                number = current['number'] + 1
                return 'reviewers', f"pass {number} reviewers: {', '.join(SCHEDULE[number - 1])}"
            pending = [n for n in current['reviewers'] if n not in current['results']]
            return 'reviewers', f"pass {current['number']} reviewers: {', '.join(pending)}"
        if action == 'fix':
            if current['number'] == len(SCHEDULE):
                return 'author', ('author fix batch for the verified minor findings (begin-fix); no review '
                                  'pass remains, so it is recorded as an unreviewed delta')
            return 'author', 'author fix batch for the verified findings (begin-fix)'
        if action == 'ready':
            return 'handoff', 'nothing outstanding; handoff validation is still required before acceptance'
        if self.state['phase'] == 'fixing' or self.state.get('interrupted_fix_batch') is not None:
            return 'author', ('author fix batch in progress or interrupted; after interruption inspect '
                              'the current diff and supply fresh checks with inspection naming '
                              f"input {self.head['input']} to run")
        outstanding = self._outstanding_findings()
        asked = [f['id'] for f in outstanding if f['action'] == 'ask']
        if asked and any(f['verification'] == 'unverified' for f in outstanding):
            return 'author', ('author verification of remaining findings against the reviewed source; '
                              'recorded questions remain pending')
        if asked:
            return 'human', 'human decision required: recorded question on ' + ', '.join(asked)
        if outstanding:
            return 'author', 'author verification of findings against the reviewed source (not a human question yet)'
        return 'human', 'human decision required: unavailable check evidence for the reviewed tree'

    def _retry_wording(self, name):
        remaining = sorted(self._in_flight)
        if self.current['attempts'][name] < 2:
            return ('retry once after remaining reviewers in this pass finish: ' + ', '.join(remaining)
                    if remaining else 'retry once now')
        return 'retry limit reached; the run stops' + (' once remaining reviewers finish' if remaining else '')

    def _decision(self):
        """Evaluate progression and its terminal reason without changing the record."""
        state, current = self.state, self.current
        if (state.get('interrupted_fix_batch') is not None and
                state['reason'].startswith('Interrupted provider work') and
                not any(d['kind'] in ('stop', 'changed_requirement', 'exception')
                        for d in state['decisions'])):
            return 'ask', ''
        if state['phase'] == 'stopped':
            return 'stop', state['reason']
        if state['phase'] == 'fixing':
            return 'ask', ''
        if not current['complete']:
            return 'review', ''
        outstanding = self._outstanding_findings()
        if any(f['verification'] != 'confirmed' or f['action'] != 'fix' for f in outstanding):
            return 'ask', ''
        if outstanding:
            if current['number'] < len(SCHEDULE):
                return 'fix', ''
            # After the final pass, a batch of only minor fixes still converges: it is
            # recorded as an unreviewed delta rather than exhausting the run. Material
            # findings, or anything left after that one batch, still exhaust capacity.
            if state.get('residual') is None and not any(f['severity'] in MATERIAL for f in outstanding):
                return 'fix', ''
            return 'stop', CAPACITY_EXHAUSTED
        if current['number'] == 1:
            return 'review', ''
        checks = self.head['checks']
        if state.get('residual') is not None:
            # No review follows the delta, so its own passing checks are its only verification:
            # neither a failure nor an unavailable-check waiver can stand in for them.
            if checks['status'] != 'passed':
                return 'stop', (f"Required checks did not pass for the unreviewed delta ({checks['status']}); "
                                'no review remains to verify it')
            if any(e not in state['exceptions'] for e in self.head['sensitive']):
                return 'ask', ''
            return 'ready', ''
        if checks['status'] == 'failed':
            return 'stop', 'Required checks failed for the reviewed tree'
        if checks['status'] == 'unavailable' and not any(
                d['kind'] == 'checks_unavailable' and d.get('input') == self.head['input']
                for d in state['decisions']):
            return 'ask', ''
        return 'ready', ''

    def approve_sensitive(self, entries, explanation):
        with self.locked():
            self.unchanged()
            entries = json.loads(encoded(entries))
            expected = self.head['sensitive']
            if not nonempty(explanation) or not entries or any(e not in expected for e in entries):
                raise ReviewError('Approve exact detected paths and before/after content identities')
            for entry in entries:
                if entry not in self.state['exceptions']:
                    self.state['exceptions'].append(entry)
            self.state['decisions'].append({'kind': 'sensitive_paths', 'text': explanation, 'entries': entries})
            self._persist()

    def review(self, invoke):
        with self.locked():
            if self.next_action() != 'review':
                raise ReviewError('Current state does not permit another review')
            self.unchanged()
            if self.current['complete']:
                self._new_pass(self.current['snapshot'])
                self._persist()
            if any(e not in self.state['exceptions'] for e in self.current['snapshot']['sensitive']):
                raise ReviewError('Sensitive paths need exact human exceptions before review')
            pending = [n for n in self.current['reviewers'] if n not in self.current['results']]
            self.progress.phase('review', self.current['number'],
                                waiting_for='reviewers: ' + ', '.join(pending))
            while pending:
                launch = []
                for name in pending:
                    if self.current['attempts'][name] >= 2:
                        self._set_stopped(f'{name}: retry limit reached')
                        self._persist()
                        return
                    self.current['attempts'][name] += 1
                    launch.append(self._request_for(self.state, self.current, name))
                # Persist attempts before launching; a killed launch consumes its attempt.
                self._persist()
                for request in launch:
                    self.progress.attempt_launched(request['reviewer'], PROVIDERS[request['reviewer']],
                                                   self.current['attempts'][request['reviewer']])
                failures = []
                stopped = False
                interrupt = None
                self._in_flight = {request['reviewer'] for request in launch}
                with ThreadPoolExecutor(max_workers=3) as pool:
                    futures = {pool.submit(invoke, request): request for request in launch}
                    try:
                        for future in as_completed(futures):
                            request = futures[future]
                            name = request['reviewer']
                            self._in_flight.discard(name)
                            try:
                                report = validate_report(future.result(), request)
                                self.unchanged()
                                self.current['results'][name] = report
                                self.progress.attempt_validated(name)
                            except BoundaryError as exc:
                                self.current['errors'][name] = str(exc)
                                self.progress.attempt_failed(
                                    name, str(exc),
                                    next_action='run stops; an input boundary failure is never retried')
                                self._set_stopped(str(exc))
                                self._persist()
                                # cancel() only stops a future that has not started, and a pass never
                                # has more reviewers than workers, so every sibling is already running
                                # and keeps going. Leaving the block still joins them via
                                # shutdown(wait=True). The stop is recorded first, so the decision does
                                # not depend on how long they take; their results are discarded.
                                for other in futures:
                                    other.cancel()
                                stopped = True
                                break
                            except Exception as exc:
                                failures.append(name)
                                self.current['errors'][name] = str(exc)
                                self.progress.attempt_failed(name, str(exc),
                                                             next_action=self._retry_wording(name))
                            self._persist()
                    except KeyboardInterrupt as exc:
                        # KeyboardInterrupt is delivered to this thread, not to the workers, so
                        # run_cli's own interrupt cleanup never sees it. Record the stop durably
                        # before re-raising: the attempts for this pass are already spent.
                        # open_run revalidates retained evidence before resuming those attempts.
                        # The re-raise happens after the pool has joined, so the peers that ran
                        # on are marked discarded in the observation first.
                        #
                        # What the interrupt does NOT do, verified rather than assumed: it does
                        # not terminate the reviewers already running. cancel() cannot stop a
                        # started future and leaving the pool joins them via shutdown(wait=True),
                        # so each one runs on until its CLI exits or its own deadline fires, and
                        # the interrupt surfaces only after the slowest of them. run_cli's
                        # KeyboardInterrupt cleanup does not apply, because the interrupt is
                        # delivered here and not to a worker; a reviewer that overruns is still
                        # killed by the ordinary timeout path. This is the same disposition the
                        # mutation stop already takes: a stop, not a kill.
                        self._set_stopped('Interrupted during review; run will validate retained evidence before resuming')
                        self._persist()
                        for other in futures:
                            other.cancel()
                        interrupt = exc
                        stopped = True
                # The pool has joined here, so every reviewer still running at the stop has
                # now finished; their late results were never validated or recorded.
                if stopped:
                    for name in sorted(self._in_flight):
                        self.progress.attempt_discarded(name)
                    self._in_flight = set()
                    if interrupt is not None:
                        raise interrupt
                    return
                self._in_flight = set()
                pending = failures
            for name in self.current['reviewers']:
                for claim in self.current['results'][name]['claims']:
                    self.state['findings'].append({**claim, 'source_id': claim['id'],
                        'id': 'F-' + str(len(self.state['findings']) + 1).zfill(3),
                        'reviewer': name, 'pass': self.current['number'],
                        'observed': self.current['snapshot']['input'], 'fixed_in': None,
                        'verification': 'unverified', 'disposition': 'open', 'action': 'none',
                        'history': []})
            self.current['complete'] = True
            self.state['phase'] = 'triage'
            self._persist()
            self.progress.phase(self.state['phase'], self.current['number'],
                                waiting_for=self.waiting()[1])

    def triage(self, decisions):
        if not isinstance(decisions, list) or any(not isinstance(d, dict) or
                set(d) != {'id', 'verification', 'action', 'evidence'} for d in decisions):
            raise ReviewError('Triage requires a list of id/verification/action/evidence decisions')
        with self.locked():
            if not self.current['complete'] or self.state['phase'] not in ('triage', 'ready'):
                raise ReviewError('Triage requires a complete current review')
            if self.state.get('residual') is not None:
                # No pass follows the delta, so a new decision could only reopen its findings.
                raise ReviewError('The unreviewed delta is recorded; no further triage is permitted')
            self.unchanged()
            updated = deepcopy(self.state['findings'])
            for decision in decisions:
                finding = next((f for f in updated if f['id'] == decision.get('id')), None)
                if finding is None or not nonempty(decision.get('evidence')):
                    raise ReviewError('Unknown finding or missing verification evidence')
                verification, action = decision.get('verification'), decision.get('action')
                if verification not in ('confirmed', 'refuted', 'unclear') or action not in ('fix', 'ask', 'none'):
                    raise ReviewError('Invalid triage decision')
                if (verification == 'refuted' and action != 'none' or
                        verification == 'unclear' and action != 'ask' or
                        verification == 'confirmed' and action == 'none' and finding['severity'] in MATERIAL):
                    raise ReviewError('Triage would drop unresolved material work')
                finding['history'].append({'input': self.current['snapshot']['input'], **decision})
                finding.update(verification=verification, action=action,
                               disposition='refuted' if verification == 'refuted' else 'open')
            self.state['findings'] = updated
            self.state['phase'] = 'triage'
            self._persist()

    def answer(self, answer):
        if not isinstance(answer, dict) or set(answer) - {'kind', 'text', 'ids'}:
            raise ReviewError('Human answers contain kind, text and optional selected IDs')
        with self.locked():
            if not nonempty(answer.get('text')):
                raise ReviewError('Record the actual human answer')
            kind = answer.get('kind')
            allowed = ('changed_requirement', 'exception', 'stop', 'clarify', 'request_minor', 'checks_unavailable')
            if kind not in allowed:
                raise ReviewError('Unknown human answer kind')
            if kind in ('changed_requirement', 'exception', 'stop'):
                self._set_stopped(answer['text'])
            else:
                if self.state['phase'] == 'fixing':
                    raise ReviewError('Interrupted fix needs current-diff inspection and fresh checks through run')
                self.unchanged()
                if kind == 'request_minor':
                    selected = answer.get('ids', [])
                    minors = {f['id'] for f in self.state['findings'] if f['severity'] == 'minor'}
                    if not selected or any(fid not in minors for fid in selected):
                        raise ReviewError('Select existing minor IDs')
                if kind == 'checks_unavailable' and self.state.get('residual') is not None:
                    raise ReviewError('Unavailable checks cannot be waived for the unreviewed delta')
                if kind == 'checks_unavailable' and self.head['checks']['status'] != 'unavailable':
                    raise ReviewError('Only unavailable checks can receive this decision')
            self.state['decisions'].append({**answer, 'input': self.head['input']})
            self._persist()

    def begin_fix(self):
        with self.locked():
            if self.next_action() != 'fix':
                raise ReviewError('No permitted fix batch, or no review capacity remains')
            self.unchanged()
            token = uuid.uuid4().hex
            self.state['fix_batch'] = {'token': token, 'input': self.current['snapshot']['input'],
                'ids': [f['id'] for f in self.state['findings'] if f['disposition'] == 'open' and f['action'] == 'fix']}
            self.state['phase'] = 'fixing'
            self._persist()
            self._fix_token = token
            return token

    def finish_fix(self, checks, token=None):
        with self.locked():
            batch = self.state['fix_batch']
            if self.state['phase'] != 'fixing' or not batch or (token or self._fix_token) != batch['token']:
                raise ReviewError('Fix completion needs the token from this uninterrupted author batch')
            self._check_snapshots()
            try:
                branch = current_branch(Path(self.state['repository']))
            except (SnapshotError, OSError) as exc:
                self._set_stopped(f'Cannot re-establish caller branch during fixing; stop and inspect it: {exc}')
                self._persist()
                raise BoundaryError(self.state['reason']) from exc
            if branch != self.state['branch']:
                self._set_stopped('Branch changed during fixing; stop and inspect the interrupted batch')
                self._persist()
                raise BoundaryError(self.state['reason'])
            snapshot = self._capture(self.state['target'], checks)
            if snapshot['tree'] == self.current['snapshot']['tree']:
                raise ReviewError('No content change recorded for fix batch')
            final = self.current['number'] == len(SCHEDULE)
            for finding in self.state['findings']:
                if finding['id'] in batch['ids']:
                    finding.update(disposition='fixed', fixed_in=snapshot['input'])
                    finding['history'].append({'fixed_in': snapshot['input'], 'batch': batch['token']})
                    if final:
                        finding['unreviewed'] = True
            self.state['fix_batch'] = None
            if final:
                self.state['residual'] = {'snapshot': snapshot, 'ids': batch['ids'], 'batch': batch['token']}
                self.state['phase'] = 'triage'
            else:
                self._new_pass(snapshot)
            self._persist()
            self._fix_token = None

    def handoff(self):
        with self.locked():
            if self.next_action() != 'ready':
                raise ReviewError('Run is not ready')
            self.unchanged()
            self.state['phase'] = 'ready'
            self._persist()
            return self.summary()

    def status(self):
        self.state = self._read()
        if self._historical():
            return self.summary(historical=True)
        try:
            with self.locked():
                if self.state['phase'] not in ('fixing', 'stopped'):
                    self.unchanged()
                # Settle terminal decisions left by older revisions only for the owner.
                if self.state['phase'] != 'stopped' and self.next_action() == 'stop':
                    self._persist()
                return self.summary()
        except ReviewError:
            # Ownership may have changed between the read above and taking the lock.
            self.state = self._read()
            if self._historical():
                return self.summary(historical=True)
            raise

    def _historical(self):
        try:
            registry = self.registry(Path(self.state['repository']), create=False)
            owner = json.loads(registry.read_text(encoding='utf-8'))
            return (Path(owner['root']).resolve() != self.root or
                    owner.get('run') not in (None, self.state['run']))
        except (OSError, ValueError, KeyError, TypeError, SnapshotError):
            # Missing live ownership cannot authorise handoff, but the archived record
            # remains independently readable even after the caller repository is moved.
            return (self.state['phase'] in ('ready', 'stopped') and
                    self.state.get('interrupted_fix_batch') is None)

    def summary(self, *, historical=False):
        # A stopped run's actionable evidence is the retained CLI output, and its path is
        # inside the recorded error message. Surface those here so the path is in the
        # command output an operator already reads, not only in state.json.
        diagnostics = [{'pass': p['number'], 'reviewer': name, 'error': message}
                       for p in self.state['passes']
                       for name, message in sorted(p['errors'].items())] \
            if self.next_action() == 'stop' else []
        result = {'action': self.next_action(), 'run': self.state['run'], 'root': str(self.root),
                'phase': self.state['phase'], 'historical': historical,
                'diagnostics': diagnostics,
                'tree': self.head['tree'], 'input': self.head['input'],
                'branch': self.head['branch'], 'base': self.head['base'],
                'models': {name: {'model': role['model'], 'effort': role['effort']}
                           for name, role in self.state['config'].items()},
                # attempts travels with every summary, not just a stopped one: a reviewer
                # accepted on its second try is what the handoff record must not present
                # as a clean pass, and diagnostics stays reserved for stopped runs.
                'passes': [{'number': p['number'], 'reviewers': p['reviewers'], 'complete': p['complete'],
                            'attempts': dict(sorted(p['attempts'].items())),
                            'retried': sorted(n for n, a in p['attempts'].items() if a > 1)}
                           for p in self.state['passes']],
                'findings': self.state['findings'], 'decisions': self.state['decisions'],
                'retained_reports': [
                    {'run': self.state['run'], 'pass': p['number'], 'pass_id': p['id'],
                     'reviewer': name, 'input': p['snapshot']['input'],
                     'tree': p['snapshot']['tree'], 'complete': False, 'report': report}
                    for p in self.state['passes'] if not p['complete']
                    for name, report in sorted(p['results'].items())],
                'advisory': [{'pass': p['number'], 'reviewer': name, 'items': report['advisory']}
                             for p in self.state['passes'] for name, report in p['results'].items()
                             if report['advisory']],
                'baseline_sensitive': self.head['baseline_sensitive'],
                # Runs recorded before submodule exclusion existed carry no such key.
                'submodules': self.head.get('submodules', []),
                'pending_sensitive': [e for e in self.head['sensitive']
                                      if e not in self.state['exceptions']],
                'exceptions': self.state['exceptions'], 'checks': self.head['checks'],
                'reason': self.state['reason'],
                'compare_pr_head': [sys.executable,
                                    str(Path(__file__).resolve().parents[1] / 'pre-pr-lens-review.py'),
                                    'compare-pr-head',
                                    '--state', str(self.root)]}
        residual = self.state.get('residual')
        if residual is not None:
            result['unreviewed_delta'] = {
                'ids': residual['ids'], 'tree': residual['snapshot']['tree'],
                'input': residual['snapshot']['input'], 'checks': residual['snapshot']['checks'],
                'reviewed_tree': self.current['snapshot']['tree'],
                'reviewed_input': self.current['snapshot']['input']}
        result['diagnostic_handoff'] = {
            'required': (self.state['phase'] == 'stopped' and self.current['complete'] and
                         self.state['reason'] == CAPACITY_EXHAUSTED and
                         self.current['number'] == len(SCHEDULE) and bool(self._outstanding_findings())),
            'template': str(Path(__file__).with_name('diagnostic-handoff.md').resolve()),
            'state': str(self.root / 'state.json'),
            'snapshots': [{'pass': p['number'], 'pass_id': p['id'],
                           **{k: p['snapshot'][k] for k in ('path', 'input', 'tree')}}
                          for p in self.state['passes']]}
        if historical:
            result.update(recorded_action=result['action'], action='stop', handoff_eligible=False,
                          inspection='Historical evidence only; current ownership is absent or belongs to another run')
        return result
