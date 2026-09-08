#!/usr/bin/env python3
"""type_size.py — the ``type-size`` built-in (A-3 / ARCH-5, E1.4; advisory).

A type or module has one job. This measures two things a reviewer wants
pointed at: a top-level type whose body runs past TYPE_LINES (Swift, Kotlin,
Python classes) and a file past FILE_LINES (the module, on every platform).
Advisory only — the rule says size is a signal for a reviewer, never a
failure.

``spans(path, text) -> [(start, end, words)]`` — one per oversized type or
file; ``hits`` reports each at its first line.
"""

from __future__ import annotations

import re

TYPE_LINES = 300
FILE_LINES = 400
TYPE_DECLARATIONS = {
    ".swift": re.compile(r"^(?:(?:public|private|internal|fileprivate|open|final|indirect)\s+)*(class|struct|enum|actor|extension)\s+(\w+)"),
    ".kt": re.compile(r"^(?:(?:public|private|internal|abstract|open|sealed|data|enum|annotation|inner)\s+)*(class|object|interface)\s+(\w+)"),
    ".py": re.compile(r"^class\s+(\w+)"),
}


def type_spans(path, lines):
    regex = next((r for extension, r in TYPE_DECLARATIONS.items() if path.endswith(extension)), None)
    if regex is None:
        return []
    starts = [(index, regex.match(line)) for index, line in enumerate(lines) if regex.match(line)]
    spans = []
    for position, (index, match) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        # trailing blank lines belong to nobody
        while end > index + 1 and not lines[end - 1].strip():
            end -= 1
        size = end - index
        if size > TYPE_LINES:
            name = match.group(match.lastindex)
            spans.append((index + 1, end, f"{name} runs {size} lines — a type with one job rarely needs more than {TYPE_LINES}"))
    return spans


def spans(path, text):
    lines = text.splitlines()
    out = type_spans(path, lines)
    if len(lines) > FILE_LINES:
        out.append((1, len(lines), f"this file runs {len(lines)} lines — a module with one job rarely needs more than {FILE_LINES}"))
    return out


def hits(path, text):
    return [(start, words) for start, _, words in spans(path, text)]
