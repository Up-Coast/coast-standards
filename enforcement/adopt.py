#!/usr/bin/env python3
"""adopt.py — install the enforcement layer into a project, idempotently
(enforcement task E2.2; design enforcement/README.md §4.6).

Run from anywhere::

    python3 enforcement/adopt.py <project-dir> [--platform <p>] [--dry-run]
                                 [--by <name>] [--today YYYY-MM-DD]
                                 [--secret-scan] [--jscpd-bin <path>]

What it installs, and who owns each file afterwards:

* GOVERNED (replaced on every run, never the founder's to edit):
  ``Scripts/checks/`` — the scanner and its modules and tables
  (``check_rules.py``, ``literals.py``, ``import_matrix.py``, …,
  ``rules_signatures.json``, ``paths.json``, and ``check_doc_comments.py``
  once E1.5 ships it); ``.githooks/pre-commit``, ``pre-push``,
  ``commit-msg``; ``.coast/platform`` (one word); ``.coast/standards-version``
  (the standards commit adopted); ``.coast/seeds.json`` (the checksums below).
* SEEDS (founder-owned): the platform's linter configs from
  ``enforcement/lint/`` and ``docs/domain-rules.md`` from the platform's
  rules document. A seed is written when absent. A linter seed that still
  equals a shipped seed (this version's or the one recorded at install) is
  replaced by the current shipped one; a seed the founder edited is left
  alone with a printed note. ``docs/domain-rules.md`` is never replaced
  (decision D157: versioned, never auto-updated).
* ``CLAUDE.md``: the block between the ``up-coast-standards: begin/end``
  markers is rewritten from ``enforcement/TEMPLATE-PROJECT-CLAUDE.md`` with
  the platform, the standards commit and the enforced/total number
  (``verify_rules.py`` on the project's rules document); text outside the
  markers is the founder's and untouched. A CLAUDE.md with no markers gets
  the block appended once.
* Baselines (decision 2: written once, the count may only fall, the
  deadline 90 days from the day it was written and never moved here):
  ``.coast/ratchet-baseline.json`` from the scanner's current tree counts
  (``check_rules.py --tree``); ``.coast/jscpd-baseline.json`` from jscpd's
  own ``--update-baseline`` fingerprints plus the clone count — or
  ``"clones": null`` with a note when jscpd is not installed. On a re-run a
  count that fell is lowered (dates kept); a count that rose is left as it
  is and reported — nothing here raises a baseline.
* ``git config core.hooksPath .githooks``.
* A first-push secret scan (the first adoption, or ``--secret-scan``): the
  scanner's ``secret-literal`` group over every tracked file; findings are
  printed as FAIL lines and the exit code is 1.

Running it twice on the same tree produces no change the second time; the
report says ``wrote``, ``replaced``, ``unchanged`` or ``kept (founder-edited)``
per file. ``--dry-run`` prints the same report and writes nothing. Stdlib
only. No network.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STANDARDS_ROOT = os.path.dirname(HERE)
CHECKS_DIR = os.path.join(HERE, "checks")
HOOKS_DIR = os.path.join(HERE, "hooks")
LINT_DIR = os.path.join(HERE, "lint")
TEMPLATE = os.path.join(HERE, "TEMPLATE-PROJECT-CLAUDE.md")
BATTERY = os.path.join(CHECKS_DIR, "battery.json")

PROJECT_CHECKS_DIR = "Scripts/checks"
PROJECT_HOOKS_DIR = ".githooks"
HOOK_NAMES = ("pre-commit", "pre-push", "commit-msg")
CHECKS_NOT_SHIPPED = {"verify_rules.py", "battery.json", "verify-baseline.json"}  # they read this repo, not a project
PLATFORMS = ("ios", "macos", "android", "react-native", "web", "python")
RATCHET_DAYS = 90
JSCPD_PIN = "5.1.2"
JSCPD_MIN_TOKENS = "50"
JSCPD_IGNORE = ("**/node_modules/**,**/.build/**,**/build/**,**/Pods/**,**/DerivedData/**,**/dist/**,"
                "**/.venv/**,**/__pycache__/**,**/.coast/**,**/Scripts/checks/**,**/.githooks/**,"
                "**/*.min.js,**/*.lock,**/Package.resolved")
BLOCK_BEGIN = "<!-- up-coast-standards: begin"
BLOCK_END = "<!-- up-coast-standards: end -->"
SECRET_IDS = {"secret-literal", "secret-file"}

# Where each shipped lint seed lands in a project (the file names the linters read).
LINT_DESTINATIONS = {
    "swiftlint.yml": ".swiftlint.yml",
    "swift-format.json": ".swift-format",
    "detekt.yml": "detekt.yml",
    "lint.xml": "lint.xml",
    ".editorconfig": ".editorconfig",
    "eslint.config.mjs": "eslint.config.mjs",
    "tsconfig.seed.json": "tsconfig.json",
    ".prettierrc.json": ".prettierrc.json",
    "ruff.toml": "ruff.toml",
    "mypy.ini": "mypy.ini",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def git(cwd, *args, check=True):
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and done.returncode != 0:
        raise SystemExit(f"adopt.py: git {' '.join(args)} failed in {cwd}: {done.stderr.strip()}")
    return done.stdout.strip()


def clean_git_env():
    """A hook or a worktree exports GIT_DIR and friends; every git call here must see the project only."""
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY", "GIT_PREFIX"):
        os.environ.pop(name, None)


def detect_platform(project):
    """One word from the project's own manifest files, or None when it is not obvious."""
    def has(*names):
        return any(os.path.exists(os.path.join(project, n)) for n in names)
    if has("Package.swift") or any(n.endswith((".xcodeproj", ".xcworkspace")) for n in os.listdir(project)):
        text = ""
        if has("Package.swift"):
            text = read_bytes(os.path.join(project, "Package.swift")).decode("utf-8", "replace")
        ios = ".iOS(" in text
        mac = ".macOS(" in text
        if ios and not mac:
            return "ios"
        if mac and not ios:
            return "macos"
        return None
    if has("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"):
        return "android"
    if has("package.json"):
        try:
            data = json.loads(read_bytes(os.path.join(project, "package.json")))
        except ValueError:
            data = {}
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        return "react-native" if "react-native" in deps else "web"
    if has("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
        return "python"
    return None


class Adoption:
    def __init__(self, project, platform, dry_run, by, today, jscpd_bin, secret_scan):
        self.project = project
        self.platform = platform
        self.dry_run = dry_run
        self.by = by
        self.today = today
        self.jscpd_bin = jscpd_bin
        self.secret_scan = secret_scan
        self.lines = []
        self.changed = 0
        self.first_adoption = not os.path.isfile(self.path(".coast/platform"))
        self.seeds = self.load_json(".coast/seeds.json") or {}
        self.standards_commit = self.standards_version()

    # -- small helpers

    def path(self, relative):
        return os.path.join(self.project, relative)

    def load_json(self, relative):
        full = self.path(relative)
        if not os.path.isfile(full):
            return None
        try:
            return json.loads(read_bytes(full))
        except ValueError:
            return None

    def say(self, verb, relative, note=""):
        self.lines.append(f"{verb:<22} {relative}{(' — ' + note) if note else ''}")
        if verb.startswith(("wrote", "replaced", "would")):
            self.changed += 1

    def standards_version(self):
        done = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=STANDARDS_ROOT, capture_output=True, text=True)
        return done.stdout.strip() if done.returncode == 0 and done.stdout.strip() else "unknown"

    def put(self, relative, data: bytes, executable=False, governed=True):
        """Write a governed file when its content differs; report what happened."""
        full = self.path(relative)
        exists = os.path.isfile(full)
        same = exists and read_bytes(full) == data and (not executable or os.access(full, os.X_OK))
        if same:
            self.say("unchanged", relative)
            return False
        verb = ("would replace" if exists else "would write") if self.dry_run else ("replaced" if exists else "wrote")
        self.say(verb, relative, "governed" if governed else "")
        if not self.dry_run:
            os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
            with open(full, "wb") as handle:
                handle.write(data)
            if executable:
                os.chmod(full, os.stat(full).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return True

    def put_json(self, relative, data):
        return self.put(relative, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))

    def put_seed(self, relative, data: bytes, replace_when_unedited=True):
        """A founder-owned seed: written when absent, replaced only while it still equals a shipped seed."""
        full = self.path(relative)
        shipped = sha256(data)
        recorded = self.seeds.get(relative, {}).get("sha256")
        if not os.path.isfile(full):
            self.say("would write" if self.dry_run else "wrote", relative, "seed — yours to edit from here")
            if not self.dry_run:
                os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
                with open(full, "wb") as handle:
                    handle.write(data)
            self.seeds[relative] = {"sha256": shipped, "written": self.today.isoformat()}
            return
        current = sha256(read_bytes(full))
        if current == shipped:
            self.say("unchanged", relative, "seed")
            self.seeds[relative] = {"sha256": shipped, "written": self.seeds.get(relative, {}).get("written", self.today.isoformat())}
            return
        if replace_when_unedited and current == recorded:
            self.say("would replace" if self.dry_run else "replaced", relative, "seed still matched the shipped one, so it took this version")
            if not self.dry_run:
                with open(full, "wb") as handle:
                    handle.write(data)
            self.seeds[relative] = {"sha256": shipped, "written": self.today.isoformat()}
            return
        self.say("kept (founder-edited)", relative, "differs from the shipped seed; not touched")

    # -- the steps

    def install_checks(self):
        for name in sorted(os.listdir(CHECKS_DIR)):
            source = os.path.join(CHECKS_DIR, name)
            if not os.path.isfile(source) or name in CHECKS_NOT_SHIPPED or name.startswith("."):
                continue
            if not name.endswith((".py", ".json")):
                continue
            self.put(f"{PROJECT_CHECKS_DIR}/{name}", read_bytes(source), executable=name.endswith(".py"))

    def install_hooks(self):
        for name in HOOK_NAMES:
            source = os.path.join(HOOKS_DIR, name)
            if not os.path.isfile(source):
                self.say("note", f"{PROJECT_HOOKS_DIR}/{name}", "not shipped by the standards repo yet")
                continue
            self.put(f"{PROJECT_HOOKS_DIR}/{name}", read_bytes(source), executable=True)
        self.put(".coast/platform", (self.platform + "\n").encode("utf-8"))
        self.put(".coast/standards-version", (self.standards_commit + "\n").encode("utf-8"))

    def install_seeds(self):
        battery = json.loads(read_bytes(BATTERY))
        linters = battery.get("platforms", {}).get(self.platform, {}).get("linters", {})
        for linter, entry in linters.items():
            config = entry.get("config", "")
            name = os.path.basename(config)
            source = os.path.join(STANDARDS_ROOT, config)
            dest = LINT_DESTINATIONS.get(name, name)
            if not os.path.isfile(source):
                self.say("note", dest, f"the {linter} config {config} is not shipped by the standards repo yet")
                continue
            self.put_seed(dest, read_bytes(source))
        rules_doc = os.path.join(STANDARDS_ROOT, "rules", "platform", f"domain-rules-{self.platform}.md")
        if os.path.isfile(rules_doc):
            self.put_seed("docs/domain-rules.md", read_bytes(rules_doc), replace_when_unedited=False)
        else:
            self.say("note", "docs/domain-rules.md", f"no rules document for {self.platform} in the standards repo")

    def rules_number(self):
        """verify_rules.py on the project's rules document (the corpus document when it has none)."""
        document = self.path("docs/domain-rules.md")
        if not os.path.isfile(document):
            document = os.path.join(STANDARDS_ROOT, "rules", "platform", f"domain-rules-{self.platform}.md")
        done = subprocess.run([sys.executable, os.path.join(CHECKS_DIR, "verify_rules.py"), "--document", document,
                               "--platform", self.platform, "--json"], cwd=STANDARDS_ROOT, capture_output=True, text=True)
        try:
            totals = json.loads(done.stdout)["totals"]
        except (ValueError, KeyError):
            totals = {}
        return {key: totals.get(key, 0) for key in ("machine", "partly", "advisory", "review", "process", "open", "total")}

    def install_claude_md(self):
        counts = self.rules_number()
        template = read_bytes(TEMPLATE).decode("utf-8")
        filled = template
        for key, value in {"STANDARDS_PATH": STANDARDS_ROOT, "PLATFORM": self.platform,
                           "STANDARDS_COMMIT": self.standards_commit, "RULES_DOCUMENT": "docs/domain-rules.md",
                           "ENFORCED": counts["machine"], "TOTAL": counts["total"], "PARTLY": counts["partly"],
                           "ADVISORY": counts["advisory"], "REVIEW": counts["review"], "PROCESS": counts["process"],
                           "OPEN": counts["open"]}.items():
            filled = filled.replace("{{" + key + "}}", str(value))
        block = filled.strip("\n")
        full = self.path("CLAUDE.md")
        if os.path.isfile(full):
            existing = read_bytes(full).decode("utf-8")
            start, end = existing.find(BLOCK_BEGIN), existing.find(BLOCK_END)
            if start != -1 and end != -1 and end > start:
                new = existing[:start] + block + existing[end + len(BLOCK_END):]
            else:
                new = existing.rstrip("\n") + "\n\n" + block + "\n"
        else:
            new = f"# {os.path.basename(self.project)} — Agent Context\n\n{block}\n"
        self.put("CLAUDE.md", new.encode("utf-8"), governed=False)
        self.say("note", "CLAUDE.md", f"rules held by a machine {counts['machine']} of {counts['total']}")

    def write_ratchet_baseline(self):
        done = subprocess.run([sys.executable, os.path.join(CHECKS_DIR, "check_rules.py"), "--tree", "--platform", self.platform,
                               "--today", self.today.isoformat()], cwd=self.project, capture_output=True, text=True)
        counts = {}
        for match in re.finditer(r"^(?:OK|FAIL) ratchet (\S+): (\d+) in the tree", done.stdout, re.M):
            counts[match.group(1)] = int(match.group(2))
        existing = self.load_json(".coast/ratchet-baseline.json") or {}
        entries = {e["id"]: e for e in existing.get("baselines", []) if isinstance(e, dict) and "id" in e}
        deadline = (self.today + _dt.timedelta(days=RATCHET_DAYS)).isoformat()
        for signature_id, count in sorted(counts.items()):
            entry = entries.get(signature_id)
            if entry is None:
                entries[signature_id] = {"id": signature_id, "count": count, "deadline": deadline,
                                         "written": self.today.isoformat(), "by": self.by, "moves": []}
            elif count < entry.get("count", 0):
                self.say("note", ".coast/ratchet-baseline.json", f"{signature_id} fell {entry.get('count')} → {count}; lowered (its deadline {entry.get('deadline')} stays)")
                entry["count"] = count
            elif count > entry.get("count", 0):
                self.say("note", ".coast/ratchet-baseline.json", f"{signature_id} is {count} in the tree, above its baseline of {entry.get('count')} — NOT raised; the push will refuse until it comes down")
        data = {"_comment": "Ratchet baselines (enforcement/README.md decision 2): each count may only fall; past its deadline the check blocks. Only a person moves a deadline, recorded under moves.",
                "baselines": [entries[k] for k in sorted(entries)]}
        self.put_json(".coast/ratchet-baseline.json", data)

    def find_jscpd(self):
        if self.jscpd_bin:
            return [self.jscpd_bin]
        env = os.environ.get("JSCPD_BIN")
        if env:
            return [env]
        found = shutil.which("jscpd")
        if found:
            return [found]
        probe = subprocess.run(["npx", "--no-install", "jscpd", "--version"], cwd=self.project, capture_output=True, text=True)
        if probe.returncode == 0:
            return ["npx", "--no-install", "jscpd"]
        return None

    def write_jscpd_baseline(self):
        relative = ".coast/jscpd-baseline.json"
        existing = self.load_json(relative)
        deadline = (self.today + _dt.timedelta(days=RATCHET_DAYS)).isoformat()
        command = self.find_jscpd()
        if command is None:
            if existing is None:
                self.put_json(relative, {"version": 1, "fingerprints": {}, "clones": None,
                                         "note": f"jscpd was not installed when adopt.py ran; install jscpd@{JSCPD_PIN} and re-run adopt.py — the pre-push jscpd seat refuses until this is written",
                                         "written": self.today.isoformat(), "by": self.by, "deadline": deadline, "moves": []})
            else:
                self.say("note", relative, "jscpd is not installed; the clone baseline was not refreshed")
            return
        with tempfile.TemporaryDirectory() as scratch:
            scratch_baseline = os.path.join(scratch, "baseline.json")
            done = subprocess.run([*command, ".", "--min-tokens", JSCPD_MIN_TOKENS, "--ignore", JSCPD_IGNORE,
                                   "--baseline", scratch_baseline, "--update-baseline",
                                   "--reporters", "json", "--output", scratch, "--silent"],
                                  cwd=self.project, capture_output=True, text=True)
            report = os.path.join(scratch, "jscpd-report.json")
            if done.returncode != 0 or not os.path.isfile(report) or not os.path.isfile(scratch_baseline):
                self.say("note", relative, f"jscpd did not produce a report: {done.stderr.strip() or done.stdout.strip()[:200]}")
                return
            clones = json.loads(read_bytes(report))["statistics"]["total"]["clones"]
            fingerprints = json.loads(read_bytes(scratch_baseline)).get("fingerprints", {})
        if existing is None or existing.get("clones") is None:
            data = {"version": 1, "fingerprints": fingerprints, "clones": clones, "written": self.today.isoformat(),
                    "by": self.by, "deadline": deadline, "moves": [],
                    "_comment": f"jscpd {JSCPD_PIN} clone baseline (enforcement/README.md decision 2): the pre-push seat refuses clones absent from these fingerprints; the count may only fall; past the deadline any clone refuses."}
        elif clones < existing.get("clones", 0):
            self.say("note", relative, f"clones fell {existing.get('clones')} → {clones}; lowered (deadline {existing.get('deadline')} stays)")
            data = dict(existing, fingerprints=fingerprints, clones=clones)
        elif clones > existing.get("clones", 0):
            self.say("note", relative, f"{clones} clones in the tree, above the baseline of {existing.get('clones')} — NOT raised; the push refuses the new ones")
            data = existing
        else:
            data = existing
        self.put_json(relative, data)

    def set_hooks_path(self):
        current = git(self.project, "config", "--get", "core.hooksPath", check=False)
        if current == PROJECT_HOOKS_DIR:
            self.say("unchanged", "git config core.hooksPath", PROJECT_HOOKS_DIR)
            return
        self.say("would set" if self.dry_run else "set", "git config core.hooksPath", PROJECT_HOOKS_DIR)
        if not self.dry_run:
            git(self.project, "config", "core.hooksPath", PROJECT_HOOKS_DIR)

    def secret_scan_tree(self):
        """The scanner's secret-literal group over every tracked file (the first-push scan). Returns the FAIL lines."""
        listed = git(self.project, "ls-files", "-z")
        files = [f for f in listed.split("\0") if f and os.path.isfile(self.path(f))]
        findings = []
        for start in range(0, len(files), 400):
            chunk = files[start:start + 400]
            done = subprocess.run([sys.executable, os.path.join(CHECKS_DIR, "check_rules.py"), "--platform", self.platform,
                                   "--files", *chunk], cwd=self.project, capture_output=True, text=True)
            for line in done.stdout.splitlines():
                if line.startswith("FAIL ") and any(f":{sid}:" in line for sid in SECRET_IDS):
                    findings.append(line)
        return findings

    def run(self):
        clean_git_env()
        self.install_checks()
        self.install_hooks()
        self.install_seeds()
        self.install_claude_md()
        self.write_ratchet_baseline()
        self.write_jscpd_baseline()
        if self.seeds or os.path.isfile(self.path(".coast/seeds.json")):
            self.put_json(".coast/seeds.json", dict(sorted(self.seeds.items())))
        self.set_hooks_path()
        secrets = []
        if self.first_adoption or self.secret_scan:
            secrets = self.secret_scan_tree()
            self.say("note", "secret scan", f"{len(secrets)} finding(s) over {'the tracked tree'}")
        return secrets


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install the Up Coast enforcement layer into a project, idempotently.")
    parser.add_argument("project", help="the project's root (a git repository)")
    parser.add_argument("--platform", choices=PLATFORMS, help="one word; default: the project's .coast/platform, else detected from its manifests")
    parser.add_argument("--dry-run", action="store_true", help="print what would change and write nothing")
    parser.add_argument("--by", help="who is adopting (recorded in the baselines); default: git user.name")
    parser.add_argument("--today", help=argparse.SUPPRESS)
    parser.add_argument("--secret-scan", action="store_true", help="run the tracked-tree secret scan even after the first adoption")
    parser.add_argument("--jscpd-bin", help="a jscpd binary to use (default: JSCPD_BIN, PATH, then npx --no-install)")
    args = parser.parse_args(argv)

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        print(f"adopt.py: {project} is not a directory")
        return 2
    clean_git_env()
    top = git(project, "rev-parse", "--show-toplevel", check=False)
    if not top:
        print(f"adopt.py: {project} is not inside a git repository — git init first")
        return 2
    project = os.path.realpath(top)

    platform = args.platform
    if not platform and os.path.isfile(os.path.join(project, ".coast", "platform")):
        platform = read_bytes(os.path.join(project, ".coast", "platform")).decode("utf-8").strip()
    if not platform:
        platform = detect_platform(project)
    if platform not in PLATFORMS:
        print(f"adopt.py: could not tell the platform from the project's files — pass --platform one of {', '.join(PLATFORMS)}")
        return 2

    by = args.by or git(project, "config", "--get", "user.name", check=False) or os.environ.get("USER", "unknown")
    today = _dt.date.fromisoformat(args.today) if args.today else _dt.date.today()
    adoption = Adoption(project, platform, args.dry_run, by, today, args.jscpd_bin, args.secret_scan)
    secrets = adoption.run()

    print(f"adopt.py — {project} ({platform}){' — DRY RUN, nothing written' if args.dry_run else ''}")
    for line in adoption.lines:
        print("  " + line)
    print(f"{adoption.changed} file(s) {'would change' if args.dry_run else 'changed'}.")
    if secrets:
        print("Secrets in the tracked tree — do not push until these are out of the history:")
        for line in secrets:
            print(line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
