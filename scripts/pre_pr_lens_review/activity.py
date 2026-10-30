"""Reviewer activity derived from each CLI's structured event stream.

What a reviewer is doing: the tool or command, its target (a path
relative to the review workspace, a search pattern or the command text) and the short
messages a CLI emits as discrete events. Notes may quote source text for the developer.
Raw tool-result contents and input prompt events are ignored here. Activity text is treated
as untrusted terminal output: control and escape sequences are stripped and credential-shaped
values are redacted. Parsing is tolerant: a line that is not JSON, or an event of an unknown
shape, yields no activity and never raises.

`retain_line` is the companion retention policy for the runner's bounded stdout tail: the
event lines that echo a reviewer's inputs back (Claude tool results, Codex command output,
Cursor completed tool calls) are never needed by the result or activity parsers, so they are
dropped before retention and cannot exhaust the runaway guard on a large review. The one
exception is Codex's report of a command it could not start (`codex_spawn_failure`), kept so
the runner can name a broken Windows sandbox.

Streams, as recorded from the real CLIs on 2026-09-14 (fixtures under tests/fixtures/streams):
  claude  --output-format stream-json: `assistant` messages whose content blocks include
          `tool_use` {name, input}; `text` blocks; a final `result` event
  codex   exec --json: `item.started`/`item.completed` with item.type `command_execution`
          {command}, `reasoning` {text} or `agent_message` {text}
  cursor  --output-format stream-json: `tool_call` events keyed `readToolCall`,
          `globToolCall`, `grepToolCall`, ... with {args}; `assistant` text; `thinking` deltas
"""
from __future__ import annotations

import json
from pathlib import PurePath
import re

TARGET_LIMIT = 160
NOTE_LIMIT = 120
ACTIVITY_LINE_CHAR_LIMIT = 4 * 1024 * 1024
_SHELL_WRAPPER = re.compile(r'^(?:/bin/|/usr/bin/)?(?:z?sh|bash|pwsh|powershell(?:\.exe)?|cmd(?:\.exe)?)\s+(?:-[a-zA-Z]+\s+)*')
# Terminal control: C0/C1 controls, CSI sequences and OSC sequences (which can retitle or spoof).
_CONTROL = re.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]|\x1b.|[\x00-\x08\x0b-\x1f\x7f-\x9f]')
# Credential-shaped values. Redaction is best-effort and deliberately broad; false positives
# cost a little clarity, misses cost a secret on a terminal.
_SECRETS = [
    re.compile(r'AKIA[0-9A-Z]{16}'),
    # Consume the scheme AND opaque credentials before the generic key/value pattern,
    # which would otherwise redact only "Bearer" or "Basic" and leave the secret behind.
    re.compile(r'''(?ix)\bauthorization["']?\s*[:=]\s*["']?
        (?:bearer|basic)\s+[^\s"'&;,]+'''),
    re.compile(r'''(?ix)\b(?:[a-z0-9]+[_-])*
        (?:api[_-]?key|secret|token|passw(?:or)?d|pwd|authorization|bearer|accountkey|sharedaccesssignature|sig)
        \b["']?\s*[:=]\s*(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s&;,]+)'''),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{8,}'),
    re.compile(r'\b(?:gh[pousr]|sk|xox[abp])[-_][A-Za-z0-9_-]{16,}'),
]
REDACTED = '[redacted]'


def sanitize(text):
    """Untrusted stream text made safe for a terminal and a shared document."""
    text = _CONTROL.sub('', str(text))
    for pattern in _SECRETS:
        text = pattern.sub(REDACTED, text)
    return text


def relative(target, workspace):
    """A path under the review workspace, shown relative to it; anything else unchanged."""
    if not isinstance(target, str) or not target:
        return target
    if workspace:
        root = str(workspace).rstrip('/\\')
        for prefix in (root + '/', root + '\\'):
            if target.startswith(prefix):
                return PurePath(target[len(prefix):]).as_posix()
        if target == root:
            return '.'
    return target


def clip(text, limit):
    text = ' '.join(sanitize(text).split())
    return text if len(text) <= limit else text[:limit - 1] + '…'


# How Codex 0.161 reports a command it could not start, as opposed to one that ran and failed:
# exit code -1 and this text from Codex itself. A reviewer could forge the shape with its own
# command's exit code and output; that only fails its own attempt, never accepts a review.
CODEX_SPAWN_FAILURE = 'Failed to create unified exec process:'


def codex_spawn_failure(event):
    """Codex's text for a command it could not start, or None for any other event."""
    if not isinstance(event, dict):
        return None
    item = event.get('item')
    if (event.get('type') != 'item.completed' or not isinstance(item, dict)
            or item.get('type') != 'command_execution' or item.get('exit_code') != -1):
        return None
    output = item.get('aggregated_output')
    return output if isinstance(output, str) and output.startswith(CODEX_SPAWN_FAILURE) else None


def retain_line(provider, line):
    """Whether the runner's bounded stdout tail should keep this stream line."""
    if not line.startswith('{'):
        return True
    try:
        event = json.loads(line)
    except ValueError:
        return True
    if not isinstance(event, dict):
        return True
    kind = event.get('type')
    if provider == 'claude':
        return kind != 'user'                       # tool results echo the files the reviewer read
    if provider == 'codex':
        item = event.get('item')
        echoes = kind == 'item.completed' and isinstance(item, dict) and item.get('type') == 'command_execution'
        return not echoes or codex_spawn_failure(event) is not None
    if provider == 'cursor':
        return not (kind == 'tool_call' and event.get('subtype') == 'completed')
    return True


def command_summary(command):
    """The command a reviewer ran, without its shell wrapper and surrounding quotes."""
    text = ' '.join(str(command).split())
    text = _SHELL_WRAPPER.sub('', text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in '"\'':
        text = text[1:-1]
    return clip(text, TARGET_LIMIT)


def _target(arguments, workspace, *keys):
    for key in keys:
        value = arguments.get(key)
        if isinstance(value, str) and value:
            return clip(relative(value, workspace), TARGET_LIMIT)
    return None


def claude_event(event, workspace):
    if event.get('type') != 'assistant':
        return []
    message = event.get('message')
    blocks = message.get('content') if isinstance(message, dict) else None
    if not isinstance(blocks, list):
        return []
    found = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get('type') == 'tool_use':
            name = str(block.get('name') or 'tool')
            if name == 'StructuredOutput':
                found.append(('report', 'writing the structured review'))
                continue
            arguments = block.get('input') if isinstance(block.get('input'), dict) else {}
            target = _target(arguments, workspace, 'file_path', 'path', 'pattern', 'command', 'query')
            found.append((name.lower(), target or name))
        elif block.get('type') == 'text' and isinstance(block.get('text'), str) and block['text'].strip():
            found.append(('note', clip(block['text'], NOTE_LIMIT)))
    return found


def codex_event(event, workspace):
    if event.get('type') != 'item.started' and event.get('type') != 'item.completed':
        return []
    item = event.get('item')
    if not isinstance(item, dict):
        return []
    kind = item.get('type')
    if kind == 'command_execution':
        # Report a command once, when it starts; its output is never surfaced.
        if event.get('type') != 'item.started':
            return []
        return [('command', command_summary(item.get('command') or ''))]
    if kind == 'reasoning' and event.get('type') == 'item.completed':
        text = item.get('text') or item.get('summary')
        if isinstance(text, list):
            text = ' '.join(str(part) for part in text)
        return [('note', clip(text, NOTE_LIMIT))] if isinstance(text, str) and text.strip() else []
    if kind == 'agent_message' and event.get('type') == 'item.completed':
        return [('report', 'final message written')]
    return []


def cursor_event(event, workspace):
    kind = event.get('type')
    if kind == 'tool_call':
        if event.get('subtype') not in (None, 'started'):
            return []
        call = event.get('tool_call')
        if not isinstance(call, dict):
            return []
        for key, value in call.items():
            if not key.endswith('ToolCall') or not isinstance(value, dict):
                continue
            name = key[:-len('ToolCall')].lower()
            arguments = value.get('args') if isinstance(value.get('args'), dict) else {}
            target = _target(arguments, workspace, 'path', 'globPattern', 'pattern', 'targetDirectory',
                             'command', 'query')
            return [(name, target or name)]
        return []
    if kind == 'assistant':
        message = event.get('message')
        blocks = message.get('content') if isinstance(message, dict) else None
        if isinstance(blocks, list):
            texts = [b.get('text') for b in blocks if isinstance(b, dict) and b.get('type') == 'text'
                     and isinstance(b.get('text'), str) and b['text'].strip()]
            if texts and not texts[0].lstrip().startswith(('{', '```')):
                return [('note', clip(texts[0], NOTE_LIMIT))]
    return []


PARSERS = {'claude': claude_event, 'codex': codex_event, 'cursor': cursor_event}


class ActivityParser:
    """Feed raw stream text as it arrives; complete JSON lines become activity events."""

    def __init__(self, provider, workspace, on_activity):
        self._parse = PARSERS.get(provider)
        self._workspace = str(workspace) if workspace else None
        self._on_activity = on_activity
        self._partial = ''
        self._discarding = False

    @property
    def supported(self):
        return self._parse is not None

    def feed(self, text):
        if self._parse is None or not text:
            return
        self._partial += text
        *lines, self._partial = self._partial.split('\n')
        for line in lines:
            if not self._discarding and len(line) <= ACTIVITY_LINE_CHAR_LIMIT:
                self._line(line)
            self._discarding = False
        if self._discarding or len(self._partial) > ACTIVITY_LINE_CHAR_LIMIT:
            # Discard through the next delimiter: a suffix must not become a new event.
            self._partial = ''
            self._discarding = True

    def finish(self):
        if not self._discarding and self._partial.strip():
            self._line(self._partial)
        self._partial = ''
        self._discarding = False

    def _line(self, line):
        line = line.strip()
        if not line.startswith('{'):
            return
        try:
            event = json.loads(line)
        except ValueError:
            return
        if not isinstance(event, dict):
            return
        try:
            found = self._parse(event, self._workspace)
        except Exception:          # an unexpected shape yields no activity, never an error
            return
        for kind, target in found:
            try:
                self._on_activity(kind, target)
            except Exception:
                # A failed observer callback must not interrupt parsing the reviewer stream.
                pass
