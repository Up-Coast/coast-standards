#!/usr/bin/env python3
"""test_criteria.py — the ``test-criterion-tag`` built-in (TEST-1, E1.4).

A test states which acceptance criterion it verifies. This finds every test
declaration in a test file (Swift Testing ``@Test`` and XCTest ``func test…``,
JUnit ``@Test``, Jest/Vitest ``it(``/``test(``, pytest ``def test_``) and
reports the ones whose declaration, the three lines above it (its comment)
and the first line of its body carry no reference — ``AC-<n>``,
``criterion`` or ``criteria``.

``hits(path, text) -> [(line, name)]``.
"""

from __future__ import annotations

import re

REFERENCE = re.compile(r"\bAC-\d+\b|\bcriteri(on|a)\b", re.IGNORECASE)
DECLARATIONS = {
    ".swift": re.compile(r"^\s*(@Test\b|func\s+test\w*\s*\()"),
    ".kt": re.compile(r"^\s*@Test\b"),
    ".kts": re.compile(r"^\s*@Test\b"),
    ".java": re.compile(r"^\s*@Test\b"),
    ".ts": re.compile(r"^\s*(it|test)\s*\("),
    ".tsx": re.compile(r"^\s*(it|test)\s*\("),
    ".js": re.compile(r"^\s*(it|test)\s*\("),
    ".jsx": re.compile(r"^\s*(it|test)\s*\("),
    ".py": re.compile(r"^\s*(async\s+)?def\s+test_\w+"),
}


def hits(path, text):
    declaration = next((regex for extension, regex in DECLARATIONS.items() if path.endswith(extension)), None)
    if declaration is None:
        return []
    lines = text.splitlines()
    out = []
    for index, line in enumerate(lines):
        if not declaration.match(line):
            continue
        window = lines[max(0, index - 3):index + 3]
        if any(REFERENCE.search(candidate) for candidate in window):
            continue
        out.append((index + 1, line.strip()))
    return out
