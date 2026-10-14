#!/usr/bin/env python3
"""unreached_views.py — the ``unreached-view`` built-in (rule 08, task E4.5; block, tree scope).

A screen was once built, tested, screenshot-approved and ticked complete — and the only
thing that ever constructed it was a debug component gallery. No route in the product
drew it; every pane that should have sat on top of it fell back to the door. A gallery,
a preview, a storybook or a test is a construction site, so a search for callers looked
satisfied. This check makes the distinction the search did not: **a gallery, preview or
test is not a consumer.** A public view or component needs a construction site on a
route the shipping product has — on by default, or behind a declared feature flag (a
construction inside ``if flag`` is a construction). A view deliberately not mounted yet
says so beside its declaration, with the task that mounts it::

    /// not-mounted-yet: S3 — The Landscape
    public struct CoastNoticedCard: View { … }

The tag lives with the code, never in a governing file an agent cannot write, so a new
view cannot join the deferred list silently and the list is read where the code is.

What is a declaration, per platform (public, top level; anything narrower is the
module's own business and is constructed where it is declared):

* Swift: ``public struct Name: View`` (any generic clause, any other conformances).
* Kotlin: a top-level ``@Composable fun Name(`` in a ``ui``/``ui_lib`` file, not
  ``private``/``internal``, named in PascalCase; a ``@Preview`` function is skipped.
* TypeScript/JavaScript: ``export function Name(``, ``export const Name =`` or
  ``export default function Name(`` in a ``ui``/``ui_lib`` file, PascalCase.
* Python: none — the rule is UI-shaped.

Web file-based routing: a file is a route (a root the framework reaches) when it sits under
``app/`` or ``src/app/`` and is named ``page``, ``layout``, ``template``, ``error``,
``not-found``, ``loading``, ``global-error``, ``default`` or ``route``; when it sits under
``pages/`` or ``src/pages/`` (Pages Router); when it is a Remix or React Router route module
(``routes/`` under ``app/`` or ``src/``, or ``root``/``routes`` in ``app/``); or when it is a
Vite entry (``main``/``index`` directly under ``src/``). Reachability follows the module import
graph from those roots (relative imports and the ``@/`` alias to ``src/``, re-exports and
dynamic imports included), so a view in any file on that graph is reached, whether it is built
directly, through a registry constant or through a library module. A view in a file no root
reaches, and that nothing constructs, is still reported.

What is a construction site: a use of the name followed by ``(`` or ``<`` (Swift, Kotlin,
TS calls) or ``<Name`` / ``component: Name`` / ``element: Name`` (JSX, route tables) in any
file the path classes do not put under ``gallery``, ``tests``, ``generated`` or ``plans``,
outside a ``#Preview`` block (Swift) or a ``@Preview`` function (Kotlin) — the file that
declares the view included, so a helper used where it is declared is reached.

``failures_for(platform, paths, files, texts=None) -> [(path, line, words)]`` — one per
unreached view, at its declaration. ``paths`` is the scanner's ``PathClasses``.
"""

from __future__ import annotations

import re

TAG = re.compile(r"not-mounted-yet\s*:\s*(\S.*)")
TAG_LOOKBACK = 6   # the comment lines above a declaration that may carry the tag

EXCLUDED_CLASSES = {"gallery", "tests", "generated", "plans", "git", "governing", "docs", "design_bundle"}
LANGUAGE_OF_PLATFORM = {"ios": "swift", "macos": "swift", "android": "kotlin",
                        "react-native": "ts", "web": "ts", "python": None}
EXTENSIONS = {"swift": (".swift",), "kotlin": (".kt",), "ts": (".ts", ".tsx", ".js", ".jsx")}

SWIFT_VIEW = re.compile(r"^\s*public\s+(?:final\s+)?struct\s+(\w+)\s*(?:<[^>]*>)?\s*:\s*(?:[\w.]+\s*,\s*)*View\b")
KOTLIN_FUN = re.compile(r"^\s*(?:(public|private|internal)\s+)?fun\s+([A-Z]\w*)\s*\(")
KOTLIN_ANNOTATION = re.compile(r"^\s*@(\w+)")
TS_EXPORTS = (
    re.compile(r"^\s*export\s+(?:default\s+)?(?:async\s+)?function\s+([A-Z]\w*)\s*[<(]"),
    re.compile(r"^\s*export\s+const\s+([A-Z]\w*)\s*[:=]"),
)
PASCAL = re.compile(r"^[A-Z]\w*$")

ROUTE_NAMES = {"page", "layout", "template", "error", "not-found", "loading", "global-error", "default", "route"}
ROUTE_DIRS = ("app/", "src/app/")
PAGES_DIRS = ("pages/", "src/pages/")
REMIX_DIRS = ("app/routes/", "src/routes/", "routes/")
REMIX_FILES = {"app/root", "app/routes", "src/root", "src/routes"}
VITE_ENTRIES = {"src/main", "src/index"}
IMPORT_SPECIFIER = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*)['"]([^'"]+)['"]""")
RESOLVE_SUFFIXES = ("", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js", "/index.jsx")


def _stem(path):
    return path.rsplit(".", 1)[0] if "." in path.rsplit("/", 1)[-1] else path


def is_web_route(path):
    """Whether a file is a framework route: a root nothing in the product has to import."""
    path = path.lstrip("./")
    stem = _stem(path)
    name = stem.rsplit("/", 1)[-1]
    if path.startswith(ROUTE_DIRS) and name in ROUTE_NAMES:
        return True
    if path.startswith(PAGES_DIRS + REMIX_DIRS):
        return True
    return stem in REMIX_FILES or stem in VITE_ENTRIES


def _resolve(importer, specifier, known):
    """The tracked file a relative or ``@/`` import names, or None."""
    if specifier.startswith("."):
        parts = importer.split("/")[:-1]
        for piece in specifier.split("/"):
            if piece == "..":
                if parts:
                    parts.pop()
            elif piece != ".":
                parts.append(piece)
        bases = ["/".join(parts)]
    elif specifier.startswith("@/"):
        bases = ["src/" + specifier[2:], specifier[2:]]
    else:
        return None
    for base in bases:
        for suffix in RESOLVE_SUFFIXES:
            if base + suffix in known:
                return base + suffix
    return None


def web_reachable_files(texts):
    """Every file reachable from a framework route over the import graph (``texts``: path -> source)."""
    known = set(texts)
    seen = {path for path in texts if is_web_route(path)}
    queue = list(seen)
    while queue:
        path = queue.pop()
        for specifier in IMPORT_SPECIFIER.findall(texts[path]):
            target = _resolve(path, specifier, known)
            if target and target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def _comment_tag(lines, index):
    """The task named by a ``not-mounted-yet:`` tag in the comment lines just above ``index``."""
    for back in range(1, TAG_LOOKBACK + 1):
        if index - back < 0:
            return None
        line = lines[index - back].strip()
        if not (line.startswith(("///", "//", "/**", "/*", "*", "#")) or line.startswith("@")):
            return None
        match = TAG.search(line)
        if match:
            return match.group(1).strip().rstrip("*/ ").strip()
    return None


def swift_declarations(lines):
    out = []
    for index, line in enumerate(lines):
        match = SWIFT_VIEW.match(line)
        if match:
            out.append((index + 1, match.group(1), _comment_tag(lines, index)))
    return out


def kotlin_declarations(lines):
    out = []
    for index, line in enumerate(lines):
        match = KOTLIN_FUN.match(line)
        if not match or match.group(1) in ("private", "internal"):
            continue
        # the annotations sit on the lines just above; a @Preview function is a preview
        annotations = set()
        back = index - 1
        while back >= 0 and KOTLIN_ANNOTATION.match(lines[back]):
            annotations.add(KOTLIN_ANNOTATION.match(lines[back]).group(1))
            back -= 1
        if "Composable" not in annotations or "Preview" in annotations:
            continue
        out.append((index + 1, match.group(2), _comment_tag(lines, back + 1)))
    return out


def ts_declarations(lines):
    out = []
    for index, line in enumerate(lines):
        for pattern in TS_EXPORTS:
            match = pattern.match(line)
            if match:
                out.append((index + 1, match.group(1), _comment_tag(lines, index)))
                break
    return out


DECLARATIONS = {"swift": swift_declarations, "kotlin": kotlin_declarations, "ts": ts_declarations}


def _without_preview_blocks(language, lines):
    """The lines with Swift ``#Preview { … }`` blocks and Kotlin ``@Preview`` functions blanked —
    a preview constructs the view it previews, and is not a route."""
    out = list(lines)
    count = len(lines)
    index = 0
    while index < count:
        stripped = lines[index].strip()
        start = None
        if language == "swift" and stripped.startswith("#Preview"):
            start = index
        elif language == "kotlin" and KOTLIN_ANNOTATION.match(stripped) and KOTLIN_ANNOTATION.match(stripped).group(1) == "Preview":
            probe = index
            while probe < count and (KOTLIN_ANNOTATION.match(lines[probe].strip()) or not lines[probe].strip()):
                out[probe] = ""
                probe += 1
            if probe < count and KOTLIN_FUN.match(lines[probe]):
                start = probe
            else:
                index = probe
                continue
        if start is None:
            index += 1
            continue
        depth = 0
        opened = False
        probe = start
        while probe < count:
            depth += lines[probe].count("{") - lines[probe].count("}")
            opened = opened or "{" in lines[probe]
            out[probe] = ""
            probe += 1
            if opened and depth <= 0:
                break
        index = probe
    return out


def construction_sites(language, name, lines):
    """Whether ``lines`` (previews already blanked) construct ``name``."""
    if language == "ts":
        pattern = re.compile(r"(?<![\w.])(?:<" + name + r"(?=[\s/>])|" + name + r"\s*\(|(?:component|element|Component|screen)\s*[:=]\s*" + name + r"\b)")
    else:
        pattern = re.compile(r"(?<![\w.])" + name + r"\s*[(<]")
    return any(pattern.search(line) for line in lines)


def failures_for(platform, paths, files, texts=None):
    language = LANGUAGE_OF_PLATFORM.get(platform)
    if language is None:
        return []
    texts = texts or {}
    extensions = EXTENSIONS[language]

    def read(path):
        if path not in texts:
            try:
                with open(path, encoding="utf-8", errors="replace") as handle:
                    texts[path] = handle.read()
            except OSError:
                texts[path] = ""
        return texts[path]

    code = [path for path in files if path.endswith(extensions)]
    declared = []   # (path, line, name, tag)
    product = {}    # path -> lines with previews blanked, for every file that may hold a route
    for path in code:
        path_class = paths.classify(path)
        if path_class in EXCLUDED_CLASSES:
            continue
        lines = read(path).splitlines()
        product[path] = _without_preview_blocks(language, lines)
        if language in ("kotlin", "ts") and path_class not in ("ui", "ui_lib"):
            continue
        for line, name, tag in DECLARATIONS[language](lines):
            if language != "swift" and not PASCAL.match(name):
                continue
            declared.append((path, line, name, tag))

    on_routes = set()
    if platform == "web":
        on_routes = web_reachable_files({path: "\n".join(lines) for path, lines in product.items()})

    failures = []
    for path, line, name, tag in declared:
        if tag or path in on_routes:
            continue
        own = product.get(path, [])
        own_without_declaration = [text for number, text in enumerate(own, 1) if number != line]
        reached = construction_sites(language, name, own_without_declaration) or any(
            construction_sites(language, name, lines) for other, lines in product.items() if other != path)
        if not reached:
            failures.append((path, line,
                             f"{name} is built and nothing on a route in the product constructs it (a gallery, "
                             f"preview or test is not a route) — mount it, or write `not-mounted-yet: <the task>` "
                             f"in the comment above it"))
    return failures
