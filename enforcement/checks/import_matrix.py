#!/usr/bin/env python3
"""Import-matrix checker — absorbed from Coast's own check_import_matrix.py under the rules scanner in E1.1; the judgments are unchanged, check_rules.py calls failures_for(). Original docstring follows.

Coast import-matrix checker — the deterministic layering gate (taxonomy §2; M5 H54a).

The structural taxonomy's module layering is enforced here as a pure function
of the checkout, so CI holds it even when the compiler would happily link a
forbidden import:

  - feature modules never import each other (cross-feature needs route
    through Domain or DesignSystem);
  - nothing but the app target imports Data (features see repositories only
    as Domain protocols);
  - Domain imports nothing app-side — no other module, no UI or data framework.

Module KINDS come from the state dir's `module-kinds.json` when the project wrote one
({"app": [...], "feature": [...], "shared": [...]}), else from the taxonomy's
standard names: Domain, Data, DesignSystem, Strings, AppFoundation, Shared and
SharedUI are shared; a target named App or ending in "App" is the app target;
every other target is a feature module.

This is the ONE implementation (T164): Coast's own local gate battery runs
this file before every push, and the gates workflow runs it in CI. There is
no Swift copy. Ships in the scaffolded repo under the GOVERNING class
(agents cannot touch it — D12). No network, no ledger access, no model calls.

WHICH layout is walked is the project's platform (P3): iOS and macOS read the
Swift package tree (`Sources/<T>/**`, `Modules/<M>/Sources/**`); Android the
Gradle tree (any `<name>/src/main/{kotlin,java}/**`, imports resolved by
declared package); React Native and Web the Node tree (`Modules/<M>/src/**`,
else the package's root `src/` as one module named after the package,
relative imports resolved by path). Tests, generated trees and dependencies
are never product code.

Usage: check_import_matrix.py [--platform <name>]   (run from the repository root;
       the platform also comes from COAST_PLATFORM, which the shipped workflow sets)
"""
import json
import os
import re
import sys

import layout as _layout  # noqa: E402 — the state dir's name comes from the layout table (E5.1)
KINDS_FILE = _layout.load().state_file("module-kinds.json")
SHARED_NAMES = {"Domain", "Data", "DesignSystem", "Strings", "AppFoundation", "Shared", "SharedUI"}
DOMAIN = "Domain"
DATA = "Data"
DOMAIN_FORBIDDEN_FRAMEWORKS = {"SwiftUI", "UIKit", "AppKit", "CoreData", "SwiftData", "GRDB", "SQLite3", "Realm"}
DECLARATION_WORDS = {"struct", "class", "enum", "protocol", "typealias", "func", "let", "var"}
HEAVY_DIRECTORIES = {".git", ".gradle", "node_modules", ".build", "intermediates",
                     "Pods", ".idea", "DerivedData", "caches", "tmp"}

LAYOUT_OF_PLATFORM = {"ios": "swift-package", "macos": "swift-package", "android": "gradle",
                      "react-native": "node", "web": "node"}
EXTENSIONS_OF_LAYOUT = {"swift-package": (".swift",), "gradle": (".kt", ".java"),
                        "node": (".ts", ".tsx", ".js", ".jsx")}


def default_kind(module):
    if module in SHARED_NAMES:
        return "shared"
    if module == "App" or module.endswith("App"):
        return "app"
    return "feature"


def kinds_for(modules):
    by_module = {}
    if os.path.exists(KINDS_FILE):
        with open(KINDS_FILE, encoding="utf-8") as handle:
            declared = json.load(handle)
        for kind in ("app", "feature", "shared"):
            for name in declared.get(kind, []):
                by_module[name] = kind
    for module in modules:
        by_module.setdefault(module, default_kind(module))
    return by_module


# ---- The walk (one layout rule, the same as Coast's own source walker) ----

def is_product_file(layout, name):
    if not name.endswith(EXTENSIONS_OF_LAYOUT[layout]):
        return False
    if layout == "node":
        if name.endswith(".d.ts"):
            return False
        if any(marker in name for marker in (".test.", ".spec.", ".stories.")):
            return False
    return True


def location(parts, layout, root_module):
    """(module, root) for a repository-relative path, or None."""
    if len(parts) < 2 or any(p in HEAVY_DIRECTORIES for p in parts[:-1]):
        return None
    if layout == "swift-package":
        if len(parts) >= 3 and parts[0] == "Sources":
            return parts[1], "Sources/" + parts[1]
        if len(parts) >= 4 and parts[0] == "Modules" and parts[2] == "Sources":
            return parts[1], "Modules/" + parts[1] + "/Sources"
        return None
    if layout == "gradle":
        if "src" not in parts:
            return None
        src = parts.index("src")
        if src < 1 or src + 1 >= len(parts) or parts[src + 1] != "main" or "build" in parts[:src]:
            return None
        return parts[src - 1], "/".join(parts[:src + 2])
    if layout == "node":
        if any(p in ("__tests__", "__mocks__") for p in parts[:-1]):
            return None
        if len(parts) >= 4 and parts[0] == "Modules" and parts[2] == "src":
            return parts[1], "Modules/" + parts[1] + "/src"
        if len(parts) >= 2 and parts[0] == "src" and root_module:
            return root_module, "src"
        return None
    return None


def skips_directory(parts, layout):
    name = parts[-1]
    if name in HEAVY_DIRECTORIES:
        return True
    if layout == "gradle":
        return name == "build"
    if layout == "node":
        return len(parts) == 1 and name in ("dist", "build")
    return False


def root_module_name(layout):
    if layout != "node":
        return None
    name = None
    if os.path.exists("package.json"):
        try:
            with open("package.json", encoding="utf-8") as handle:
                name = json.load(handle).get("name")
        except (ValueError, OSError):
            name = None
    if name:
        name = name.split("/")[-1]
    return name or "app"


def walk(layout, root_module):
    by_module = {}
    for dirpath, dirnames, filenames in os.walk("."):
        rel_dir = os.path.relpath(dirpath, ".")
        keep = []
        for d in sorted(dirnames):
            rel = d if rel_dir == "." else rel_dir + "/" + d
            if not skips_directory(rel.split("/"), layout):
                keep.append(d)
        dirnames[:] = keep
        for name in sorted(filenames):
            if not is_product_file(layout, name):
                continue
            rel = name if rel_dir == "." else rel_dir + "/" + name
            found = location(rel.split("/"), layout, root_module)
            if found:
                by_module.setdefault(found[0], []).append(rel)
    return by_module


# ---- The import readers, per language ----

def string_opener(text, i):
    """If text[i:] opens a Swift string literal, return (closing delimiter,
    opener length, escape prefix). Covers plain "…", multiline \"\"\"…\"\"\",
    and raw #"…"#/#\"\"\"…\"\"\"# forms — in a raw string the escape is
    backslash-hashes, and the closing delimiter carries the hashes."""
    j = i
    hashes = 0
    while j < len(text) and text[j] == "#":
        hashes += 1
        j += 1
    if j >= len(text) or text[j] != '"':
        return None
    if text.startswith('"""', j):
        return ('"""' + "#" * hashes, (j - i) + 3, "\\" + "#" * hashes)
    return ('"' + "#" * hashes, (j - i) + 1, "\\" + "#" * hashes)


def strip_comments(text):
    """Swift text with comments removed. A character scan, not a regex:
    string literals are tracked — plain, MULTILINE and raw forms, so a
    bare quote or a "/*" inside a string body cannot swallow the rest of
    the file — and Swift's NESTED block comments close where Swift closes
    them. Newlines survive so nothing shifts lines. String contents are
    blanked (never scanned for imports)."""
    out = []
    i, n = 0, len(text)
    depth = 0            # block-comment nesting
    in_line = False      # inside //
    closing = None       # the delimiter that ends the current string
    escape = "\\"        # the current string's escape prefix
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_line:
            if c == "\n":
                in_line = False
                out.append(c)
            i += 1
        elif depth:
            if c == "/" and nxt == "*":
                depth += 1
                i += 2
            elif c == "*" and nxt == "/":
                depth -= 1
                i += 2
            else:
                if c == "\n":
                    out.append(c)
                i += 1
        elif closing is not None:
            if text.startswith(escape, i):
                i += len(escape) + 1
            elif text.startswith(closing, i):
                out.append('""')  # a blank literal keeps the line's shape
                i += len(closing)
                closing = None
            else:
                if c == "\n":
                    out.append(c)
                i += 1
        elif (c == '"' or c == "#") and string_opener(text, i):
            closing, opener_len, escape = string_opener(text, i)
            i += opener_len
        elif c == "/" and nxt == "/":
            in_line = True
            i += 2
        elif c == "/" and nxt == "*":
            depth = 1
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def imports_in(text):
    """Swift: `import X`, `@testable import X`, `import struct X.Y` —
    every statement on a line (`import A; import B` hides nothing)."""
    found = []
    for raw in strip_comments(text).split("\n"):
        for statement in raw.split(";"):
            line = statement.strip()
            if not (line.startswith("import ") or " import " in line):
                continue
            words = [w for w in line.split(" ") if w]
            if "import" not in words:
                continue
            at = words.index("import")
            rest = [w for w in words[at + 1:] if w not in DECLARATION_WORDS]
            if not rest:
                continue
            found.append(rest[0].split(".")[0])
    return found


def kotlin_read(text):
    """(declared package, [imports]) — Kotlin and Java."""
    package = None
    imports = []
    for raw in text.split("\n"):
        line = raw.strip()
        if line.startswith("package "):
            package = line[8:].strip(" ;")
        elif line.startswith("import "):
            name = line[7:].strip(" ;")
            if name.startswith("static "):
                name = name[7:]
            if " as " in name:
                name = name.split(" as ")[0]
            imports.append(name)
    return package, imports


NAMED_LIST_OPEN = re.compile(r"^(?:import|export)\s+(?:type\s+)?(?:[\w$]+\s*,\s*)?\{[^}]*$")


def typescript_imports(text):
    """The module specifiers of the real import forms only. A named list broken over
    several lines (`import {\n  a,\n  b,\n} from "x"`) is read as one statement."""
    def quoted(fragment):
        fragment = fragment.lstrip()
        if not fragment or fragment[0] not in "\"'":
            return None
        end = fragment.find(fragment[0], 1)
        return fragment[1:end] if end > 1 else None

    specifiers = []
    pending = None  # an `import {` / `export {` whose named list is still open (prettier's one-name-per-line form)
    for raw in text.split("\n"):
        line = raw.strip()
        if pending is not None:
            pending += " " + line
            if "}" not in line:
                continue
            line, pending = pending, None
        elif NAMED_LIST_OPEN.match(line):
            pending = line
            continue
        if line.startswith("import ") or line.startswith("export "):
            at = line.rfind(" from ")
            spec = quoted(line[at + 6:]) if at >= 0 else None
            if spec is None and line.startswith("import "):
                spec = quoted(line[7:])
            if spec:
                specifiers.append(spec)
        search = line
        while "require(" in search:
            search = search[search.index("require(") + 8:]
            spec = quoted(search)
            if spec:
                specifiers.append(spec)
    return specifiers


def resolve(layout, module, path, imports, modules, packages, root_module):
    """The project modules a file's imports resolve to (never its own)."""
    resolved = set()
    for name in imports:
        if layout == "swift-package":
            if name in modules:
                resolved.add(name)
        elif layout == "gradle":
            for other, declared in packages.items():
                if any(name == p or name.startswith(p + ".") for p in declared):
                    resolved.add(other)
        else:
            if not name.startswith("."):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(path), name))
            if target.startswith(".."):
                continue
            probe = target if "." in os.path.basename(target) else target + "/index.ts"
            found = location(probe.split("/"), layout, root_module)
            if found and found[0] in modules:
                resolved.add(found[0])
    resolved.discard(module)
    return resolved


def judge(importer, imported, kinds):
    importer_kind = kinds.get(importer, default_kind(importer))
    imported_is_module = imported in kinds
    if importer == DOMAIN:
        if imported_is_module:
            return ("domain-imports-nothing",
                    f"Domain imports {imported} — Domain is the stable centre and imports nothing app-side")
        if imported in DOMAIN_FORBIDDEN_FRAMEWORKS:
            return ("domain-imports-nothing", f"Domain imports {imported} — no UI or data framework belongs in Domain")
        return None
    if not imported_is_module:
        return None
    if imported == DATA and importer_kind != "app":
        return ("only-app-imports-data",
                f"{importer} imports Data — only the app target wires Data in; features see repositories as Domain protocols")
    if importer_kind == "feature" and kinds.get(imported) == "feature":
        return ("features-never-import-each-other",
                f"{importer} imports {imported} — feature modules never import each other; route shared logic through Domain or shared UI through DesignSystem")
    return None


def failures_for(platform):
    """The layering failures for one platform, as (path, words) pairs — the
    same judgments main() prints, for check_rules.py to fold under its runner."""
    layout = LAYOUT_OF_PLATFORM.get(platform)
    if layout is None:
        raise SystemExit(f"import_matrix: unknown platform '{platform}' "
                         f"(expected one of {', '.join(sorted(LAYOUT_OF_PLATFORM))})")
    root_module = root_module_name(layout)
    by_module = walk(layout, root_module)
    modules = set(by_module)
    kinds = kinds_for(modules)

    texts = {}
    packages = {}
    for module, paths in by_module.items():
        for path in paths:
            with open(path, encoding="utf-8", errors="replace") as handle:
                texts[path] = handle.read()
            if layout == "gradle":
                package, _ = kotlin_read(texts[path])
                if package:
                    packages.setdefault(module, []).append(package)

    failures = []
    for module in sorted(by_module):
        for path in sorted(by_module[module]):
            text = texts[path]
            if layout == "swift-package":
                raw = imports_in(text)
            elif layout == "gradle":
                raw = kotlin_read(text)[1]
            else:
                raw = typescript_imports(text)
            imported = set(raw) | resolve(layout, module, path, raw, modules, packages, root_module)
            for name in sorted(imported):
                if name == module:
                    continue
                verdict = judge(module, name, kinds)
                if verdict:
                    rule, words = verdict
                    failures.append((path, f"{words} [{rule}]"))
    return failures, layout, bool(by_module)


def main():
    args = sys.argv[1:]
    platform = os.environ.get("COAST_PLATFORM") or None
    if len(args) == 2 and args[0] == "--platform":
        platform = args[1]
    elif args:
        print("usage: import_matrix.py [--platform <name>]")
        return 2
    if platform is None:
        raise SystemExit("import_matrix.py: the project's platform is not known — set COAST_PLATFORM "
                         "(the shipped workflow does) or pass --platform <name>; expected one of "
                         + ", ".join(sorted(LAYOUT_OF_PLATFORM)))
    failures, layout, judged = failures_for(platform)
    if failures:
        for path, words in failures:
            print(f"FAIL import-matrix {path}: {words}")
        return 1
    if not judged:
        # Honest, never silent: nothing matched the platform's layout, so
        # nothing was judged. Still a pass (a repo may predate the layout),
        # but a misconfigured platform must be visible in the check's words.
        print(f"PASS import-matrix (taxonomy §2) — no modules found under the {layout} layout; nothing was judged")
        return 0
    print("PASS import-matrix (taxonomy §2)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
