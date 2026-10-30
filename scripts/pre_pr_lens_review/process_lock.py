"""Reviewer lifetime leases, held by a supervisor outside the controller process."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import uuid


def ensure_idle(registry):
    """Check reviewer leases while the caller holds the repository command lock."""
    from .cycle import ReviewError, file_lock

    directory = Path(registry).with_suffix('.reviewers')
    try:
        leases = list(directory.iterdir())
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ReviewError(f'Reviewer leases could not be checked at {directory}') from exc
    for lease in leases:
        if lease.suffix != '.lock':
            continue
        try:
            with file_lock(lease):
                pass
        except (OSError, ReviewError) as exc:
            detail = ''
            try:
                metadata = json.loads(lease.with_suffix('.json').read_text(encoding='utf-8'))
                detail = f" ({metadata.get('details', {})})"
            except (OSError, ValueError, AttributeError):
                pass
            raise ReviewError('A reviewer process is still active for this repository; '
                              f'wait for it to exit before continuing{detail}; lease: {lease}') from exc
        # The supervisor has released this lease. Remove its artifacts only after
        # proving it is idle; a crashed supervisor may leave any of these behind.
        try:
            for suffix in ('.ready', '.json', '.exit', '.lock'):
                lease.with_suffix(suffix).unlink(missing_ok=True)
        except OSError as exc:
            raise ReviewError(f'Completed reviewer lease could not be cleaned at {lease}') from exc


def prepare(directory, argv, timeout, details=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lease = directory / (uuid.uuid4().hex + '.lock')
    request = lease.with_suffix('.json')
    request.write_text(json.dumps({'argv': argv, 'timeout': timeout,
                                   'details': details or {}}), encoding='utf-8')
    return [sys.executable, str(Path(__file__).resolve()), str(lease)], lease


def await_ready(process, lease, timeout):
    from .cycle import ReviewError

    deadline = time.monotonic() + min(timeout, 30)
    while not lease.with_suffix('.ready').exists():
        if process.poll() is not None:
            raise ReviewError('Reviewer lifetime supervisor exited before acquiring its lease')
        if time.monotonic() >= deadline:
            raise ReviewError('Reviewer lifetime supervisor did not acquire its lease in time')
        time.sleep(0.01)


def wait_reviewer(process, lease, timeout):
    """Observe native CLI exit independently of descendants retaining output pipes."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            return int(lease.with_suffix('.exit').read_text(encoding='ascii')), True
        except (OSError, ValueError):
            pass
        code = process.poll()
        if code is not None:
            return code, False
        if time.monotonic() >= deadline:
            raise subprocess.TimeoutExpired(process.args, timeout)
        time.sleep(0.01)


def _windows_job():
    """Put this supervisor and its children in a job killed when this process exits."""
    import ctypes
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):
        _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                    ('flags', wintypes.DWORD), ('min_working_set', ctypes.c_size_t),
                    ('max_working_set', ctypes.c_size_t), ('active_processes', wintypes.DWORD),
                    ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD),
                    ('scheduling', wintypes.DWORD)]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [('basic', BasicLimits), ('io', ctypes.c_ulonglong * 6),
                    ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                    ('peak_process_memory', ctypes.c_size_t), ('peak_job_memory', ctypes.c_size_t)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                              ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    job = kernel.CreateJobObjectW(None, None)
    limits = ExtendedLimits()
    limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if (not job or not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits),
                                                     ctypes.sizeof(limits)) or
            not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess())):
        raise ctypes.WinError(ctypes.get_last_error())
    # Deliberately leave this non-inheritable handle open until process exit.
    return job


def _terminate_tree(job):
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        if not kernel.TerminateJobObject(job, 124):
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        os.killpg(os.getpid(), signal.SIGKILL)


def _forward(source, destination):
    with source:
        while chunk := source.read1(16384):
            # Once the controller disappears, continue draining the reviewer so its
            # pipe writes can finish and the lifetime lease can eventually release.
            if destination is not None:
                try:
                    while chunk:
                        chunk = chunk[os.write(destination, chunk):]
                except OSError:
                    destination = None


def supervise(lease):
    from pre_pr_lens_review.cycle import file_lock

    request = json.loads(lease.with_suffix('.json').read_text(encoding='utf-8'))
    with file_lock(lease):
        job = _windows_job() if os.name == 'nt' else None
        lease.with_suffix('.ready').write_text(str(os.getpid()), encoding='ascii')
        # Read exactly one byte without buffering any of the provider's prompt.
        # No GO means the controller died before the lease was established.
        if os.read(sys.stdin.fileno(), 1) != b'\x01':
            return 1
        child = subprocess.Popen(request['argv'], stdin=sys.stdin, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=False)
        readers = [threading.Thread(target=_forward, args=(source, destination.fileno()), daemon=True)
                   for source, destination in ((child.stdout, sys.stdout), (child.stderr, sys.stderr))]
        for reader in readers:
            reader.start()
        deadline = time.monotonic() + request['timeout']
        try:
            code = child.wait(timeout=request['timeout'])
        except subprocess.TimeoutExpired:
            _terminate_tree(job)
            return 124
        lease.with_suffix('.exit').write_text(str(code), encoding='ascii')
        for reader in readers:
            reader.join(timeout=max(0, deadline - time.monotonic()))
        if any(reader.is_alive() for reader in readers):
            _terminate_tree(job)
            return 124
        return code


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    lease = Path(sys.argv[1])
    try:
        code = supervise(lease)
    finally:
        for suffix in ('.ready', '.json', '.exit'):
            lease.with_suffix(suffix).unlink(missing_ok=True)
    sys.exit(code)
