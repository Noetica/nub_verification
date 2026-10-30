"""Decode Cursor's non-partial stream protocol, not JSON-looking progress prose.

Protocol: https://cursor.com/docs/cli/reference/output-format
The terminal result concatenates all assistant text. Complete assistant events carry
message boundaries; the last message after tool activity supplies the review document.
"""
import json
import re

from .cycle import ReviewError


def parse_cursor(stdout):
    final, terminal, session = None, False, None
    for line in stdout.split('\n'):
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict) or terminal:
            raise ReviewError('Invalid Cursor stream or data after terminal result')
        identity = event.get('session_id')
        if identity is not None:
            if not isinstance(identity, str) or not identity or (session and session != identity):
                raise ReviewError('Cursor stream session identity mismatch')
            session = identity
        kind = event.get('type')
        if kind == 'assistant':
            message = event.get('message')
            if not isinstance(message, dict) or message.get('role') != 'assistant':
                raise ReviewError('Invalid Cursor assistant message')
            blocks = message.get('content')
            if (not isinstance(blocks, list) or any(not isinstance(b, dict) or
                    b.get('type') != 'text' or not isinstance(b.get('text'), str) for b in blocks)):
                raise ReviewError('Invalid Cursor assistant content')
            final = ''.join(b['text'] for b in blocks)
        elif kind in ('tool_call', 'user'):
            final = None
        elif kind == 'result':
            if (event.get('subtype') != 'success' or event.get('is_error') is not False or
                    not identity or not isinstance(event.get('result'), str)):
                raise ReviewError('Cursor reported an unsuccessful terminal result')
            terminal = True
    if not terminal or not final:
        raise ReviewError('Cursor did not return a terminal success and final assistant message')
    answer = final.strip()
    # Ignore plain introductory/concluding prose around one explicitly delimited
    # document, never search earlier messages or guess how to repair its contents.
    # Structural characters outside the fence could be a competing report; reject
    # those rather than silently choosing one. Greedy capture preserves fence-like
    # text inside JSON strings; json.loads still rejects multiple fenced documents.
    fence = re.fullmatch(
        r'[^`{}\[\]]*```json[ \t]*\r?\n(.*)\r?\n```[ \t]*(?:\r?\n[^`{}\[\]]*)?',
        answer, re.DOTALL)
    return json.loads(fence[1] if fence else answer)
