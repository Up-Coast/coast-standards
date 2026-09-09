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

    check_rules.py <base> <head> --platform <p>      # lines added between two commits (a pre-push hook)
    check_rules.py <base> WORKTREE --platform <p>    # tracked changes since base + every untracked file
    check_rules.py --staged --platform <p>           # the index (a pre-commit hook)
    check_rules.py --files a b c --platform <p>      # whole files (an editor hook; every line is new)
    check_rules.py --tree --platform <p>             # no diff: only the tree-scope and ratchet signatures, over the whole tree

Every mode but ``--tree`` judges the change: the added-scope signatures on the added lines
and the tree-scope block signatures on the changed files, no ratchets. The whole-tree pass
with the ratchets is ``--tree`` alone, so a push runs it once.
    check_rules.py --ratchet <id> --count <n> --platform <p>   # a tool's count judged as a ratchet (build-warnings, format-findings)
    check_rules.py --ratchet <id> --log <log> [--measured <listing>] --platform <p>
                                                     # the tool's own output counted here (one reader for the
                                                     # file:line:col: warning|error: lines); with --measured, the
                                                     # count over those files against the baseline's per-file map (E8)
    check_rules.py --measure <id> --log <log>        # MEASURE <id> <total> and MEASURE-FILE <id> <count> <path> lines for adopt.py
    check_rules.py --has-baseline <id> [--per-file]  # exit 0 when the state dir's ratchet-baseline.json carries an entry for <id>
                                                     # (with --per-file: one that carries the per-file map)
    … --only <id>[,<id>]                             # run only the named signatures (adopt.py's first-push secret scan)

The platform also comes from ``<prefix>PLATFORM`` (``COAST_PLATFORM`` by
default; every path and name here comes from the layout table, ``layout.json``
beside this file). The project's config (``config.json`` in the state dir, read
through ``config.py``) can switch a signature off, lower its severity or add
retired words; a signature switched off is simply not in the list this runs.
Run from the repository root. Exit 0 = pass; any failure prints
``FAIL <check> <path>:<line>:<id>: <words> [<rule>]`` and exits 1 — the
line format the battery, the hooks, CI and Coast parse. The last line is a
JSON summary (``{"result": "pass"|"fail", ...}``).

Severities:

* ``block`` — any hit on an added line (scope ``added``) or anywhere in the
  tree (scope ``tree``) fails, unless an exception covers it.
* ``ratchet`` — counted over the whole tree and compared with
  the state dir's ``ratchet-baseline.json`` (``{"baselines": [{id, count, deadline,
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
* the state dir's ``rules-exceptions.json`` — ``{"exceptions": [{id, path, reason,
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
import layout as _layout  # noqa: E402 — the one table of the paths the layer names (E5.1), beside this file
import config as _config  # noqa: E402 — the one loader of the project's config (E5.3), beside this file
LAYOUT = _layout.load()   # the project's layout, read from the working directory (the repository root)
BASELINE_FILE = LAYOUT.state_file("ratchet-baseline.json")
EXCEPTIONS_FILE = LAYOUT.state_file("rules-exceptions.json")
PATHS_OVERRIDE_FILE = LAYOUT.state_file("paths.json")  # a project's own class bindings, merged over the platform's (GOVERNING)
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
        # a {key} in a glob is a layout key (paths.json's governing classes name the layer's own folders that way)
        self.classes = {name: [LAYOUT.expand(pattern) for pattern in patterns] for name, patterns in table.get("classes", {}).items()}

    def classify(self, path):
        for name in self.order:
            if any(glob_matches(pattern, path) for pattern in self.classes.get(name, [])):
                return name
        return "source"


# ---------------------------------------------------------------- git


def git(*args, check=True):
    # core.quotePath would print a non-ASCII path as "Caf\303\251View.swift", which no later
    # git command finds; every mode silently skipped such files before this.
    result = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True, text=True)
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
    in_hunk = False
    for raw in diff_text.splitlines():
        hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
        if hunk:
            new_line = int(hunk.group(1))
            in_hunk = True
            continue
        if not in_hunk and (raw.startswith("+++") or raw.startswith("---")):
            continue   # the file headers; inside a hunk a line starting "++" is an added line like any other
        if raw.startswith("+"):
            lines.append((new_line, raw[1:]))
            new_line += 1
    return lines


class Change:
    """One changed file: its path, the lines the change adds, git's status letter for it
    (A added, M modified, R renamed, C copied, T type-changed; a named or untracked file is A —
    every line is new) and, when the content the diff describes is not the worktree file, the
    ``git show`` spec that reads it (``:path`` for the index, ``<head>:path`` for a commit)."""

    __slots__ = ("path", "lines", "status", "blob")

    def __init__(self, path, lines, status="A", blob=None):
        self.path, self.lines, self.status, self.blob = path, lines, status, blob

    def text(self):
        """The whole file as the diff saw it, or None when it cannot be read (a deleted worktree file)."""
        if self.blob is None:
            if not os.path.isfile(self.path):
                return None
            with open(self.path, encoding="utf-8", errors="replace") as handle:
                return handle.read()
        shown = subprocess.run(["git", "-c", "core.quotePath=false", "show", self.blob], capture_output=True)
        if shown.returncode != 0:
            return None
        return shown.stdout.decode("utf-8", errors="replace")


NEW_FILE_STATUSES = ("A", "R", "C")   # the statuses under which a file itself is new to the tree (secret-file)


def name_status(*diff_args):
    """[(status letter, old path or None, path)] from ``git diff --name-status -M``, deletions dropped.
    Renames are asked for explicitly (``-M``) so the answer never depends on the user's diff.renames."""
    out = []
    for line in git("diff", "--name-status", "-M", *diff_args).splitlines():
        if not line or line.startswith("D"):
            continue
        parts = line.split("\t")
        status = parts[0][0]
        old = parts[1] if len(parts) == 3 else None
        out.append((status, old, parts[-1]))
    return out


def file_diff(status, old, path, *diff_args):
    """The --unified=0 diff of one changed file. A renamed or copied file is asked for under BOTH
    its paths, so git pairs them and only the lines the move changed count as added; asking for the
    new path alone defeats rename detection and re-judges every legacy line as new."""
    pathspec = [old, path] if old and status in ("R", "C") else [path]
    return git("diff", "--unified=0", "-M", "-C", *diff_args, "--", *pathspec)


def changed_files(mode, base, head):
    """[Change] for the mode — what the change adds."""
    if mode == "files":
        return [Change(path, list(enumerate(read_lines(path), 1))) for path in head if os.path.isfile(path)]
    if mode == "staged":
        return [Change(path, added_lines_from_diff(file_diff(status, old, path, "--cached")), status, f":{path}")
                for status, old, path in name_status("--cached")]
    if head == WORKTREE:
        names = name_status(base)
        untracked = [p for p in git("ls-files", "--others", "--exclude-standard").splitlines() if p]
    else:
        names = name_status(f"{base}..{head}")
        untracked = []
    out = []
    for status, old, path in names:
        if head == WORKTREE:
            if not tracked(path):
                continue
            out.append(Change(path, added_lines_from_diff(file_diff(status, old, path, base)), status))
        else:
            out.append(Change(path, added_lines_from_diff(file_diff(status, old, path, f"{base}..{head}")), status, f"{head}:{path}"))
    for path in untracked:
        if os.path.isfile(path):
            out.append(Change(path, list(enumerate(read_lines(path), 1))))
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
    try:
        with open(BASELINE_FILE, encoding="utf-8") as handle:
            data = json.load(handle)
        entries = data.get("baselines", [])
    except (ValueError, AttributeError) as error:
        print(f"FAIL ratchet {BASELINE_FILE}:0:baseline: the ratchet baseline is not the JSON adopt.py writes ({error}) — re-run adopt.py")
        sys.exit(1)
    baselines = {entry["id"]: entry for entry in entries if isinstance(entry, dict) and "id" in entry}
    # Decision 2: every baseline carries a deadline. An entry without one would be a permanent
    # allowance nobody agreed to, so it is refused here, before any count is judged.
    undated = [signature_id for signature_id, entry in baselines.items() if not entry.get("deadline")]
    for signature_id in undated:
        print(f"FAIL ratchet {BASELINE_FILE}:0:{signature_id}: the baseline entry for {signature_id} has no deadline "
              f"— every baseline carries one (YYYY-MM-DD; adopt.py writes 90 days out); add it or re-run adopt.py")
    if undated:
        sys.exit(1)
    return baselines


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


# Tool ratchets — decision 2 applied to the tools the pre-push battery runs.
# The rule is "zero NEW compiler warnings" (C-4 on every app platform, the
# numbered file 02 for Python): on a repository that already carries
# warnings, the build seat counts them and this verdict holds the count
# against the same baseline file, with the same deadline, as any scanner
# ratchet; with no entry the tool runs strict (warnings as errors). One
# baseline file, one verdict, one reader.
TOOL_RATCHETS = {
    "build-warnings": {
        "words": "compiler warnings in the build — a change added one; the count may only fall, and past the deadline the build runs with warnings as errors",
        "rules": {"python": "02 zero-new-warnings"}, "rule": "C-4", "log": "warnings"},
    "format-findings": {
        "words": "formatter findings in the tree — a change added one; the count may only fall, and past the deadline the format check refuses any finding",
        "rules": {"python": "02 zero-new-warnings"}, "rule": "C-4", "log": "findings"},
    "lint-findings": {
        "words": "linter findings in the tree — a change added one; the count may only fall, and past the deadline the linter runs strict",
        "rules": {"python": "02 zero-new-warnings"}, "rule": "C-4", "log": "findings"},
    "tests-missing": {
        "words": "the project has no test target — tests come first (rules/06); add one and re-run adopt.py to lower this to zero; past the deadline the push refuses until a test target exists",
        "rules": {"python": "06 tests-first"}, "rule": "06 tests-first"},
}


def tool_ratchet_rule(signature_id, platform):
    entry = TOOL_RATCHETS[signature_id]
    return entry["rules"].get(platform or "", entry["rule"])


TOOL_LINE = re.compile(r"^([^ :][^:]*):(\d+):(\d+): (warning|error): ")


def tool_log_counts(log_path, kind):
    """{path: count} from a tool's output — the one reader of the ``file:line:col: warning|error:``
    lines the compiler, the linter and the formatter print. ``warnings`` counts distinct warning
    lines (a build prints the same warning once per target that includes the file); ``findings``
    counts every warning and error line, which is what the linter and formatter report. Paths
    are made relative to the working directory (the repository root the hook runs from), so a
    count can be matched to the baseline's per-file map and to the files a push measured."""
    root = os.path.realpath(os.getcwd()).rstrip("/") + "/"
    counts = {}
    seen = set()
    with open(log_path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = TOOL_LINE.match(line)
            if not match:
                continue
            if kind == "warnings":
                if match.group(4) != "warning":
                    continue
                stripped = line.rstrip("\n")
                if stripped in seen:
                    continue
                seen.add(stripped)
            path = match.group(1)
            if os.path.isabs(path):
                real = os.path.realpath(path)   # a Mac's /var is /private/var; the tools print either
                if real.startswith(root):
                    path = real[len(root):]
            counts[path] = counts.get(path, 0) + 1
    return counts


def read_listing(path):
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle if line.strip()]


def print_measure(signature_id, counts):
    """The lines adopt.py --measure-tools reads: the total, then one per file with a count."""
    print(f"MEASURE {signature_id} {sum(counts.values())}")
    for path in sorted(counts):
        print(f"MEASURE-FILE {signature_id} {counts[path]} {path}")


def judge_tool_ratchet(signature_id, count, platform, today, measured=None, counts=None):
    """Print the ratchet line (and the FAIL line on a refusal) for a tool's count; the exit code.

    A tool's count is NOT the deterministic tree count a scanner ratchet judges: a build
    prints warnings only for what it recompiles, so the number depends on the build's state
    as much as on the code. The rule is "zero NEW warnings" (C-4), so only a RISE refuses.
    A count below the baseline passes with a note offering to lower it — it is an
    improvement or a warm build, and neither is a reason to refuse a push. (Two real
    refusals produced this: one adopting app measured 22 and rebuilt to 0, the reference implementation measured 270
    and rebuilt to 0 while another session held the build directory warm.)

    With ``measured`` (the files a scoped run rebuilt or linted, E8) the count is judged
    against the baseline's per-file map summed over those same files — plus any file the
    tool reported on, so a warning cannot hide in a file the listing forgot. Files the run
    did not touch keep their numbers: nothing in them could have changed.
    """
    if signature_id not in TOOL_RATCHETS:
        print(f"check_rules.py: unknown tool ratchet '{signature_id}' (one of {', '.join(sorted(TOOL_RATCHETS))})")
        return 2
    if count < 0:
        print(f"check_rules.py: a count of {count} for '{signature_id}' is not a count — the seat's counter is broken")
        return 2
    rule = tool_ratchet_rule(signature_id, platform)
    entry = load_baselines().get(signature_id)
    baseline = entry.get("count", 0) if entry else 0
    deadline = entry.get("deadline") if entry else None
    today = today or _dt.date.today()
    scope_words = ""
    if measured is not None:
        files = entry.get("files") if entry else None
        if not isinstance(files, dict):
            print(f"check_rules.py: the baseline entry for '{signature_id}' has no per-file map — a scoped run cannot be judged; "
                  f"run adopt.py --measure-tools, or run the tool whole")
            return 2
        judged = sorted(set(measured) | set(counts or {}))
        baseline = sum(int(files.get(path, 0) or 0) for path in judged)
        scope_words = f" over the {len(judged)} file(s) this push measured"
    if deadline:
        try:
            past = today > _dt.date.fromisoformat(deadline)
        except ValueError:
            print(f"FAIL ratchet {signature_id}: the baseline deadline '{deadline}' is not a date (YYYY-MM-DD) [{rule}]")
            return 1
        if past and count > 0:
            print(f"FAIL ratchet {signature_id}: {count} reported and the baseline deadline {deadline} has passed "
                  f"— this check is now blocking [{rule}]")
            print(f"FAIL ratchet {BASELINE_FILE}:0:{signature_id}: {TOOL_RATCHETS[signature_id]['words']} [{rule}]")
            return 1
    if count > baseline:
        print(f"FAIL ratchet {signature_id}: {count} reported{scope_words}, above the baseline of {baseline} "
              f"— a change added one; the count may only fall [{rule}]")
        if counts and measured is not None:
            for path in sorted(counts):
                if counts[path] > int((entry or {}).get("files", {}).get(path, 0) or 0):
                    print(f"FAIL ratchet {path}:0:{signature_id}: {counts[path]} reported, {int((entry or {}).get('files', {}).get(path, 0) or 0)} in the baseline [{rule}]")
        print(f"FAIL ratchet {BASELINE_FILE}:0:{signature_id}: {TOOL_RATCHETS[signature_id]['words']} [{rule}]")
        return 1
    if count < baseline:
        print(f"OK ratchet {signature_id}: {count} reported{scope_words}, below the baseline of {baseline} "
              f"— nothing new; lower the baseline with adopt.py --measure-tools when the tree is quiet"
              + (f"; deadline {deadline}" if deadline else "") + f" [{rule}]")
        return 0
    print(f"OK ratchet {signature_id}: {count} reported{scope_words}, equal to the baseline"
          + (f"; deadline {deadline}" if deadline else "") + f" [{rule}]")
    return 0


# ---------------------------------------------------------------- matching


def files_match(signature, path, extensions):
    patterns = signature.get("files") or [f"**/*{ext}" for ext in extensions]
    if any(glob_matches(pattern, path) for pattern in signature.get("files_excluded", [])):
        return False
    return any(glob_matches(pattern, path) for pattern in patterns)


def builtin_hits(signature, path, text):
    """[(line, text)] of a built-in added-scope check over one file's whole text — the one dispatch
    the scanner and the plant test both use (``ui-string-literal``: literals.py; the Python
    ``blocking-call``: async_blocking.py)."""
    if signature["id"] == "ui-string-literal":
        import literals  # beside this file
        return literals.hits(path, text)
    if signature["id"] == "blocking-call":
        import async_blocking  # beside this file
        return async_blocking.hits(path, text)
    if signature["id"] == "test-criterion-tag":
        import test_criteria  # beside this file
        return test_criteria.hits(path, text)
    if signature["id"] == "type-size":
        import type_size  # beside this file
        return type_size.hits(path, text)
    if signature["id"] == "doc-comments":
        import check_doc_comments  # beside this file — reads the file (and, for Swift, its module) from disk
        platform = os.environ.get("COAST_PLATFORM") or check_doc_comments.platform_for(path)
        return [(line, entry) for _, line, entry in check_doc_comments.undocumented([path], platform, texts={os.path.normpath(path): text})]
    if signature["id"] == "secret-file":
        return secret_file_hits(signature, path)
    if signature["id"] == "plaintext-http":
        return plaintext_http_hits(path, text)
    if signature["id"] == "exported-component":
        return exported_component_hits(text)
    return []


# The three built-ins below live here because each is a few lines that need the whole file, not
# a lexer of its own. Each returns [(line, text)] like every other built-in.


def secret_file_hits(signature, path):
    """A file whose NAME is a secret or data shape (the signature's own file globs): the hit is
    the file, at line 1. Its content is never read — a .p12, .sqlite or .jks is binary, adds no
    ``+`` line to any diff, and a content regex never saw it."""
    return [(1, path)] if files_match(signature, path, ()) else []


_PLAINTEXT_LINE = re.compile(
    r"^(?!.*(?:xmlns|DOCTYPE|w3\.org|schemas\.|purl\.org|json-schema\.org|apple\.com/DTDs|ns\.adobe\.com"
    r"|localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|10\.0\.2\.2|example\.(?:com|org|net))).*\bhttp://"
    r'|usesCleartextTraffic="true"')
_PLIST_ARBITRARY_LOADS = re.compile(r"<key>\s*NSAllowsArbitraryLoads\s*</key>")
_PLIST_TRUE = re.compile(r"<true\s*/?>")


def plaintext_http_hits(path, text):
    """A plain http:// URL or the Android cleartext attribute on a line, and the plist toggle
    ``<key>NSAllowsArbitraryLoads</key>`` followed by ``<true/>`` — on the same line or the next
    line that is not blank or a comment. The toggle is reported at the ``<true/>`` line: flipping
    ``<false/>`` to ``<true/>`` under an existing key adds only that line, and that is the line
    the added-scope filter keeps."""
    hits = []
    key_line = None
    for number, line in enumerate(text.splitlines(), 1):
        if _PLAINTEXT_LINE.search(line):
            hits.append((number, line))
        key = _PLIST_ARBITRARY_LOADS.search(line)
        if key:
            if _PLIST_TRUE.search(line, key.end()):
                hits.append((number, line))
                key_line = None
            else:
                key_line = number
            continue
        if key_line is not None:
            stripped = line.strip()
            if not stripped or stripped.startswith("<!--"):
                continue
            if _PLIST_TRUE.search(line):
                hits.append((number, line))
            key_line = None
    return sorted(set(hits))


_COMPONENT_OPEN = re.compile(r"<(activity|service|receiver|provider)(?=[\s/>])")
_EXPORTED_TRUE = re.compile(r'android:exported\s*=\s*"true"')
_LAUNCHER = "android.intent.category.LAUNCHER"


def exported_component_hits(text):
    """A manifest component exported with no ``android:permission`` on it, unless its body carries
    the LAUNCHER category (the one component that must be reachable). Read over the whole file, so
    the tag may span any number of lines; the hit is the line holding ``android:exported="true"``,
    the line a toggle adds."""
    hits = []
    for opened in _COMPONENT_OPEN.finditer(text):
        close = text.find(">", opened.end())
        if close < 0:
            break
        head = text[opened.start():close + 1]
        exported = _EXPORTED_TRUE.search(head)
        if not exported or "android:permission" in head:
            continue
        if not head.endswith("/>"):
            end = text.find(f"</{opened.group(1)}>", close)
            if _LAUNCHER in text[close:end if end >= 0 else len(text)]:
                continue
        at = opened.start() + exported.start()
        hits.append((text.count("\n", 0, at) + 1, head.strip()))
    return hits


def builtin_added_hits(signature, change):
    """Hits of a built-in added-scope check: the whole file — as the diff saw it, the index or
    the commit, never a worktree file the diff did not describe — is lexed, and only the added
    lines count. Two exceptions: ``secret-file`` is the file itself, judged by git's status
    (a new, renamed or copied path) because a binary adds no line; ``type-size`` reports an
    oversized type once, at the first added line inside it, so that growing a type that is
    already too big is what surfaces."""
    if signature["id"] == "secret-file":
        return secret_file_hits(signature, change.path) if change.status in NEW_FILE_STATUSES else []
    text = change.text()
    if text is None:
        return []
    added = {number for number, _ in change.lines}
    if signature["id"] == "type-size":
        import type_size  # beside this file
        hits = []
        for start, end, words in type_size.spans(change.path, text):
            inside = sorted(number for number in added if start <= number <= end)
            if inside:
                hits.append((inside[0], words))
        return hits
    return [(number, text) for number, text in builtin_hits(signature, change.path, text) if number in added]


def class_applies(signature, path_class):
    applies = signature.get("applies_to", ["*"])
    if path_class in signature.get("excludes", []):
        return False
    return "*" in applies or path_class in applies


JOIN_WINDOW = 8   # a hatch split across chained modifiers spans a few lines, never a file


def pattern_hits(pattern, lines):
    """The (line, text) pairs the regex matches, or — when only the whitespace-stripped
    join of a few consecutive lines matches (a hatch split across chained modifiers) — the
    first line of that window. The window is bounded: joining a whole file made a `print(`
    on one line and the word `address` hundreds of lines later one pii-in-log hit."""
    regex = re.compile(pattern)
    hits = [(number, text) for number, text in lines if regex.search(text)]
    if hits:
        return hits
    stripped = [text.strip() for _, text in lines]
    for start in range(len(lines)):
        if regex.search("".join(stripped[start:start + JOIN_WINDOW])):
            return [lines[start]]
    return []


def signature_hits(signature, lines):
    hits = pattern_hits(signature["pattern"], lines)
    if not hits:
        return []
    paired = signature.get("paired")
    if paired and not pattern_hits(paired, lines):
        return []
    return hits[:1] if signature.get("once") else hits


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
        return signature.get("group") or ("import-matrix" if signature["id"] == "import-matrix" else "rules")

    def excepted(self, signature, path, head, changed_paths):
        if self.deviations is None:
            self.deviations = approved_deviations(head, changed_paths)
        if any(target_covers(d["file"], path) and signature["id"] in d["signatures"] for d in self.deviations):
            return True
        return any(e["id"] == signature["id"] and target_covers(e["path"], path) for e in governed_exceptions())

    def scan_added(self, changed, head):
        changed_paths = [change.path for change in changed]
        for signature in self.signatures:
            if signature.get("scope", "added") != "added":
                continue
            builtin = signature.get("kind") == "builtin"
            severity = signature.get("severity", "block")
            for change in changed:
                path = change.path
                if not files_match(signature, path, self.paths.extensions):
                    continue
                if not class_applies(signature, self.paths.classify(path)):
                    continue
                hits = builtin_added_hits(signature, change) if builtin else signature_hits(signature, change.lines)
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

    def scan_tree(self, include_untracked, head, only=None):
        """The tree-scope signatures and the ratchets. With ``only`` (the changed files of every mode
        but ``--tree``) the tree-scope block signatures run over those files alone and the ratchets
        are not judged at all — a count over the whole tree is ``--tree``'s business, run once per
        push; judging it at every commit, every edit and again beside the push's own diff scan made
        a large repository wait half a minute each time."""
        tree_signatures = [s for s in self.signatures if s.get("kind") != "builtin"
                           and (s.get("scope") == "tree" or s.get("severity") == "ratchet")]
        builtins = [s for s in self.signatures if s.get("kind") == "builtin" and s.get("scope") == "tree"]
        if only is not None:
            tree_signatures = [s for s in tree_signatures if s.get("severity") != "ratchet"]
            builtins = []
        if not tree_signatures and not builtins:
            return
        files = (list(only) if only is not None else tree_files(include_untracked)) if tree_signatures else []
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


def flatten_signatures(document):
    """{platform: [signature]} from the one-row-per-signature file (E5.2).

    A row carries the shared fields once and, under ``platforms``, one entry per platform
    the signature runs on: the platform's own ``files``/``pattern``/``paired`` and any
    shared field whose value differs there. Each platform's list keeps the row order, and
    each entry is the row's shared fields with the platform's own laid over them — the
    per-platform shape the scanner, the plants and the verifier read.
    """
    tables = {}
    for row in document.get("signatures", []):
        shared = {key: value for key, value in row.items() if key != "platforms"}
        for platform, own in row.get("platforms", {}).items():
            tables.setdefault(platform, []).append({**shared, **own})
    return tables


def load_signature_tables(path=None):
    with open(path or SIGNATURES_FILE, encoding="utf-8") as handle:
        return flatten_signatures(json.load(handle))


def load_config():
    """The project's config (config.py), or a FAIL line and exit 1 when the file refuses to load."""
    try:
        return _config.load()
    except _config.ConfigError as error:
        print(f"FAIL config {LAYOUT.state_file(_config.FILE_NAME)}:0:config: {error}")
        sys.exit(1)


def load_tables(platform, paths_override=None, config=None):
    """(signatures, PathClasses) for the platform, under the project's config (E5.3): the
    signatures the config switches off are gone from the list, the severities it lowers are
    lowered, and its retired words join the retired-wording pattern."""
    tables = load_signature_tables()
    config = config or load_config()
    try:
        tables = {name: _config.apply_to_signatures(config, entries) for name, entries in tables.items()}
    except _config.ConfigError as error:
        print(f"FAIL config {LAYOUT.state_file(_config.FILE_NAME)}:0:severity: {error}")
        sys.exit(1)
    with open(PATHS_FILE, encoding="utf-8") as handle:
        paths = json.load(handle)["platforms"]
    override = paths_override or (PATHS_OVERRIDE_FILE if os.path.isfile(PATHS_OVERRIDE_FILE) else None)
    if override and platform in paths:
        with open(override, encoding="utf-8") as handle:
            own = json.load(handle)
        own = own.get("platforms", {}).get(platform, own)  # either the platform table or the bare {"classes": …}
        merged = dict(paths[platform])
        merged["classes"] = dict(merged.get("classes", {}), **own.get("classes", {}))
        if own.get("extensions"):
            merged["extensions"] = own["extensions"]
        paths[platform] = merged
    if platform is None:
        raise SystemExit(f"check_rules.py: the project's platform is not known — set {LAYOUT.env('PLATFORM')} "
                         "(the shipped workflow does) or pass --platform <name>; expected one of " + ", ".join(sorted(tables)))
    if platform not in tables or platform not in paths:
        raise SystemExit(f"check_rules.py: unknown platform '{platform}' (expected one of {', '.join(sorted(tables))})")
    return tables[platform], PathClasses(paths[platform])


def main(argv=None):
    parser = argparse.ArgumentParser(description="The rules scanner.")
    parser.add_argument("base", nargs="?")
    parser.add_argument("head", nargs="?")
    parser.add_argument("--platform", default=LAYOUT.env_value("PLATFORM"))
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--files", nargs="+")
    parser.add_argument("--tree", action="store_true")
    parser.add_argument("--paths-override", help=f"a project's own path-class bindings (default: {PATHS_OVERRIDE_FILE} when present)")
    parser.add_argument("--only", metavar="ID[,ID]", help="run only these signature ids (adopt.py's first-push secret scan uses it; not a bypass — git never passes it)")
    parser.add_argument("--ratchet", metavar="ID", help="judge a tool's count as a ratchet: build-warnings, format-findings, lint-findings or tests-missing (with --count or --log)")
    parser.add_argument("--count", type=int, help="the count the tool produced (with --ratchet)")
    parser.add_argument("--log", metavar="FILE", help="the tool's own output, counted here (with --ratchet or --measure)")
    parser.add_argument("--measured", metavar="LISTING", help="the files a scoped run measured, one per line: judge their count against the baseline's per-file map (with --ratchet --log)")
    parser.add_argument("--measure", metavar="ID", help="print MEASURE and MEASURE-FILE lines for adopt.py from --log")
    parser.add_argument("--has-baseline", metavar="ID", help="exit 0 when the ratchet baseline carries an entry for ID, else 1")
    parser.add_argument("--per-file", action="store_true", help="with --has-baseline: the entry must carry the per-file map")
    parser.add_argument("--today", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    modes = [bool(args.staged), bool(args.files), bool(args.tree), bool(args.base), bool(args.ratchet), bool(args.has_baseline), bool(args.measure)]
    counted = args.count is not None or args.log is not None
    if sum(modes) != 1 or (args.base and not args.head) or (args.ratchet and not counted) or (args.measure and not args.log):
        parser.print_usage()
        print("check_rules.py: give exactly one of <base> <head|WORKTREE>, --staged, --files …, --tree, --ratchet ID --count N|--log FILE, "
              "--measure ID --log FILE, --has-baseline ID")
        return 2
    if args.has_baseline:
        entry = load_baselines().get(args.has_baseline)
        if entry is None:
            return 1
        return 0 if not args.per_file or isinstance(entry.get("files"), dict) else 1
    if args.measure:
        if args.measure not in TOOL_RATCHETS or "log" not in TOOL_RATCHETS[args.measure]:
            print(f"check_rules.py: --measure counts a tool's log: one of {', '.join(k for k, v in sorted(TOOL_RATCHETS.items()) if 'log' in v)}")
            return 2
        print_measure(args.measure, tool_log_counts(args.log, TOOL_RATCHETS[args.measure]["log"]))
        return 0
    if args.ratchet:
        today = _dt.date.fromisoformat(args.today) if args.today else None
        counts = None
        count = args.count
        if args.log is not None:
            if args.ratchet not in TOOL_RATCHETS or "log" not in TOOL_RATCHETS[args.ratchet]:
                print(f"check_rules.py: --log counts a tool's output: one of {', '.join(k for k, v in sorted(TOOL_RATCHETS.items()) if 'log' in v)}")
                return 2
            counts = tool_log_counts(args.log, TOOL_RATCHETS[args.ratchet]["log"])
            count = sum(counts.values())
        measured = read_listing(args.measured) if args.measured is not None else None
        return judge_tool_ratchet(args.ratchet, count, args.platform, today, measured, counts)
    signatures, paths = load_tables(args.platform, args.paths_override)
    if args.only:
        wanted = set(args.only.split(","))
        signatures = [sig for sig in signatures if sig.get("id") in wanted]
        missing = wanted - {sig.get("id") for sig in signatures}
        if missing:
            print(f"check_rules.py: --only names signatures the {args.platform} table does not have: {', '.join(sorted(missing))}")
            return 2
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

    governed = changed and all(paths.classify(change.path) in ("governing", "git") for change in changed)
    if governed:
        print("PASS rules (governance-only diff)")
        print(json.dumps({"result": "pass", "governance_only": True}))
        return 0

    scan.scan_added(changed, head)
    # The whole tree and the ratchets are --tree's alone: the pre-push hook runs the diff scan
    # once per pushed base and --tree once, and a diff mode that judged the tree too ran the
    # half-minute pass twice on a large repository.
    scan.scan_tree(include_untracked, head, only=None if args.tree else [change.path for change in changed])

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
