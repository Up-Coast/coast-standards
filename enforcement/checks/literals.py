#!/usr/bin/env python3
"""literals.py — the built-in user-facing-text check (signature ``ui-string-literal``, E1.2).

A regex over one line cannot tell a string literal from a comment, skip an
interpolation, or see what call the literal sits in. This module lexes the
whole file the way Coast's copy guard does (Tests/CoastAppCoreTests/
CoastCopyGuardTests.swift — the algorithm is ported, the skip contexts are
its list plus the ones a customer app needs) and returns every literal that
reads as words a person would see: it contains a letter outside any
interpolation, and it looks like text rather than a key — a space, a
capitalised word, or sentence punctuation. A semantic key
(``vehicle.status.doNotDispatch``, ``save_button``) is never text.

Tuned (E1.2, 2026-09-04) against Coast's copy guard on Coast's own Views and
ViewModels: both report zero there — the Swift skip contexts are the guard's
list plus the customer-app ones, and the pass plant
(``tests/plants/ios/ui-string-literal.pass.swift``) carries every one of
those contexts so the parity cannot silently regress.

Per language: Swift (full lexer: nested block comments, ``\\(…)``
interpolation, raw and multi-line strings), Kotlin (string literals in the
Compose text slots and XML ``android:text``), TypeScript/JSX (JSX text
between tags, bare JSX text on its own line, and the known text props —
comparisons, arrows, generics and named-import lists are not copy), Python (message-shaped literals
in response bodies and exceptions, outside the messages module).

``hits(language, text, skip_suffixes) -> [(line, literal)]``.
"""

from __future__ import annotations

import re

TEXT_SHAPE = re.compile(r"\s|[.!?,:;]$|^[A-Z][a-z]")
# A statement handed to a database is never words on a screen (tuned on Coast's
# own tree, E1.2: the SQL in a store file whose name ends in "…Review.swift").
SQL_STATEMENT = re.compile(r"^(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|PRAGMA|WITH|VACUUM|BEGIN|COMMIT|ROLLBACK|EXPLAIN|REPLACE)\b", re.IGNORECASE)
SQL_CLAUSE = re.compile(r"\b(FROM|INTO|SET|TABLE|INDEX|VALUES|WHERE|TRANSACTION|VIEW|TRIGGER)\b", re.IGNORECASE)


def looks_like_text(body):
    """Words a person reads, not an identifier, key, symbol name, URL or SQL."""
    stripped = body.strip()
    if not stripped or not re.search(r"[A-Za-z]", stripped):
        return False
    if SQL_STATEMENT.match(stripped) and SQL_CLAUSE.search(stripped):
        return False
    if re.match(r"^[\w.\-/:%#@+]*$", stripped) and " " not in stripped:
        # an identifier, a dotted key, a path, a URL — unless it is one capitalised English word
        return bool(re.match(r"^[A-Z][a-z]+$", stripped))
    if stripped.startswith(("http://", "https://", "/", "%", "#")):
        return False
    return TEXT_SHAPE.search(stripped) is not None


# ---------------------------------------------------------------- Swift


SWIFT_SKIP_SUFFIXES = (
    "systemName:", "systemImage:", "string:", "==", "!=", "Contains(", "accessibilityIdentifier(",
    "keyboardShortcut(", "named:", "forKey:", "contains(", "hasPrefix(", "hasSuffix(", "appendingPathComponent(",
    "atPath:", "toFile:", "id:", "ID:", "referencedName:", "secretName:", "[",
    "Image(", "Color(", "Font.custom(", "#Preview(", "Name(", "subsystem:", "category:", "identifier:",
    "print(", ".info(", ".debug(", ".error(", ".warning(", ".notice(", ".fault(", ".trace(", ".log(",
    "assert(", "precondition(", "fatalError(", "assertionFailure(", "NSLocalizedString(", "localized:",
    "forResource:", "withExtension:", "ofType:", "rawValue:", "key:", "Key(", "userInfo:", "scheme:", "host:",
    "path:", "url:", "URL(", "AppStorage(", "SceneStorage(", "UserDefaults(", "tag(", "Notification.Name(",
    "bundle:", "tableName:", "comment:", "CodingKeys", "static let", "let key", "case ",
)


def swift_literals(src):
    """[(line, body, text_before)] for every top-level string literal in Swift source, comments skipped."""
    out = []
    i, n = 0, len(src)
    line = 1

    def scan_string(j):
        """src[j] opens a string (after any raw # prefix); returns the index past its close."""
        hashes = 0
        while j < n and src[j] == "#":
            hashes += 1
            j += 1
        closing = ('"""' if src.startswith('"""', j) else '"') + "#" * hashes
        j += 3 if closing.startswith('"""') else 1
        escape = "\\" + "#" * hashes
        while j < n:
            if src.startswith(escape, j):
                if src.startswith("(", j + len(escape)):
                    j = skip_interpolation(j + len(escape))
                    continue
                j += len(escape) + 1
                continue
            if src.startswith(closing, j):
                return j + len(closing)
            j += 1
        return n

    def skip_interpolation(j):
        depth = 0
        while j < n:
            c = src[j]
            if c == '"' or (c == "#" and re.match(r'#+"', src[j:j + 8])):
                j = scan_string(j)
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return j + 1
            j += 1
        return n

    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c == "/" and src.startswith("//", i):
            end = src.find("\n", i)
            i = n if end < 0 else end
            continue
        if c == "/" and src.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/*", j):
                    depth += 1
                    j += 2
                elif src.startswith("*/", j):
                    depth -= 1
                    j += 2
                else:
                    if src[j] == "\n":
                        line += 1
                    j += 1
            i = j
            continue
        if c == '"' or (c == "#" and re.match(r'#+"', src[i:i + 8])):
            start = i
            end = scan_string(i)
            raw = src[start:end]
            body = raw.strip("#")
            body = body[3:-3] if body.startswith('"""') else body[1:-1]
            out.append((line, body, src[:start]))
            line += raw.count("\n")
            i = end
            continue
        i += 1
    return out


def swift_text_outside_interpolation(body):
    text, i = [], 0
    while i < len(body):
        if body[i] == "\\" and i + 1 < len(body):
            if body[i + 1] == "(":
                depth, j = 0, i + 1
                while j < len(body):
                    if body[j] == "(":
                        depth += 1
                    elif body[j] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                i = j + 1
                continue
            i += 2
            continue
        text.append(body[i])
        i += 1
    return "".join(text)


def swift_hits(src, skip_suffixes=SWIFT_SKIP_SUFFIXES):
    hits = []
    for line, body, before in swift_literals(src):
        text = swift_text_outside_interpolation(body)
        if not looks_like_text(text):
            continue
        trimmed = before.rstrip()
        if any(trimmed.endswith(suffix) for suffix in skip_suffixes):
            continue
        last_line = trimmed.rsplit("\n", 1)[-1].strip()
        if trimmed.endswith("=") and last_line.startswith("case "):
            continue  # a raw-value enum case is an identifier
        if last_line.startswith(("static let", "let ", "var ")) and "=" in last_line and re.search(r"\b(id|key|name|identifier|Key|ID)\s*(:\s*String)?\s*=\s*$", last_line):
            continue
        hits.append((line, text.strip()))
    return hits


# ---------------------------------------------------------------- Kotlin, TypeScript/JSX, Python (line shapes)


KOTLIN_SLOTS = re.compile(r'(?:\bText\s*\(\s*|\b(?:text|title|label|placeholder|contentDescription|headline|supportingText|message)\s*=\s*)"((?:[^"\\]|\\.)*)"')
XML_TEXT = re.compile(r'android:(?:text|hint|contentDescription|title|label)\s*=\s*"([^"@?][^"]*)"')
# A `>` that closes a tag is not preceded by whitespace, `=` (an arrow), `-` or another `>`;
# the `<` that opens the next tag is followed by `/` or a tag name. `if (a > 0 && b < max)`
# and `() => Promise<T>` match neither shape (E2.11, tuned on one adopting web project).
JSX_TEXT = re.compile(r"(?<![\s=<>\-])>\s*([^<>{}]*[A-Za-z][^<>{}]*?)\s*<(?=[/A-Za-z])")
JSX_BARE_TEXT = re.compile(r"^\s*([A-Z][A-Za-z][^<>{}=;()]*)\s*$")
# Words on a screen never carry an operator, and never open with a closing bracket.
TSX_OPERATOR = re.compile(r"&&|\|\||=>|==|!=|\?\?|\?\.|\+=|-=")
TSX_NOT_COPY_START = ")]}=:;,&|/"
# `import {`, `import type {`, `import React, {`, `export {` — a named list prettier breaks one name per line.
TSX_NAMED_LIST_OPEN = re.compile(r"^\s*(?:import|export)\s+(?:type\s+)?(?:[\w$]+\s*,\s*)?\{[^}]*$")
JSX_PROPS = re.compile(r'\b(?:title|placeholder|aria-label|alt|label|helperText|description|accessibilityLabel)\s*=\s*"((?:[^"\\]|\\.)*)"')
TS_CALL_TEXT = re.compile(r"""\b(?:Alert\.alert|alert|confirm|toast(?:\.\w+)?|showMessage|setError|setMessage)\s*\(\s*(['"`])((?:(?!\1).)*)\1""")
PY_MESSAGE = re.compile(r"""(?:\b(?:detail|message|msg|error|title|description|text)\s*=\s*|["'](?:detail|message|msg|error|title|description|text)["']\s*:\s*)(['"])((?:(?!\1).)*)\1""")
PY_RAISE = re.compile(r"""\braise\s+\w+(?:\.\w+)*\s*\(\s*(['"])((?:(?!\1).)*)\1""")
COMMENT_LINE = re.compile(r"^\s*(//|#|\*|/\*)")


def line_hits(text, patterns, comment=COMMENT_LINE, group=1):
    hits = []
    for number, line in enumerate(text.splitlines(), 1):
        if comment.match(line):
            continue
        for pattern in patterns:
            for match in pattern.finditer(line):
                body = match.group(group if pattern.groups == 1 else pattern.groups)
                if looks_like_text(body):
                    hits.append((number, body.strip()))
    return hits


def kotlin_hits(src):
    return line_hits(src, [KOTLIN_SLOTS])


def xml_hits(src):
    return line_hits(src, [XML_TEXT], comment=re.compile(r"^\s*<!--"))


def tsx_copy(body):
    stripped = body.strip()
    return bool(stripped) and stripped[0] not in TSX_NOT_COPY_START and not TSX_OPERATOR.search(stripped) and looks_like_text(stripped)


def neighbour(lines, index, step):
    """The nearest non-blank line before (step -1) or after (step 1) lines[index], stripped; '' at the edge."""
    index += step
    while 0 <= index < len(lines):
        if lines[index].strip():
            return lines[index].strip()
        index += step
    return ""


def tsx_hits(src):
    """JSX text between tags, the known text props, and the message calls; then bare JSX text on
    its own line. A bare line is copy when it is several words, or one word sitting under an
    opening tag or above a closing one — `  Button,` in a named import, `  Monday,` in a list
    and `  Inactive` at the end of an enum are identifiers, not copy."""
    hits = [(number, body) for number, body in line_hits(src, [JSX_TEXT, JSX_PROPS, TS_CALL_TEXT]) if tsx_copy(body)]
    lines = src.splitlines()
    in_named_list = False
    for index, line in enumerate(lines):
        if in_named_list:
            in_named_list = "}" not in line
            continue
        if TSX_NAMED_LIST_OPEN.match(line):
            in_named_list = True
            continue
        if COMMENT_LINE.match(line):
            continue
        match = JSX_BARE_TEXT.match(line)
        if not match:
            continue
        body = match.group(1).strip()
        if " " not in body:
            if body.endswith(","):
                continue
            if not (neighbour(lines, index, -1).endswith(">") or neighbour(lines, index, 1).startswith("</")):
                continue
        if tsx_copy(body) and (index + 1, body) not in hits:
            hits.append((index + 1, body))
    return sorted(set(hits))


def python_hits(src):
    return line_hits(src, [PY_MESSAGE, PY_RAISE])


LANGUAGES = {
    ".swift": swift_hits, ".kt": kotlin_hits, ".xml": xml_hits,
    ".tsx": tsx_hits, ".jsx": tsx_hits, ".ts": lambda src: line_hits(src, [TS_CALL_TEXT]), ".js": lambda src: line_hits(src, [TS_CALL_TEXT]),
    ".py": python_hits,
}


def hits(path, src):
    """[(line, literal)] of user-facing text literals in a file of a known language; [] otherwise."""
    for extension, function in LANGUAGES.items():
        if path.endswith(extension):
            return function(src)
    return []
