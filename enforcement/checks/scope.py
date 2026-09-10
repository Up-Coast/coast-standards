#!/usr/bin/env python3
"""What a push changed, and what the battery therefore runs (enforcement task E8).

    scope.py [--platform <p>] [--files-to <listing>] [--measured-to <listing>] <base>:<tip> …

The pushed ranges' changed paths are classified with the scanner's own path classes
(``paths.json``, the project's bindings merged in). The answer is printed as shell
assignments the pre-push hook ``eval``s:

    scope_kind=none|files|all   none: no code changed, every code seat is skipped;
                                files: code changed, the seats run on it; all: the
                                checks themselves changed (a governing or manifest
                                path), a file no module owns, or SCOPE=all — everything
    scope_reason='…'            the plain-words reason, printed by the seats
    scope_modules=0|1           1 when a module graph limited the build and the tests
    scope_targets='A B'         the affected targets that the build compiles (changed + dependents)
    scope_test_targets='ATests' the affected test targets
    scope_test_filter='^(ATests)\\.'   the ``swift test --filter`` expression for them
    scope_files=<n>             how many changed code files still exist and carry a
                                platform source extension — the listing --files-to writes,
                                one path per line, for the seats that take a file list
    scope_measured=<n>          how many files the affected targets own — the listing
                                --measured-to writes; a scoped build's warning count is
                                judged against those files' baseline (check_rules.py --measured)
    scope_tests=<n>             how many test FILES the change reaches (Python: the test
                                files whose imports lead to a changed file) — the listing
                                --tests-to writes, for a runner that takes test files

A path in one of ``not_code_classes`` (docs, plans, the design bundle, generated files)
or with one of ``prose_extensions`` is not code. A path in one of ``full_run_classes``
(governing, manifest) means everything runs. The module graph is the platform's own:

    ios / macos     ``swift package describe`` — targets, their folders, their dependencies;
                    a test target is one of type ``test``
    android         ``settings.gradle[.kts]`` names the modules (``include ':app', ':core'``),
                    each module's ``build.gradle[.kts]`` names its ``project(':x')``
                    dependencies; a module's tests live inside it, so the affected
                    modules ARE the test targets (``./gradlew :m:test``)
    react-native    the root ``package.json``'s ``workspaces``: each workspace is a module,
    / web           its ``dependencies`` on sibling workspaces the edges; a project with no
                    workspaces has no module graph, and the hook hands the changed files
                    to ``jest --findRelatedTests`` or ``vitest related`` instead
    python          every tracked ``.py`` file is a node and its imports (resolved to
                    files in the tree, the src layout included) are the edges — the test
                    files the change reaches are the ones to run

An Xcode project has none the hook reads, so its build and tests run whole when code
changed while its lint and format seats still take the file list. ``<prefix>SCOPE=all``
in the environment (the layout's prefix, ``COAST_`` by default) forces everything —
CI's word, or a person's. GOVERNING: agents never edit the files that define their own checks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_rules  # noqa: E402 — the path classes, the git helper and the tables, beside this file
import import_matrix  # noqa: E402 — the import readers, beside this file (one reader per language)

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
KINDS = ("none", "files", "all")


def scope_lists():
    with open(check_rules.PATHS_FILE, encoding="utf-8") as handle:
        table = json.load(handle)
    return (tuple(table.get("not_code_classes", ())), tuple(table.get("full_run_classes", ())),
            tuple(ext.lower() for ext in table.get("prose_extensions", ())))


def changed_paths(ranges):
    """Every path a pushed range touches, deletions included — a deleted file changes its module too."""
    paths = set()
    for base, tip in ranges:
        out = check_rules.git("diff", "--name-only", base, tip)
        paths.update(line for line in out.splitlines() if line)
    return sorted(paths)


def classify(paths_table, path, not_code, full_run, prose):
    """'prose', 'full' or 'code' for one changed path."""
    cls = paths_table.classify(path)
    if cls in full_run:
        return "full"
    if cls in not_code or os.path.splitext(path)[1].lower() in prose:
        return "prose"
    return "code"


# ---------------------------------------------------------------- the module graph


def swiftpm_graph():
    """[{name, type, path, sources, deps}] from ``swift package describe``, or None without a package."""
    if not os.path.isfile("Package.swift"):
        return None
    done = subprocess.run(["swift", "package", "describe", "--type", "json"], capture_output=True, text=True)
    if done.returncode != 0:
        return None
    try:
        targets = json.loads(done.stdout).get("targets", [])
    except ValueError:
        return None
    graph = []
    for target in targets:
        if not isinstance(target, dict) or "name" not in target:
            continue
        graph.append({"name": target["name"], "type": target.get("type", "library"),
                      "path": (target.get("path") or "").strip("/"), "sources": target.get("sources") or [],
                      "deps": [d for d in target.get("target_dependencies") or [] if isinstance(d, str)]})
    return graph or None


GRADLE_INCLUDE = re.compile(r"""include\s*\(?\s*((?:['"]:[^'"]*['"]\s*,?\s*)+)\)?""")
GRADLE_MODULE = re.compile(r"""['"](:[^'"]+)['"]""")
GRADLE_PROJECT = re.compile(r"""project\s*\(\s*(?:path\s*[:=]\s*)?['"](:[^'"]+)['"]""")


def gradle_graph():
    """[{name, type, path, sources, deps}] from settings.gradle(.kts) and each module's build
    file, or None without a settings file. A module is ``:a:b`` at ``a/b``; its dependencies
    are the ``project(':x')`` references in its build file; an application plugin makes it
    the app. Tests live inside a module, so every module is its own test target."""
    settings = next((name for name in ("settings.gradle.kts", "settings.gradle") if os.path.isfile(name)), None)
    if settings is None:
        return None
    with open(settings, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    names = []
    for match in GRADLE_INCLUDE.finditer(text):
        names.extend(GRADLE_MODULE.findall(match.group(1)))
    names = sorted(set(names))
    if not names:
        return None
    graph = []
    for name in names:
        folder = name.strip(":").replace(":", "/")
        build = next((b for b in (f"{folder}/build.gradle.kts", f"{folder}/build.gradle") if os.path.isfile(b)), None)
        deps, kind = [], "library"
        if build:
            with open(build, encoding="utf-8", errors="replace") as handle:
                body = handle.read()
            deps = sorted({d for d in GRADLE_PROJECT.findall(body) if d in names and d != name})
            if "com.android.application" in body or re.search(r"""(?<![\w.])application(?![\w.-])""", body):
                kind = "app"
        graph.append({"name": name, "type": kind, "path": folder, "sources": [], "deps": deps})
    return graph


def npm_graph():
    """[{name, type, path, sources, deps}] from the root package.json's workspaces, or None
    without workspaces. Each workspace folder with a package.json is a module named as the
    package is; a dependency on a sibling workspace is an edge."""
    if not os.path.isfile("package.json"):
        return None
    try:
        with open("package.json", encoding="utf-8") as handle:
            root = json.load(handle)
    except (OSError, ValueError):
        return None
    patterns = root.get("workspaces")
    if isinstance(patterns, dict):
        patterns = patterns.get("packages")
    if not isinstance(patterns, list) or not patterns:
        return None
    import glob
    folders = []
    for pattern in patterns:
        if not isinstance(pattern, str):
            continue
        folders.extend(sorted(f.rstrip("/") for f in glob.glob(pattern) if os.path.isfile(os.path.join(f, "package.json"))))
    modules = {}
    for folder in folders:
        try:
            with open(os.path.join(folder, "package.json"), encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            continue
        name = data.get("name") or folder
        wants = set()
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            wants.update((data.get(key) or {}).keys())
        modules[name] = {"name": name, "type": "library", "path": folder, "sources": [], "deps": wants}
    if not modules:
        return None
    for module in modules.values():
        module["deps"] = sorted(d for d in module["deps"] if d in modules and d != module["name"])
    return [modules[k] for k in sorted(modules)]


def python_graph(is_test):
    """One node per tracked .py file, its imports resolved to files in the tree as the edges
    (``import_matrix.python_read`` reads them; the src layout and relative imports included).
    A node is a ``test`` when the path classes say so, so the test files a change reaches are
    the closure's tests. None when the tree holds no Python."""
    files = [p for p in check_rules.tree_files(False) if p.endswith(".py")]
    if not files:
        return None
    present = set(files)
    roots = [r for r in ("src", "") if r == "" or os.path.isdir(r)]
    names = set()
    for root in roots:
        for entry in os.listdir(root or "."):
            names.add(entry[:-3] if entry.endswith(".py") else entry)

    def package_of(path):
        parts = path.split("/")[:-1]
        if parts and parts[0] == "src":
            parts = parts[1:]
        return parts

    def resolve(parts):
        for root in roots:
            base = "/".join(([root] if root else []) + parts)
            for candidate in (base + ".py", base + "/__init__.py"):
                if candidate in present:
                    return candidate
        return None

    graph = []
    for path in files:
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            continue
        _foreign, own = import_matrix.python_read(text, package_of(path), names)
        deps = set()
        for parts in own:
            for length in range(len(parts), 0, -1):
                found = resolve(parts[:length])
                if found and found != path:
                    deps.add(found)
                    break
        graph.append({"name": path, "type": "test" if is_test(path) else "library", "path": path, "sources": [], "deps": sorted(deps)})
    return graph


def owner(graph, path):
    """The target whose folder holds the path (the longest match), or None."""
    best = None
    for target in graph:
        folder = target["path"]
        if folder and (path == folder or path.startswith(folder + "/")):
            if best is None or len(folder) > len(best["path"]):
                best = target
    return best


def affected(graph, changed_targets):
    """The changed targets and every target that depends on one of them, transitively."""
    dependents = {}
    for target in graph:
        for dep in target["deps"]:
            dependents.setdefault(dep, set()).add(target["name"])
    seen = set()
    queue = list(changed_targets)
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        queue.extend(dependents.get(name, ()))
    return sorted(seen)


def test_filter(test_targets):
    return "^(" + "|".join(re.escape(name) for name in test_targets) + r")\." if test_targets else ""


# ---------------------------------------------------------------- the answer


class Scope:
    def __init__(self, kind, reason, modules=False, targets=(), test_targets=(), files=(), measured=(), tests=()):
        self.kind, self.reason, self.modules = kind, reason, modules
        self.targets, self.test_targets = list(targets), list(test_targets)
        self.files, self.measured, self.tests = list(files), list(measured), list(tests)

    def to_sh(self):
        lines = [f"scope_kind={self.kind}", f"scope_reason={shlex.quote(self.reason)}",
                 f"scope_modules={1 if self.modules else 0}",
                 f"scope_targets={shlex.quote(' '.join(self.targets))}",
                 f"scope_test_targets={shlex.quote(' '.join(self.test_targets))}",
                 f"scope_test_filter={shlex.quote(test_filter(self.test_targets))}",
                 f"scope_files={len(self.files)}", f"scope_measured={len(self.measured)}", f"scope_tests={len(self.tests)}"]
        return "\n".join(lines) + "\n"


def decide(paths, paths_table, extensions, graph, forced=False, lists=None, flavour="swiftpm"):
    """The Scope for the changed paths. ``graph`` is the module graph, None, or a function that
    reads it — called only when a code change needs it. ``flavour`` says how the graph's nodes
    test: ``swiftpm`` (test targets of type test), ``gradle`` (every affected module runs its
    own tests), ``files`` (the nodes are files; the affected test files are listed)."""
    not_code, full_run, prose = lists or scope_lists()
    if forced:
        return Scope("all", "everything — the environment asked for the whole battery")
    kinds = {path: classify(paths_table, path, not_code, full_run, prose) for path in paths}
    full = sorted(p for p, k in kinds.items() if k == "full")
    if full:
        return Scope("all", f"the checks themselves changed ({', '.join(full[:3])}{', …' if len(full) > 3 else ''})")
    code = sorted(p for p, k in kinds.items() if k == "code")
    if not code:
        return Scope("none", "documents and plans only" if paths else "nothing changed")
    files = [p for p in code if os.path.isfile(p) and p.lower().endswith(tuple(extensions))]
    if callable(graph):
        graph = graph()   # read only now: a push of documents alone never asks the package
    if graph is None:
        return Scope("files", f"{len(code)} code file(s) changed; no module graph, so the build and the tests run whole",
                     modules=False, files=files)
    changed_targets = set()
    for path in code:
        target = owner(graph, path)
        if target is None:
            return Scope("all", f"{path} belongs to no target of the package, so everything runs")
        changed_targets.add(target["name"])
    names = affected(graph, changed_targets)
    by_name = {t["name"]: t for t in graph}
    tests = [n for n in names if by_name[n]["type"] == "test"]
    built = [n for n in names if by_name[n]["type"] != "test"]
    if flavour == "files":
        reason = f"{len(code)} code file(s); {len(names)} file(s) import them, {len(tests)} of them test files"
        return Scope("files", reason, modules=True, targets=[], test_targets=[], files=files, tests=tests)
    if flavour == "gradle":
        reason = f"{len(code)} code file(s) in {', '.join(sorted(changed_targets))}; affected modules: {', '.join(names)}"
        return Scope("files", reason, modules=True, targets=names, test_targets=names, files=files)
    measured = []
    for name in built:
        target = by_name[name]
        measured.extend(f"{target['path']}/{source}" if target["path"] else source for source in target["sources"])
    reason = f"{len(code)} code file(s) in {', '.join(sorted(changed_targets))}; affected: {', '.join(names)}"
    return Scope("files", reason, modules=True, targets=built, test_targets=tests, files=files, measured=sorted(set(measured)))


def parse_range(text):
    if ":" not in text:
        raise argparse.ArgumentTypeError(f"a range is <base>:<tip>, not {text!r}")
    base, tip = text.split(":", 1)
    return base or EMPTY_TREE, tip


def main(argv=None):
    parser = argparse.ArgumentParser(description="What a push changed, and what the battery runs.")
    parser.add_argument("ranges", nargs="*", type=parse_range, metavar="BASE:TIP")
    parser.add_argument("--platform", default=check_rules.LAYOUT.env_value("PLATFORM"))
    parser.add_argument("--files-to", metavar="LISTING", help="write the changed source files here, one per line")
    parser.add_argument("--measured-to", metavar="LISTING", help="write the affected targets' files here, one per line")
    parser.add_argument("--tests-to", metavar="LISTING", help="write the test files the change reaches here, one per line")
    parser.add_argument("--all", action="store_true", help="answer 'all' without looking (the hook's --measure mode)")
    args = parser.parse_args(argv)
    _signatures, paths_table = check_rules.load_tables(args.platform)
    forced = args.all or (check_rules.LAYOUT.env_value("SCOPE") or "").strip().lower() == "all"
    paths = [] if forced else changed_paths(args.ranges)
    graph, flavour = None, "swiftpm"
    if args.platform in ("ios", "macos"):
        graph = swiftpm_graph
    elif args.platform == "android":
        graph, flavour = gradle_graph, "gradle"
    elif args.platform in ("react-native", "web"):
        graph = npm_graph
    elif args.platform == "python":
        graph, flavour = (lambda: python_graph(lambda p: paths_table.classify(p) == "tests")), "files"
    scope = decide(paths, paths_table, paths_table.extensions, graph, forced=forced, flavour=flavour)
    for listing, lines in ((args.files_to, scope.files), (args.measured_to, scope.measured), (args.tests_to, scope.tests)):
        if listing:
            with open(listing, "w", encoding="utf-8") as handle:
                handle.write("".join(line + "\n" for line in lines))
    sys.stdout.write(scope.to_sh())
    return 0


if __name__ == "__main__":
    sys.exit(main())
