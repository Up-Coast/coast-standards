#!/usr/bin/env python3
"""view_model_ownership.py — two native-pattern built-ins for SwiftUI (A-5).

SwiftUI rebuilds a view's value, and re-runs every builder closure in its
body, whenever its state changes. An observable view model built in either
place is rebuilt with it, and whatever it held (a recording, typed input, a
loaded page) is lost. The platform's wiring is ownership in ``@State``.

- ``view-model-in-presentation``: an observable view model constructed inside
  a presentation builder: ``.sheet``, ``.fullScreenCover``, ``.popover``,
  ``.navigationDestination`` or a ``NavigationLink``.
- ``view-model-in-let``: a SwiftUI view that constructs an observable view
  model into a ``let`` or plain ``var`` property, as a default value or by
  assigning ``self.<name>`` in its initializer.

A view that receives a model it does not create keeps it in a plain property;
that is how Observation passes a model down and neither check refuses it.

A type counts as an observable view model when its name ends in ``ViewModel``
or the file declares it ``@Observable`` or ``ObservableObject``.

``presentation_hits(text)`` and ``let_hits(text)`` return ``[(line, text)]``.
"""

from __future__ import annotations

import re

PRESENTER = re.compile(
    r"\.(?:sheet|fullScreenCover|popover|navigationDestination)\s*\(|\bNavigationLink\s*[({]")
OBSERVABLE_DECLARATION = re.compile(
    r"@Observable\b(?:\s+(?:final|public|internal|private|fileprivate|open))*\s+class\s+(\w+)"
    r"|\bclass\s+(\w+)\s*:[^{]*\bObservableObject\b")
VIEW_DECLARATION = re.compile(r"\bstruct\s+(\w+)\s*(?:<[^>{]*>)?\s*:[^{]*\bView\b[^{]*\{")
PROPERTY_WRAPPER = re.compile(r"@\w+")


def mask(text):
    """The source with comments and string literals blanked to spaces, newlines kept, so
    braces and names inside them never count and every offset keeps its line."""
    out = list(text)
    i, n = 0, len(text)

    def blank(start, end):
        for k in range(start, min(end, n)):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        if text.startswith("//", i):
            end = text.find("\n", i)
            end = n if end < 0 else end
            blank(i, end)
            i = end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = n if end < 0 else end + 2
            blank(i, end)
            i = end
        elif text.startswith('"""', i):
            end = text.find('"""', i + 3)
            end = n if end < 0 else end + 3
            blank(i, end)
            i = end
        elif text[i] == '"':
            j = i + 1
            while j < n and text[j] not in '"\n':
                j += 2 if text[j] == "\\" else 1
            blank(i, j + 1)
            i = j + 1
        else:
            i += 1
    return "".join(out)


def closing(code, start, open_char, close_char):
    """The index past the bracket that closes the one at ``start``."""
    depth = 0
    for index in range(start, len(code)):
        if code[index] == open_char:
            depth += 1
        elif code[index] == close_char:
            depth -= 1
            if depth == 0:
                return index + 1
    return len(code)


def construction(code):
    """A regex matching a call that builds an observable view model in this file."""
    declared = {name for match in OBSERVABLE_DECLARATION.finditer(code) for name in match.groups() if name}
    names = r"\w*ViewModel" + "".join(f"|{re.escape(name)}" for name in sorted(declared))
    return re.compile(rf"(?<![\w.])(?:{names})\s*(?:\.init\s*)?\(")


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def hit(text, offset):
    number = line_of(text, offset)
    return number, text.splitlines()[number - 1]


def presentation_hits(text):
    """Each observable view model built inside a presentation builder's arguments or its
    trailing closure."""
    code = mask(text)
    builds = construction(code)
    hits = set()
    for presenter in PRESENTER.finditer(code):
        end = presenter.end() - 1
        if code[end] == "(":
            end = closing(code, end, "(", ")")
        after = end
        while after < len(code) and code[after] in " \t\n":
            after += 1
        if after < len(code) and code[after] == "{":
            end = closing(code, after, "{", "}")
        for built in builds.finditer(code, presenter.end(), end):
            hits.add(hit(text, built.start()))
    return sorted(hits)


def let_hits(text):
    """Each observable view model a SwiftUI view constructs into a property it does not hold
    in ``@State`` or ``@StateObject``."""
    code = mask(text)
    builds = construction(code)
    hits = set()
    for view in VIEW_DECLARATION.finditer(code):
        body_start = view.end() - 1
        body_end = closing(code, body_start, "{", "}")
        owned = set()
        initializers = []
        for start, line in top_level_lines(code, body_start + 1, body_end - 1):
            declared = PROPERTY.match(line)
            if declared:
                wrappers = PROPERTY_WRAPPER.findall(declared.group(1))
                if "@State" in wrappers or "@StateObject" in wrappers:
                    owned.add(declared.group(2))
                elif declared.group(3) is not None:
                    at = start + declared.end()
                    if builds.match(code, at):
                        hits.add(hit(text, at))
            opened = INITIALIZER.match(line)
            if opened:
                brace = code.find("{", start + opened.end())
                if 0 <= brace < body_end:
                    initializers.append((brace, closing(code, brace, "{", "}")))
        for start, end in initializers:
            for assigned in SELF_ASSIGNMENT.finditer(code, start, end):
                at = assigned.end()
                if assigned.group(1) not in owned and builds.match(code, at):
                    hits.add(hit(text, at))
    return sorted(hits)


PROPERTY = re.compile(
    r"\s*((?:@\w+(?:\([^)]*\))?\s+)*)(?:(?:private|fileprivate|internal|public)(?:\(set\))?\s+)*"
    r"(?:let|var)\s+(\w+)\s*(?::[^={]*)?(=\s*)?")
INITIALIZER = re.compile(r"\s*(?:(?:private|fileprivate|internal|public)\s+)*init\s*[(<]")
SELF_ASSIGNMENT = re.compile(r"\bself\.(\w+)\s*=\s*")


def top_level_lines(code, start, end):
    """(offset, line) for each line of ``code[start:end]`` that begins at brace depth zero."""
    depth = 0
    line_start = start
    line_depth = 0
    for index in range(start, end + 1):
        if index == end or code[index] == "\n":
            if line_depth == 0:
                yield line_start, code[line_start:index]
            line_start = index + 1
            line_depth = depth
            continue
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
