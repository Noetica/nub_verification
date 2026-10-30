"""Capture the intended Git tree using a private index and object directory."""
from __future__ import annotations

import fnmatch
import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile


class SnapshotError(RuntimeError):
    pass


def git(repo: Path, *args: str, env=None) -> bytes:
    if env is None:
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    result = subprocess.run(['git', '--no-optional-locks', *args], cwd=repo,
                            env=env, capture_output=True)
    if result.returncode:
        raise SnapshotError(result.stderr.decode(errors='replace').strip())
    return result.stdout


def current_branch(repo: Path, *, env=None) -> str:
    try:
        return git(repo, 'symbolic-ref', '--quiet', 'HEAD', env=env).decode().strip()
    except SnapshotError as exc:
        if str(exc):
            raise
        # Quiet symbolic-ref reports a detached HEAD with no stderr.
        raise SnapshotError('HEAD is detached; check out a branch before continuing review') from exc


def sensitive(path: str) -> bool:
    name = Path(path).name.lower()
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in
               ('.env*', '*.pem', '*.pfx', '*.key', 'secrets.json', 'appsettings.*.local.json'))


def _entries(repo, tree, env):
    """Return a tree's blobs as {path: (mode, oid)} and its Gitlinks as {path: commit}."""
    entries, gitlinks = {}, {}
    for record in git(repo, 'ls-tree', '-rz', '--full-tree', tree, env=env).split(b'\0'):
        if not record:
            continue
        meta, rawpath = record.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        path = os.fsdecode(rawpath)
        if kind == 'commit':
            gitlinks[path] = oid
        elif kind == 'blob':
            entries[path] = (mode, oid)
        else:
            raise SnapshotError(f'Unsupported Git entry {kind}: {path}; supply complete source before review')
    return entries, gitlinks


def _submodules(repo, before, after, before_links, after_links):
    """Unchanged Gitlinks as a recorded exclusion list; any change to one stops capture.

    A Gitlink is a commit pointer, not source, so a pack could not show reviewers what a
    changed one brings in. One the change leaves at the same commit is outside the change
    and is excluded from the pack; the returned list is how that absence stays visible.
    """
    changes = []
    for path in sorted(before_links.keys() | after_links.keys()):
        old, new = before_links.get(path), after_links.get(path)
        if old == new:
            continue
        if old is None:
            detail = (f'file replaced by a submodule at {new}' if path in before
                      else f'added at {new}')
        elif new is None:
            if path in after:
                detail = f'replaced by a file (was {old})'
            else:
                detail = f'removed (was {old})'
                if not os.path.lexists(repo / path):
                    detail += ('; its directory is missing, which Git records as a removal. If that '
                               'is unintended, restore the submodule directory')
        else:
            detail = f'repointed {old} -> {new}'
        changes.append(f'{path}: {detail}')
    if changes:
        raise SnapshotError('Changed submodule ' + '; '.join(changes) +
                            '. A Gitlink is not complete source; supply complete source before review')
    return [{'path': path, 'commit': commit} for path, commit in sorted(after_links.items())]


class _BlobReader:
    """Read blobs through one `git cat-file --batch` process, one request at a time.

    A process per blob made capture cost grow with the tree (ENG-619). Batch output is
    the raw blob, the same bytes `cat-file blob` prints. Each request is written only
    after the previous response is fully read, so the request and response pipes
    cannot deadlock each other. Stderr goes to a file, not a pipe nobody drains while
    blobs stream, so Git's warnings cannot fill it and stall the export.
    """

    def __init__(self, repo, env):
        if env is None:
            env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        self.errors = tempfile.TemporaryFile()
        try:
            self.process = subprocess.Popen(
                ['git', '--no-optional-locks', 'cat-file', '--batch'], cwd=repo, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.errors)
        except BaseException:
            self.errors.close()
            raise

    def read(self, oid: str) -> bytes:
        stdin, stdout = self.process.stdin, self.process.stdout
        try:
            stdin.write(oid.encode() + b'\n')
            stdin.flush()
        except OSError:
            pass  # Git exited; the empty response below reports why.
        header = stdout.readline()
        fields = header.split()
        if (len(fields) != 3 or fields[0] != oid.encode() or fields[1] != b'blob'
                or not fields[2].isdigit()):
            reason = header.decode(errors='replace').strip() or self._stderr() or 'no response'
            raise SnapshotError(f'Cannot read Git blob {oid}: {reason}')
        size = int(fields[2])
        data = stdout.read(size)
        if len(data) != size or stdout.read(1) != b'\n':
            raise SnapshotError(f'Cannot read Git blob {oid}: truncated response')
        return data

    def _stderr(self):
        self._stop()
        self.errors.seek(0)
        return self.errors.read().decode(errors='replace').strip()

    def _stop(self):
        if not self.process.stdin.closed:
            try:
                self.process.stdin.close()
            except OSError:
                pass  # Git already exited; nothing is left to flush.
        # Closing stdout too lets Git exit at once when a failure leaves a response unread.
        self.process.stdout.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    def close(self):
        self._stop()
        self.errors.close()


def _export(repo, entries, dest, env):
    links = []
    dest.mkdir(parents=True, exist_ok=True)
    reader = _BlobReader(repo, env)
    try:
        for name, (mode, oid) in entries.items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or '.git' in path.parts:
                raise SnapshotError(f'Unsafe snapshot path: {name}')
            target = dest / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise SnapshotError(f'Snapshot paths collide on this filesystem: {name}')
            target.write_bytes(reader.read(oid))
            # Link text is evidence; never create a link into the caller or prior runs.
            if mode == '120000':
                links.append(name)
            target.chmod(0o444)
    finally:
        reader.close()
    return links


def remove_readonly(function, path, error):
    # Windows requires clearing the readonly bit even when the directory is writable.
    # onexc, not the onerror callback deprecated in 3.12; the runner requires 3.12+.
    if not isinstance(error, PermissionError):
        raise error
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    function(path)


def capture(repo: Path, target: str, destination: Path) -> dict:
    repo = Path(git(Path(repo), 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    destination = destination.resolve()
    if destination == repo or destination.is_relative_to(repo):
        raise SnapshotError('Snapshot destination must be outside the caller tree')
    if destination.exists():
        raise SnapshotError('Snapshot destination already exists')
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS'] = '0'
    branch = current_branch(repo, env=env)
    head = git(repo, 'rev-parse', 'HEAD', env=env).decode().strip()
    pinned_target = git(repo, 'rev-parse', '--verify', target + '^{commit}', env=env).decode().strip()
    base = git(repo, 'merge-base', head, pinned_target, env=env).decode().strip()
    index = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-path', 'index', env=env).decode().strip())
    # Stat before reading, so the timestamp carried below belongs to these bytes.
    index_stat = index.stat()
    index_before = index.read_bytes()
    objects = git(repo, 'rev-parse', '--path-format=absolute', '--git-path', 'objects', env=env).decode().strip()
    if os.pathsep in objects:
        raise SnapshotError('Git object path contains an unsupported path-list separator')
    with tempfile.TemporaryDirectory(prefix='eng353-capture-') as temporary:
        scratch = Path(temporary)
        private_index = scratch / 'index'
        private_index.write_bytes(index_before)
        # Carry the caller index's modification time onto the copy. Git re-reads a file's
        # content only while the index is no newer than the entry it compares against; a
        # copy stamped "now" leaves that set, so a same-length edit made in the caller's
        # index write second would be trusted as clean and dropped from the tree (ENG-548).
        os.utime(private_index, ns=(index_stat.st_atime_ns, index_stat.st_mtime_ns))
        # A split index refers to sharedindex.<oid> beside the index file. Keep
        # all index reads private as well as writes: untracked-cache refreshes
        # can rewrite the caller's index even when optional locks are disabled.
        for shared_index in index.parent.glob('sharedindex.*'):
            (scratch / shared_index.name).write_bytes(shared_index.read_bytes())
        (scratch / 'objects').mkdir()
        env.update(GIT_INDEX_FILE=str(private_index), GIT_OBJECT_DIRECTORY=str(scratch / 'objects'),
                   GIT_ALTERNATE_OBJECT_DIRECTORIES=objects)
        unknown = git(repo, 'ls-files', '--others', '--exclude-standard', '-z', env=env)
        if unknown:
            raise SnapshotError('Untracked files must be intent-to-add or ignored: ' +
                                ', '.join(os.fsdecode(p) for p in unknown.split(b'\0') if p))
        # Missing skip-worktree files are outside a sparse checkout, not deletions.
        # Existing tracked files still contribute their actual working content.
        records = git(repo, 'ls-files', '-t', '-z', env=env).split(b'\0')
        tracked = b''.join(record[2:] + b'\0' for record in records if record and
                           (not record.startswith(b'S ') or os.path.lexists(repo / os.fsdecode(record[2:]))))
        flags = subprocess.run(
            ['git', 'update-index', '--no-assume-unchanged', '--no-skip-worktree', '-z', '--stdin'],
            cwd=repo, env=env, input=tracked, capture_output=True)
        if flags.returncode:
            raise SnapshotError(flags.stderr.decode(errors='replace'))
        git(repo, 'add', '-u', '--', '.', env=env)
        tree = git(repo, 'write-tree', env=env).decode().strip()
        before, before_links = _entries(repo, base, env)
        after, after_links = _entries(repo, tree, env)
        submodules = _submodules(repo, before, after, before_links, after_links)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        destination.mkdir(parents=True, mode=0o700)
        try:
            links = {side: _export(repo, entries, destination / side, env)
                     for side, entries in (('base', before), ('source', after))}
            patch = git(repo, 'diff', '--binary', '--no-ext-diff', '--no-textconv', base, tree, env=env)
            (destination / 'change.patch').write_bytes(patch)
            (destination / 'change.patch').chmod(0o444)
            # A second private-index capture detects concurrent changes during export.
            git(repo, 'add', '-u', '--', '.', env=env)
            end_tree = git(repo, 'write-tree', env=env).decode().strip()
            if (tree != end_tree or index.read_bytes() != index_before or
                    head != git(repo, 'rev-parse', 'HEAD', env=env).decode().strip() or
                    branch != current_branch(repo, env=env) or
                    git(repo, 'ls-files', '--others', '--exclude-standard', '-z', env=env)):
                raise SnapshotError('Caller changed during snapshot capture; retry after inspecting the change')
        except BaseException:
            shutil.rmtree(destination, onexc=remove_readonly)
            raise
    return {'repository': str(repo), 'branch': branch, 'target': pinned_target, 'base': base,
            'head': head, 'tree': tree, 'changed_paths': changed, 'symlinks': links,
            'submodules': submodules,
            'sensitive': [{'path': p, 'before': before.get(p), 'after': after.get(p)}
                          for p in changed if sensitive(p)],
            'baseline_sensitive': sorted(p for p in before if sensitive(p) and p not in changed)}


def content_digest(directory: Path) -> str:
    """Digest pack bytes and relative paths; reject links and non-regular entries."""
    digest = hashlib.sha256()
    for path in sorted(directory.rglob('*'), key=lambda p: p.relative_to(directory).as_posix()):
        if path.is_symlink():
            raise SnapshotError('Snapshot contains a symlink')
        if path.is_dir():
            continue
        if not path.is_file():
            raise SnapshotError('Snapshot contains a non-regular file')
        name = os.fsencode(path.relative_to(directory).as_posix())
        data = path.read_bytes()
        digest.update(len(name).to_bytes(8, 'big') + name + len(data).to_bytes(8, 'big') + data)
    return digest.hexdigest()
