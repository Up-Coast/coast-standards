#!/usr/bin/env python3
"""check_rules.py — the rules scanner (enforcement task E1.1).

One runner for every machine-held rule: per-platform signature tables
(``rules_signatures.json``) scoped by path class (``paths.json``), run over
the lines a change ADDS, the staged diff, named files, or the whole tree.
Design: ``enforcement/README.md`` §4.2. It absorbs Coast's two existing
checkers without changing their judgments: the native-pattern signature
lists are the ``native-pattern`` group in the tables (same ids, same
patterns, same plan-approved exceptions), and the import matrix runs as the
built-in ``import-matrix`` (``import_matrix.py`` beside this file).

Usage::

    check_rules.py <base> <head> --platform <p>      # lines added between two commits
    check_rules.py <base> WORKTREE --platform <p>    # tracked changes since base + every untracked file
    check_rules.py --staged --platform <p>           # the index (a pre-commit hook)
    check_rules.py --files a b c --platform <p>      # whole files (an editor hook; every line is new)
    check_rules.py --tree --platform <p>             # no diff: only the tree-scope and ratchet signatures

The platform also comes from ``COAST_PLATFORM``. Run from the repository
root. Exit 0 = pass; any failure prints
``FAIL <check> <path>:<line>:<id>: <words> [<rule>]`` and exits 1 — the
line format the battery, the hooks, CI and Coast parse. The last line is a
JSON summary (``{"result": "pass"|"fail", ...}``).

Severities:

* ``block`` — any hit on an added line (scope ``added``) or anywhere in the
  tree (scope ``tree``) fails, unless an exception covers it.
* ``ratchet`` — counted over the whole tree and compared with
  ``.coast/ratchet-baseline.json`` (``{"baselines": [{id, count, deadline,
  written, by, moves}]}``). A count above the baseline fails; a count below
  it fails until the baseline is lowered in the same commit (the message
  says the number); a signature with no baseline entry has a baseline of 0;
  past the deadline the signature is ``block``. Nothing here writes the
  baseline.
* ``advisory`` — printed as ``ADVISORY`` lines, never a failure.

Exceptions (agents cannot write either):

* the plan's approved native deviations — Coast's mechanism, unchanged: the
  operative (last) plan-bar verdict in ``plans/<feature>/proof.json`` carries
  ``approved_native_deviations: [{file, signatures: [ids]}]``;
* ``.coast/rules-exceptions.json`` — ``{"exceptions": [{id, path, reason,
  who, when}]}`` for repos without a plan; ``path`` is an exact path or a
  ``dir/**`` glob.

A diff that touches only GOVERNING or git paths passes (gate maintenance
is the founder's own work). Stdlib only. No network. No model.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import json
import os
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNATURES_FILE = os.path.join(HERE, "rules_signatures.json")
PATHS_FILE = os.path.join(HERE, "paths.json")
BASELINE_FILE = ".coast/ratchet-baseline.json"
EXCEPTIONS_FILE = ".coast/rules-exceptions.json"
WORKTREE = "WORKTREE"
HEAVY_DIRECTORIES = {".git", ".gradle", "node_modules", ".build", "intermediates", "Pods", ".idea",
                     "DerivedData", "caches", "tmp", ".venv", "__pycache__"}


# ---------------------------------------------------------------- globs and path classes


def match_form(path):
    """Case- and NFC-insensitive comparison form (Coast's PlanScope.matchForm)."""
    return unicodedata.normalize("NFC", path).lower()


_glob_cache = {}


def glob_regex(pattern):
    """Coast's Glob semantics: ** crosses directories (x/** matches x too, **/y matches y at the root), * stays in one component."""
    if pattern in _glob_cache:
        return _glob_cache[pattern]
    normalized = match_form(pattern)
    expr = "^"
    i = 0
    while i < len(normalized):
        c = normalized[i]
        if c == "*":
            if normalized.startswith("**/", i):
                expr += "(?:.*/)?"
                i += 3
                continue
            if normalized.startswith("**", i):
                if i > 0 and normalized[i - 1] == "/" and i + 2 == len(normalized):
                    expr = expr[:-1] + "(?:/.*)?"
                else:
                    expr += ".*"
                i += 2
                continue
            expr += "[^/]*"
            i += 1
            continue
        if c == "?":
            expr += "[^/]"
        else:
            expr += "/" if c == "/" else re.escape(c)
        i += 1
    compiled = re.compile(expr + "$")
    _glob_cache[pattern] = compiled
    return compiled


def glob_matches(pattern, path):
    return glob_regex(pattern).match(match_form(path)) is not None


class PathClasses:
    """One platform's ordered class bindings; everything else is 'source'."""

    def __init__(self, table):
        self.extensions = tuple(table.get("extensions", []))
        self.order = table.get("order", [])
        self.classes = table.get("classes", {})

    def classify(self, path):
        for name in self.order:
            if any(glob_matches(pattern, path) for pattern in self.classes.get(name, [])):
                return name
        return "source"


# ---------------------------------------------------------------- git


def git(*args, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def tracked(path):
    return git("ls-files", "--error-unmatch", "--", path, check=False) != ""


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read().splitlines()


def added_lines_from_diff(diff_text):
    """[(new-file line number, text)] from a --unified=0 diff of one file."""
    lines = []
    new_line = 0
    for raw in diff_text.splitlines():
        hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
        if hunk:
            new_line = int(hunk.group(1))
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            lines.append((new_line, raw[1:]))
            new_line += 1
    return lines


def changed_files(mode, base, head):
    """[(path, [(line, text)])] for the mode — what the change adds."""
    if mode == "files":
        return [(path, list(enumerate(read_lines(path), 1))) for path in head if os.path.isfile(path)]
    if mode == "staged":
        names = git("diff", "--cached", "--name-status")
        paths = [line.split("\t")[-1] for line in names.splitlines() if line and not line.startswith("D")]
        return [(path, added_lines_from_diff(git("diff", "--cached", "--unified=0", "--", path))) for path in paths]
    if head == WORKTREE:
        names = git("diff", "--name-status", base)
        untracked = [p for p in git("ls-files", "--others", "--exclude-standard").splitlines() if p]
    else:
        names = git("diff", "--name-status", f"{base}..{head}")
        untracked = []
    paths = [line.split("\t")[-1] for line in names.splitlines() if line and not line.startswith("D")]
    out = []
    for path in paths:
        if head == WORKTREE and not tracked(path):
            continue
        diff = git("diff", base, "--unified=0", "--", path) if head == WORKTREE else git("diff", f"{base}..{head}", "--unified=0", "--", path)
        out.append((path, added_lines_from_diff(diff)))
    for path in untracked:
        if os.path.isfile(path):
            out.append((path, list(enumerate(read_lines(path), 1))))
    return out


def tree_files(include_untracked):
    files = [p for p in git("ls-files").splitlines() if p]
    if include_untracked:
        files += [p for p in git("ls-files", "--others", "--exclude-standard").splitlines() if p]
    return [p for p in files if os.path.isfile(p) and not any(part in HEAVY_DIRECTORIES for part in p.split("/"))]


# ---------------------------------------------------------------- exceptions


def approved_deviations(head, changed_paths):
    """Coast's plan-approved native deviations, read exactly as check_native_patterns.py read them."""
    ids = sorted({p.split("/")[1] for p in changed_paths if p.startswith("plans/") and p.count("/") >= 2})
    if len(ids) != 1:
        return []
    proof_path = f"plans/{ids[0]}/proof.json"
    if head in (WORKTREE, None):
        try:
            with open(proof_path, "rb") as handle:
                raw_bytes = handle.read()
        except OSError:
            return []
    else:
        raw = subprocess.run(["git", "show", f"{head}:{proof_path}"], capture_output=True)
        if raw.returncode != 0:
            return []
        raw_bytes = raw.stdout
    try:
        proof = json.loads(raw_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return []
    plan_approval = proof.get("plan_approval")
    if not isinstance(plan_approval, list) or not plan_approval:
        return []
    operative = plan_approval[-1]
    if not isinstance(operative, dict) or operative.get("verdict") != "approved":
        return []
    entries = operative.get("context", {}).get("approved_native_deviations", [])
    return [e for e in entries if isinstance(e, dict) and isinstance(e.get("file"), str) and isinstance(e.get("signatures"), list)]


def target_covers(target, path):
    """Exact match, or a 'dir/**' glob covering the path (Coast's plan-item target rule)."""
    t, p = match_form(target), match_form(path)
    if t.endswith("/**"):
        prefix = t[:-2]
        return p.startswith(prefix) or p == prefix[:-1]
    return t == p


def governed_exceptions():
    if not os.path.isfile(EXCEPTIONS_FILE):
        return []
    try:
        with open(EXCEPTIONS_FILE, encoding="utf-8") as handle:
            entries = json.load(handle).get("exceptions", [])
    except (ValueError, OSError):
        return []
    return [e for e in entries if isinstance(e, dict) and isinstance(e.get("id"), str) and isinstance(e.get("path"), str)]


# ---------------------------------------------------------------- the ratchet baseline


def load_baselines():
    if not os.path.isfile(BASELINE_FILE):
        return {}
    with open(BASELINE_FILE, encoding="utf-8") as handle:
        data = json.load(handle)
    return {entry["id"]: entry for entry in data.get("baselines", []) if isinstance(entry, dict) and "id" in entry}


def ratchet_verdict(signature_id, count, baselines, today):
    """(ok, words) for a ratchet count against the committed baseline."""
    entry = baselines.get(signature_id)
    baseline = entry.get("count", 0) if entry else 0
    deadline = entry.get("deadline") if entry else None
    if deadline:
        try:
            past = today > _dt.date.fromisoformat(deadline)
        except ValueError:
            return False, f"the baseline deadline '{deadline}' is not a date (YYYY-MM-DD)"
        if past and count > 0:
            return False, f"{count} in the tree and the baseline deadline {deadline} has passed — this check is now blocking"
    if count > baseline:
        return False, f"{count} in the tree, above the baseline of {baseline} — a change added one; the count may only fall"
    if count < baseline:
        return False, f"{count} in the tree, below the baseline of {baseline} — lower the baseline to {count} in the same commit ({BASELINE_FILE})"
    return True, f"{count} in the tree, equal to the baseline" + (f"; deadline {deadline}" if deadline else "")


# ---------------------------------------------------------------- matching


def files_match(signature, path, extensions):
    patterns = signature.get("files") or [f"**/*{ext}" for ext in extensions]
    return any(glob_matches(pattern, path) for pattern in patterns)


def class_applies(signature, path_class):
    applies = signature.get("applies_to", ["*"])
    if path_class in signature.get("excludes", []):
        return False
    return "*" in applies or path_class in applies


def pattern_hits(pattern, lines, joined):
    """The (line, text) pairs the regex matches, or — when only the whitespace-stripped
    join of the lines matches (a hatch split across chained modifiers) — the first line."""
    regex = re.compile(pattern)
    hits = [(number, text) for number, text in lines if regex.search(text)]
    if hits:
        return hits
    if lines and regex.search(joined):
        return [lines[0]]
    return []


def signature_hits(signature, lines):
    joined = "".join(text.strip() for _, text in lines)
    hits = pattern_hits(signature["pattern"], lines, joined)
    if not hits:
        return []
    paired = signature.get("paired")
    if paired and not pattern_hits(paired, lines, joined):
        return []
    return hits


# ---------------------------------------------------------------- the run


class Scan:
    def __init__(self, platform, signatures, paths, today=None):
        self.platform = platform
        self.signatures = signatures
        self.paths = paths
        self.today = today or _dt.date.today()
        self.failures = []
        self.advisories = []
        self.notes = []
        self.deviations = None

    def fail(self, check, path, line, signature_id, words, rule):
        self.failures.append({"check": check, "path": path, "line": line, "id": signature_id, "words": words, "rule": rule})

    @staticmethod
    def check_name(signature):
        return signature.get("group") or ("import-matrix" if signature.get("kind") == "builtin" else "rules")

    def excepted(self, signature, path, head, changed_paths):
        if self.deviations is None:
            self.deviations = approved_deviations(head, changed_paths)
        if any(target_covers(d["file"], path) and signature["id"] in d["signatures"] for d in self.deviations):
            return True
        return any(e["id"] == signature["id"] and target_covers(e["path"], path) for e in governed_exceptions())

    def scan_added(self, changed, head):
        changed_paths = [path for path, _ in changed]
        for signature in self.signatures:
            if signature.get("kind") == "builtin" or signature.get("scope", "added") != "added":
                continue
            severity = signature.get("severity", "block")
            for path, lines in changed:
                if not files_match(signature, path, self.paths.extensions):
                    continue
                if not class_applies(signature, self.paths.classify(path)):
                    continue
                hits = signature_hits(signature, lines)
                if not hits:
                    continue
                if severity == "advisory":
                    for number, _ in hits:
                        self.advisories.append((self.check_name(signature), path, number, signature["id"], signature["words"], signature["rule"]))
                    continue
                if severity == "ratchet":
                    continue  # ratchets are judged on the whole tree below
                if self.excepted(signature, path, head, changed_paths):
                    continue
                for number, _ in hits:
                    self.fail(self.check_name(signature), path, number, signature["id"], signature["words"], signature["rule"])

    def scan_tree(self, include_untracked, head):
        tree_signatures = [s for s in self.signatures if s.get("kind") != "builtin"
                           and (s.get("scope") == "tree" or s.get("severity") == "ratchet")]
        builtins = [s for s in self.signatures if s.get("kind") == "builtin"]
        if not tree_signatures and not builtins:
            return
        files = tree_files(include_untracked) if tree_signatures else []
        baselines = load_baselines() if any(s.get("severity") == "ratchet" for s in tree_signatures) else {}
        contents = {}
        for signature in tree_signatures:
            count = 0
            hits = []
            for path in files:
                if not files_match(signature, path, self.paths.extensions) or not class_applies(signature, self.paths.classify(path)):
                    continue
                if path not in contents:
                    contents[path] = list(enumerate(read_lines(path), 1))
                for number, _ in signature_hits(signature, contents[path]):
                    if self.excepted(signature, path, head, []):
                        continue
                    count += 1
                    hits.append((path, number))
            severity = signature.get("severity", "block")
            if severity == "ratchet":
                ok, words = ratchet_verdict(signature["id"], count, baselines, self.today)
                self.notes.append(f"{'OK' if ok else 'FAIL'} ratchet {signature['id']}: {words} [{signature['rule']}]")
                if not ok:
                    for path, number in hits:
                        self.fail("ratchet", path, number, signature["id"], signature["words"], signature["rule"])
                    if not hits:
                        self.fail("ratchet", BASELINE_FILE, 0, signature["id"], words, signature["rule"])
            elif severity == "advisory":
                for path, number in hits:
                    self.advisories.append((self.check_name(signature), path, number, signature["id"], signature["words"], signature["rule"]))
            else:
                for path, number in hits:
                    self.fail(self.check_name(signature), path, number, signature["id"], signature["words"], signature["rule"])
        for signature in builtins:
            if signature["id"] == "import-matrix":
                import import_matrix  # beside this file
                failures, layout, judged = import_matrix.failures_for(self.platform)
                for path, words in failures:
                    self.fail("import-matrix", path, 0, "import-matrix", words, signature["rule"])
                if not judged:
                    self.notes.append(f"PASS import-matrix — no modules found under the {layout} layout; nothing was judged")
            else:
                self.fail("rules", SIGNATURES_FILE, 0, signature["id"], f"unknown builtin check '{signature['id']}'", signature.get("rule", "-"))


def load_tables(platform):
    with open(SIGNATURES_FILE, encoding="utf-8") as handle:
        tables = json.load(handle)["platforms"]
    with open(PATHS_FILE, encoding="utf-8") as handle:
        paths = json.load(handle)["platforms"]
    if platform is None:
        raise SystemExit("check_rules.py: the project's platform is not known — set COAST_PLATFORM "
                         "(the shipped workflow does) or pass --platform <name>; expected one of " + ", ".join(sorted(tables)))
    if platform not in tables or platform not in paths:
        raise SystemExit(f"check_rules.py: unknown platform '{platform}' (expected one of {', '.join(sorted(tables))})")
    entry = tables[platform]
    signatures = entry["signatures"] if isinstance(entry, dict) else entry
    return signatures, PathClasses(paths[platform])


def main(argv=None):
    parser = argparse.ArgumentParser(description="The rules scanner.")
    parser.add_argument("base", nargs="?")
    parser.add_argument("head", nargs="?")
    parser.add_argument("--platform", default=os.environ.get("COAST_PLATFORM") or None)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--files", nargs="+")
    parser.add_argument("--tree", action="store_true")
    parser.add_argument("--today", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    modes = [bool(args.staged), bool(args.files), bool(args.tree), bool(args.base)]
    if sum(modes) != 1 or (args.base and not args.head):
        parser.print_usage()
        print("check_rules.py: give exactly one of <base> <head|WORKTREE>, --staged, --files …, --tree")
        return 2
    signatures, paths = load_tables(args.platform)
    today = _dt.date.fromisoformat(args.today) if args.today else None
    scan = Scan(args.platform, signatures, paths, today)

    head = None
    include_untracked = True
    if args.staged:
        changed = changed_files("staged", None, None)
    elif args.files:
        changed = changed_files("files", None, args.files)
    elif args.tree:
        changed = []
    else:
        head = args.head
        include_untracked = head == WORKTREE
        changed = changed_files("diff", args.base, head)

    governed = changed and all(paths.classify(path) in ("governing", "git") for path, _ in changed)
    if governed:
        print("PASS rules (governance-only diff)")
        print(json.dumps({"result": "pass", "governance_only": True}))
        return 0

    scan.scan_added(changed, head)
    scan.scan_tree(include_untracked, head)

    for check, path, line, signature_id, words, rule in scan.advisories:
        print(f"ADVISORY {check} {path}:{line}:{signature_id}: {words} [{rule}]")
    for note in scan.notes:
        print(note)
    for f in scan.failures:
        print(f"FAIL {f['check']} {f['path']}:{f['line']}:{f['id']}: {f['words']} [{f['rule']}]")
    if scan.failures:
        print(json.dumps({"result": "fail", "failures": scan.failures}, ensure_ascii=False))
        return 1
    print("PASS rules")
    print(json.dumps({"result": "pass", "advisories": len(scan.advisories)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
