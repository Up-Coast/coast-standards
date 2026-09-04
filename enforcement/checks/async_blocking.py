#!/usr/bin/env python3
"""async_blocking.py — the Python half of the ``blocking-call`` signature (ASYNC-1, E1.3).

A line pattern cannot tell a blocking call in a plain function (fine) from
the same call inside ``async def`` (it parks the event loop). This walks the
file's indentation: every ``def`` / ``async def`` opens a frame, a line at or
left of the frame's indent closes it, and a blocking call counts only while
the innermost open frame is ``async``.

``hits(path, text) -> [(line, text)]``; only ``.py`` files answer.
"""

from __future__ import annotations

import re

ASYNC_DEF = re.compile(r"^\s*async\s+def\b")
SYNC_DEF = re.compile(r"^\s*(def|class)\b")
BLOCKING = re.compile(
    r"\btime\.sleep\(|\brequests\.(get|post|put|patch|delete|head|options|request|Session)\(|"
    r"\burllib\.request\.urlopen\(|\bhttpx\.(get|post|put|patch|delete|head|request|Client)\(|"
    r"\bsubprocess\.(run|call|check_output|check_call|Popen)\(|\bsocket\.(create_connection|socket)\(|"
    r"\bopen\([^)]*\)\.(read|write)|\.result\(\)|\binput\("
)


def hits(path, text):
    if not path.endswith(".py"):
        return []
    out = []
    frames = []  # (indent, is_async) — the enclosing function bodies, innermost last
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        while frames and indent <= frames[-1][0]:
            frames.pop()
        if ASYNC_DEF.match(line):
            frames.append((indent, True))
            continue
        if SYNC_DEF.match(line):
            frames.append((indent, False))
            continue
        if frames and frames[-1][1] and BLOCKING.search(line.split("#", 1)[0]):
            out.append((number, stripped))
    return out
