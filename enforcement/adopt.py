#!/usr/bin/env python3
"""adopt.py — install the enforcement layer into a project, idempotently
(enforcement task E2.2; design enforcement/README.md §4.6).

Run from anywhere::

    python3 enforcement/adopt.py <project-dir> [--platform <p>] [--dry-run]
                                 [--by <name>] [--today YYYY-MM-DD]
                                 [--secret-scan] [--jscpd-bin <path>]
                                 [--measure-tools [build,format,lint,tests]]

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
* ``CLAUDE.md``: the block between the ``coast-standards: begin/end``
  markers (the older ``up-coast-standards`` markers are recognised too, so
  a re-adopt replaces that block instead of adding a second) is rewritten
  from ``enforcement/TEMPLATE-PROJECT-CLAUDE.md`` with the platform, the
  standards commit and the enforced/total number (``verify_rules.py`` on
  the project's rules document); text outside the markers is the founder's
  and untouched. A CLAUDE.md with no markers gets the block appended once;
  markers in any other arrangement refuse the run before anything is written.
* ``.coast/installed.json``: the governed files this run put under
  ``Scripts/checks/``, ``.githooks/`` and ``Scripts/hooks/``; a later run
  removes any of them a newer release stops shipping.
* Baselines (decision 2: written once, the count may only fall, the
  deadline 90 days from the day it was written and never moved here):
  ``.coast/ratchet-baseline.json`` from the scanner's current tree counts
  (``check_rules.py --tree``) and, with ``--measure-tools``, from the tools
  the pre-push battery runs (``.githooks/pre-push --measure build,format,lint,tests``:
  the build's distinct warnings as ``build-warnings``, the formatter's
  findings as ``format-findings``, the linter's as ``lint-findings``, and
  ``tests-missing`` 1 for a project with no test target at all — the rule is "zero NEW warnings", so a
  repository that already carries some ratchets them down instead of being
  refused wholesale; a count of zero writes nothing and the seat stays
  strict); ``.coast/jscpd-baseline.json`` from jscpd's
  own ``--update-baseline`` fingerprints plus the clone count — or
  ``"clones": null`` with a note when jscpd is not installed. On a re-run a
  count that fell is lowered (dates kept); a count that rose is left as it
  is and reported — nothing here raises a baseline.
* The Claude Code session layer (E2.1, E2.8): ``Scripts/hooks/claude-hook.py``
  (GOVERNED) and ``.claude/settings.json`` — its ``hooks`` and
  ``disableAllHooks`` keys are governed and rewritten from
  ``enforcement/hooks/claude-settings.json``, the shipped ``permissions.deny``
  rules are merged in front of the project's own; any other key in an
  existing settings file is the founder's and kept.
* ``git config core.hooksPath .githooks``.
* A first-push secret scan (the first adoption, or ``--secret-scan``): the
  scanner's ``secret-literal`` group over every tracked file; findings are
  printed as FAIL lines and the exit code is 1.

Running it twice on the same tree produces no change the second time; the
report says ``wrote``, ``replaced``, ``unchanged`` or ``kept (founder-edited)``
per file. ``--dry-run`` prints the same report and writes nothing. Stdlib
only. No network, except ``--release``: it fetches a published release of the
standards (a GitHub tag's tarball) into a cache and installs from that copy, so
no clone of the standards repository is needed and "upgrade this project to
1.2.0" is one command. ``.coast/standards-version`` records the release
installed (``1.2.0``), or ``1.2.0+<commit>`` from an unreleased clone.
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

VERSION_FILE = os.path.join(STANDARDS_ROOT, "CHECKS-VERSION")
# A release is the tag vN.N.N on the public repository; its tarball is the copy a
# project installs from when no clone is at hand. The base may be overridden (a
# file:// URL in the tests, a mirror in a locked-down network).
RELEASES_REPO = "Up-Coast/coast-standards"
RELEASES_BASE = os.environ.get("COAST_STANDARDS_RELEASES", f"https://github.com/{RELEASES_REPO}/archive/refs/tags/")
LATEST_RELEASE_API = f"https://api.github.com/repos/{RELEASES_REPO}/releases/latest"
CACHE_DIR = os.environ.get("COAST_STANDARDS_CACHE") or os.path.join(
    os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache"), "coast-standards")

PROJECT_CHECKS_DIR = "Scripts/checks"
PROJECT_HOOKS_DIR = ".githooks"
PROJECT_CLAUDE_HOOK = "Scripts/hooks/claude-hook.py"   # the path claude-settings.json's commands name
PROJECT_CLAUDE_SETTINGS = ".claude/settings.json"
HOOK_NAMES = ("pre-commit", "pre-push", "commit-msg")
# The folders whose every file is the installer's: what a release stops shipping is removed
# from them on the next run (.coast/installed.json records what this one put there).
GOVERNED_FOLDERS = (PROJECT_CHECKS_DIR + "/", PROJECT_HOOKS_DIR + "/", os.path.dirname(PROJECT_CLAUDE_HOOK) + "/")
INSTALLED_MANIFEST = ".coast/installed.json"
CHECKS_NOT_SHIPPED = {"verify_rules.py", "battery.json", "verify-baseline.json"}  # they read this repo, not a project


def number_label():
    """The headline number's wording, from checks/vocabulary.json (the one place it is defined)."""
    try:
        with open(os.path.join(CHECKS_DIR, "vocabulary.json"), encoding="utf-8") as handle:
            return json.load(handle)["number"]["label"]
    except (OSError, ValueError, KeyError):
        return "enforced by a check"
PLATFORMS = ("ios", "macos", "android", "react-native", "web", "python")
RATCHET_DAYS = 90
JSCPD_PIN = "5.1.2"
JSCPD_MIN_TOKENS = "50"
# Code only: DRY-5 is about duplicated code, and a plan, a transcript or a data file
# repeats itself on purpose (a handoff note on Coast read as ten new clones).
# Keep in step with the `ignore=` line of enforcement/hooks/pre-push.
JSCPD_IGNORE = ("**/node_modules/**,**/.build/**,**/build/**,**/Pods/**,**/DerivedData/**,**/dist/**,"
                "**/.venv/**,**/__pycache__/**,**/.coast/**,**/Scripts/checks/**,**/.githooks/**,"
                "**/*.min.js,**/*.lock,**/Package.resolved,"
                "**/*.md,**/*.markdown,**/*.txt,**/*.json,**/*.jsonl,**/*.yml,**/*.yaml,**/*.toml,**/*.html,**/*.svg,**/*.xml,**/*.plist,**/*.strings,**/*.xcstrings,**/*.stringsdict")
BLOCK_BEGIN = "<!-- coast-standards: begin"
BLOCK_END = "<!-- coast-standards: end -->"
# The markers before the rename; a re-adopt replaces a block written under them.
OLD_BLOCK_BEGIN = "<!-- up-coast-standards: begin"
OLD_BLOCK_END = "<!-- up-coast-standards: end -->"
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


def pbxproj_platforms(project):
    """The Apple platforms an Xcode project builds for, read from every ``*.xcodeproj/project.pbxproj``
    in the project root or one folder down: ``SDKROOT = iphoneos`` / ``macosx`` and the
    ``SUPPORTED_PLATFORMS`` build settings. A set drawn from {"ios", "macos"}."""
    found = set()
    candidates = []
    for name in sorted(os.listdir(project)):
        full = os.path.join(project, name)
        if not os.path.isdir(full) or name.startswith("."):
            continue
        if name.endswith(".xcodeproj"):
            candidates.append(os.path.join(full, "project.pbxproj"))
        else:
            for inner in sorted(os.listdir(full)):
                if inner.endswith(".xcodeproj"):
                    candidates.append(os.path.join(full, inner, "project.pbxproj"))
    for pbxproj in candidates:
        if not os.path.isfile(pbxproj):
            continue
        text = read_bytes(pbxproj).decode("utf-8", "replace")
        for match in re.finditer(r'(?m)^\s*(SDKROOT|SUPPORTED_PLATFORMS)\s*=\s*"?([^";]*)"?\s*;', text):
            words = match.group(2).lower().split()
            if any(w.startswith("iphone") for w in words):
                found.add("ios")
            if "macosx" in words:
                found.add("macos")
    return found


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
        # An app without Package.swift (or one naming both platforms) is an Xcode project: its
        # pbxproj says which SDK it builds for. Every one of the owner's apps is shaped this way.
        platforms = pbxproj_platforms(project)
        if platforms == {"ios"}:
            return "ios"
        if platforms == {"macos"}:
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


def checks_version():
    """The number in CHECKS-VERSION, the one place the standards are versioned."""
    try:
        return read_bytes(VERSION_FILE).decode("utf-8").strip()
    except OSError:
        return "0.0.0"


def standards_version():
    """The release this copy of the standards is: ``1.2.0`` when the copy is a release
    (a tarball, or a clone checked out at the tag ``v1.2.0``), ``1.2.0+<commit>`` from
    a clone that is not at a release tag."""
    version = checks_version()
    if not os.path.isdir(os.path.join(STANDARDS_ROOT, ".git")):
        return version
    tagged = subprocess.run(["git", "tag", "--points-at", "HEAD"], cwd=STANDARDS_ROOT, capture_output=True, text=True)
    if tagged.returncode == 0 and f"v{version}" in tagged.stdout.split():
        return version
    done = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=STANDARDS_ROOT, capture_output=True, text=True)
    commit = done.stdout.strip() if done.returncode == 0 else ""
    return f"{version}+{commit}" if commit else version


def latest_release():
    """The newest published release's version, from the repository's releases API."""
    import urllib.request
    with urllib.request.urlopen(LATEST_RELEASE_API, timeout=30) as response:
        tag = json.load(response).get("tag_name", "")
    if not tag.startswith("v"):
        raise SystemExit(f"adopt.py: could not read the latest release from {LATEST_RELEASE_API}")
    return tag[1:]


def fetch_release(version):
    """The directory holding release ``version`` of the standards, fetched into the cache
    once (``<cache>/<version>/``); a later call finds it there and fetches nothing."""
    import tarfile
    import urllib.request
    target = os.path.join(CACHE_DIR, version)
    if os.path.isfile(os.path.join(target, "enforcement", "adopt.py")):
        return target
    url = f"{RELEASES_BASE}v{version}.tar.gz"
    os.makedirs(CACHE_DIR, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=CACHE_DIR) as work:
        archive = os.path.join(work, "release.tar.gz")
        try:
            with urllib.request.urlopen(url, timeout=120) as response, open(archive, "wb") as handle:
                shutil.copyfileobj(response, handle)
        except OSError as error:
            raise SystemExit(f"adopt.py: could not fetch release {version} from {url}: {error}")
        with tarfile.open(archive) as tar:
            members = [m for m in tar.getmembers() if not (m.issym() or m.islnk()) and ".." not in m.name.split("/")]
            tar.extractall(work, members=members)
        roots = [d for d in os.listdir(work) if os.path.isdir(os.path.join(work, d))]
        if len(roots) != 1 or not os.path.isfile(os.path.join(work, roots[0], "enforcement", "adopt.py")):
            raise SystemExit(f"adopt.py: {url} is not a release of the standards (no enforcement/adopt.py inside)")
        fetched = read_bytes(os.path.join(work, roots[0], "CHECKS-VERSION")).decode("utf-8").strip()
        if fetched != version:
            raise SystemExit(f"adopt.py: release {version} says it is {fetched} — refusing to install a mislabelled release")
        shutil.rmtree(target, ignore_errors=True)
        shutil.move(os.path.join(work, roots[0]), target)
    return target


class Adoption:
    def __init__(self, project, platform, dry_run, by, today, jscpd_bin, secret_scan, measure_tools=None):
        self.project = project
        self.platform = platform
        self.dry_run = dry_run
        self.by = by
        self.today = today
        self.jscpd_bin = jscpd_bin
        self.secret_scan = secret_scan
        self.measure_tools = measure_tools
        self.lines = []
        self.changed = 0
        self.first_adoption = not os.path.isfile(self.path(".coast/platform"))
        if self.measure_tools is None:
            # A first adoption always measures. An existing repository has warnings, lint
            # findings and formatter findings already; without their baselines its first
            # push meets a strict toolchain and refuses everything, which is not a choice
            # anyone should have to make — it is just what adopting an existing repo means.
            self.measure_tools = "build,format,lint,tests" if self.first_adoption else ""
        self.seeds = self.load_json(".coast/seeds.json") or {}
        self.installed = []   # the governed files this run put under GOVERNED_FOLDERS
        self.standards_commit = self.standards_version()
        self.rules_document = None   # the document the number is counted from, once install_seeds decides

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
        if verb.startswith(("wrote", "replaced", "removed", "would")):
            self.changed += 1

    def standards_version(self):
        return standards_version()

    def put(self, relative, data: bytes, executable=False, governed=True):
        """Write a governed file when its content differs; report what happened."""
        full = self.path(relative)
        if governed and relative.startswith(GOVERNED_FOLDERS):
            self.installed.append(relative)
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

    def note_case_folded_collision(self):
        """macOS folds case: writing Scripts/ beside an existing scripts/ lands the checks inside scripts/,
        git records them there, and a Linux clone — where the two spellings are different folders —
        finds nothing at the path the hooks and settings name. Said out loud; the layout is not yet
        configurable (enforcement/README.md, review of 2026-09-07)."""
        wanted = PROJECT_CHECKS_DIR.split("/")[0]
        for name in os.listdir(self.project):
            if name != wanted and name.lower() == wanted.lower() and os.path.isdir(self.path(name)):
                self.say("note", f"{wanted}/", f"this project already has {name}/ — on this case-folding filesystem the "
                         f"checks land inside it and git records them as {name}/checks; a Linux clone will not find "
                         f"them at {wanted}/checks. Rename {name}/ before adopting if the project is built anywhere but a Mac")

    def install_checks(self):
        self.note_case_folded_collision()
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
        self.install_claude_hooks()

    def install_claude_hooks(self):
        """The Claude Code session layer (E2.1, decision 3): the one hook entry point, governed,
        and the committed .claude/settings.json — its ``hooks`` key is governed and rewritten from
        the shipped template; every other key in an existing settings file is the founder's and kept."""
        entry = os.path.join(HOOKS_DIR, "claude-hook.py")
        template = os.path.join(HOOKS_DIR, "claude-settings.json")
        if not os.path.isfile(entry) or not os.path.isfile(template):
            self.say("note", PROJECT_CLAUDE_SETTINGS, "the Claude Code hooks are not shipped by the standards repo yet")
            return
        self.put(PROJECT_CLAUDE_HOOK, read_bytes(entry), executable=True)
        with open(template, encoding="utf-8") as handle:
            shipped = json.load(handle)
        existing = self.load_json(PROJECT_CLAUDE_SETTINGS) or {}
        merged = dict(existing)
        merged["hooks"] = shipped["hooks"]
        merged["_comment"] = shipped.get("_comment", "")
        # E2.8: the permission layer travels with the hooks. `disableAllHooks` is replaced (a project false
        # overrides a user true, per the hooks page); the shipped deny rules go in front of the project's own
        # deny list, once each; the project's allow/ask and every other key are the founder's and kept.
        if "disableAllHooks" in shipped:
            merged["disableAllHooks"] = shipped["disableAllHooks"]
        shipped_deny = list((shipped.get("permissions") or {}).get("deny") or [])
        if shipped_deny:
            permissions = dict(existing.get("permissions") or {})
            own = [rule for rule in (permissions.get("deny") or []) if rule not in shipped_deny]
            permissions["deny"] = shipped_deny + own
            merged["permissions"] = permissions
        self.put_json(PROJECT_CLAUDE_SETTINGS, merged)

    def remove_stale_governed(self):
        """A module renamed or dropped upstream leaves its old file in Scripts/checks/ (or a hook in
        .githooks/) for ever, and a stale module still imports. The manifest says what the last run
        installed; whatever it named that this release did not ship is removed. Only files under the
        governed folders are ever touched, and only ones the installer itself wrote."""
        previous = self.load_json(INSTALLED_MANIFEST) or {}
        for relative in sorted(set(previous.get("files", []))):
            if relative in self.installed or not relative.startswith(GOVERNED_FOLDERS):
                continue
            full = self.path(relative)
            if not os.path.isfile(full):
                continue
            self.say("would remove" if self.dry_run else "removed", relative, "this release no longer ships it")
            if not self.dry_run:
                os.remove(full)
        self.put_json(INSTALLED_MANIFEST, {
            "_comment": "The governed files adopt.py installed; a later run removes any of them a newer release stops shipping.",
            "files": sorted(set(self.installed))})

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
            self.put_rules_document(read_bytes(rules_doc))
        else:
            self.say("note", "docs/domain-rules.md", f"no rules document for {self.platform} in the standards repo")

    @staticmethod
    def corpus_version(data):
        """The `<!-- coast-rules-version: N -->` stamp on the document's first line, or None."""
        found = re.search(rb"coast-rules-version:\s*(\d+)", data[:400])
        return int(found.group(1)) if found else None

    def put_rules_document(self, shipped):
        """docs/domain-rules.md is founder-owned, and it is also VERSIONED. A copy carrying an
        older corpus version is not a founder's edit to preserve — it is last year's rule book,
        and leaving it means the project's rules name checks that do not exist yet (one adopting web project
        sat at version 7 with three check tags, so its number read 0 of 54). An older stamp is
        upgraded and the copy it replaces is written beside it, so nothing a founder wrote is lost.
        A copy at the current version that differs is a founder's edit, and is left alone."""
        relative = "docs/domain-rules.md"
        full = self.path(relative)
        shipped_path = os.path.join(STANDARDS_ROOT, "rules", "platform", f"domain-rules-{self.platform}.md")
        if not os.path.isfile(full):
            self.put_seed(relative, shipped, replace_when_unedited=False)
            self.rules_document = shipped_path
            return
        current = read_bytes(full)
        if current == shipped:
            self.say("unchanged", relative, "seed")
            return
        have, want = self.corpus_version(current), self.corpus_version(shipped)
        if have is not None and want is not None and have < want:
            kept = f"docs/domain-rules.v{have}.md"
            self.put(kept, current, governed=False)
            self.put(relative, shipped, governed=False)
            self.say("note", relative, f"corpus version {have} → {want}; the copy it replaced is {kept}, "
                                       "so anything you wrote in it is still there")
            # count from the document that will be there, so a --dry-run reports the real number
            self.rules_document = shipped_path
            return
        self.say("kept (founder-edited)", relative, "differs from the shipped seed at the same corpus version; not touched")

    def rules_number(self):
        """verify_rules.py on the project's rules document (the corpus document when it has none)."""
        document = self.rules_document or self.path("docs/domain-rules.md")
        if not os.path.isfile(document):
            document = os.path.join(STANDARDS_ROOT, "rules", "platform", f"domain-rules-{self.platform}.md")
        done = subprocess.run([sys.executable, os.path.join(CHECKS_DIR, "verify_rules.py"), "--document", document,
                               "--platform", self.platform, "--json"], cwd=STANDARDS_ROOT, capture_output=True, text=True)
        try:
            totals = json.loads(done.stdout)["totals"]
        except (ValueError, KeyError):
            totals = {}
        return {key: totals.get(key, 0) for key in ("machine", "partly", "advisory", "review", "process", "open", "total")}

    @staticmethod
    def block_span(text):
        """Where the standards block sits in CLAUDE.md: (start, end) of the last begin marker and the
        first end marker after it, None when the file has no markers. Both marker names count (a
        block written under the old ``up-coast-standards`` name is replaced, not doubled). Markers
        in any other arrangement — an end before its begin, a begin with no end, a stray marker
        outside the pair — are refused out loud: the old code appended a block on every run and,
        after an orphaned begin, deleted the founder's text on the next. Nothing is guessed here."""
        begins = [m.start() for m in re.finditer(re.escape(BLOCK_BEGIN) + "|" + re.escape(OLD_BLOCK_BEGIN), text)]
        ends = [(m.start(), m.end()) for m in re.finditer(re.escape(BLOCK_END) + "|" + re.escape(OLD_BLOCK_END), text)]
        if not begins and not ends:
            return None
        problem = None
        if len(begins) != 1 or len(ends) != 1:
            problem = f"{len(begins)} begin marker(s) and {len(ends)} end marker(s)"
        elif ends[0][0] < begins[0]:
            problem = "the end marker comes before the begin marker"
        if problem:
            raise SystemExit("adopt.py: CLAUDE.md has " + problem + " — keep exactly one "
                             f"'{BLOCK_BEGIN} … -->' … '{BLOCK_END}' pair (or none) and run again; nothing was written")
        return begins[-1], ends[0][1]

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
            span = self.block_span(existing)
            if span:
                start, end = span
                new = existing[:start] + block + existing[end:]
            else:
                new = existing.rstrip("\n") + "\n\n" + block + "\n"
        else:
            new = f"# {os.path.basename(self.project)} — Agent Context\n\n{block}\n"
        self.put("CLAUDE.md", new.encode("utf-8"), governed=False)
        self.say("note", "CLAUDE.md", f"rules {number_label()} {counts['machine']} of {counts['total']}")

    def bind_theme(self):
        """An existing app already has a theme file, almost never at the platform's default
        path; unbound, it fails `second-theme-file` on every push. Bind the one it has (the
        first, sorted, when there are several — the others are then real second theme files)
        as the project's own `theme` class, and its folder as `ui_lib`, in .coast/paths.json.
        Written once; a founder edits it from there (it is GOVERNING: agents never do)."""
        if self.load_json(".coast/paths.json") is not None:
            return
        done = subprocess.run([sys.executable, os.path.join(CHECKS_DIR, "check_rules.py"), "--tree", "--platform", self.platform],
                              cwd=self.project, capture_output=True, text=True, env=clean_git_env())
        found = sorted(set(re.findall(r"^FAIL rules (\S+?):\d+:second-theme-file:", done.stdout, re.M)))
        if not found:
            return
        # The theme is the project's design-token home, not whichever path sorts first
        # (one adopting web project's tokens live in src/styles/, and alphabetical order picked
        # src/lib/email/tokens.ts). Rank by where a token file actually lives, then bind
        # EVERY token file in that folder: tokens.css and tokens.ts beside each other are
        # one token set in two formats, not a second theme.
        found.sort(key=lambda path: (-self.theme_rank(path), path))
        theme = found[0]
        folder = os.path.dirname(theme)
        siblings = [f for f in found if os.path.dirname(f) == folder] if folder else [theme]
        classes = {"theme": siblings}
        if folder:
            classes["ui_lib"] = [folder + "/**"]
        self.put_json(".coast/paths.json", {
            "_comment": "This project's own path-class bindings, merged over the platform's defaults (enforcement/README.md section 4.2). Written once by adopt.py from the theme file it found; a founder edits it from here.",
            "platforms": {self.platform: {"classes": classes}}})
        self.say("note", ".coast/paths.json", "bound the theme " + ", ".join(siblings)
                 + (f" (the folder {folder}/ is the UI library)" if folder else ""))
        elsewhere = [f for f in found if f not in siblings]
        if elsewhere:
            self.say("note", ".coast/paths.json", "theme-shaped files outside that folder still refuse as second theme files: "
                     + ", ".join(elsewhere))

    def measure_tool_counts(self):
        """The counts the pre-push tools report in --measure mode (the installed hook is the one
        home of the build and format commands): {id: count}. A tool that cannot run is a note."""
        if not self.measure_tools:
            return {}
        hook = self.path(f"{PROJECT_HOOKS_DIR}/pre-push")
        if not os.path.isfile(hook):
            self.say("note", "tool ratchets", "the pre-push hook is not installed, so nothing was measured")
            return {}
        env = dict(os.environ, COAST_CHECKS_DIR=self.path(PROJECT_CHECKS_DIR))
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY", "GIT_PREFIX"):
            env.pop(name, None)
        done = subprocess.run(["sh", hook, "--measure", self.measure_tools], cwd=self.project, capture_output=True, text=True, env=env)
        counts = {m.group(1): int(m.group(2)) for m in re.finditer(r"^MEASURE (\S+) (\d+)$", done.stdout, re.M)}
        if done.returncode != 0:
            failed = [line for line in (done.stdout + done.stderr).splitlines() if line.startswith(("FAIL ", "gate: ")) and "failed" in line]
            self.say("note", "tool ratchets", "a tool did not finish, so its count was not measured: " + ("; ".join(failed[-2:]) or "see the build output"))
        for signature_id, count in sorted(counts.items()):
            self.say("note", "tool ratchets", f"{signature_id} measured {count}" + ("" if count else " — the seat stays strict"))
        existing = self.load_json(".coast/ratchet-baseline.json") or {}
        held = {e.get("id") for e in existing.get("baselines", []) if isinstance(e, dict)}
        # a count of zero writes nothing (the seat stays strict) unless an entry exists to lower
        return {k: v for k, v in counts.items() if v > 0 or k in held}

    @staticmethod
    def theme_rank(path):
        """How much a path looks like the project's design-token home. Higher wins."""
        lowered = path.lower()
        score = 0
        for weight, marker in enumerate(("/styles/", "/style/", "/theme/", "/themes/", "/designsystem/",
                                         "/design-system/", "/design/", "/tokens/")):
            if marker in lowered:
                score = max(score, 20 - weight)
        name = os.path.basename(lowered)
        if name.startswith(("tokens.", "theme.", "colors.", "palette.")):
            score += 5
        return score

    def write_ratchet_baseline(self):
        done = subprocess.run([sys.executable, os.path.join(CHECKS_DIR, "check_rules.py"), "--tree", "--platform", self.platform,
                               "--today", self.today.isoformat()], cwd=self.project, capture_output=True, text=True)
        counts = {}
        for match in re.finditer(r"^(?:OK|FAIL) ratchet (\S+): (\d+) in the tree", done.stdout, re.M):
            counts[match.group(1)] = int(match.group(2))
        counts.update(self.measure_tool_counts())
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
        if not shutil.which("npx"):
            return None
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
        if current and current != PROJECT_HOOKS_DIR:
            self.keep_existing_hooks(current)
        elif not current:
            # No hooksPath means git runs the hooks in its own hooks directory (pre-commit-framework,
            # lefthook and the old husky install there). Pointing core.hooksPath at .githooks would
            # switch them off without a word — §4.8 promises they are not.
            git_hooks = git(self.project, "rev-parse", "--git-path", "hooks", check=False)
            if git_hooks and any(os.access(os.path.join(self.project, git_hooks, name), os.X_OK)
                                 and os.path.isfile(os.path.join(self.project, git_hooks, name)) for name in HOOK_NAMES):
                self.keep_existing_hooks(git_hooks)
        if current == PROJECT_HOOKS_DIR:
            self.say("unchanged", "git config core.hooksPath", PROJECT_HOOKS_DIR)
            return
        self.say("would set" if self.dry_run else "set", "git config core.hooksPath", PROJECT_HOOKS_DIR)
        if not self.dry_run:
            git(self.project, "config", "core.hooksPath", PROJECT_HOOKS_DIR)

    def keep_existing_hooks(self, current):
        """A project that already had hooks keeps them: ours run first, then its own.
        one adopting web project's pre-push ran gitleaks, a real secret scanner this layer does not
        have, and pointing core.hooksPath at .githooks switched it off without a word."""
        existing = os.path.join(self.project, current)
        kept = [name for name in HOOK_NAMES if os.path.isfile(os.path.join(existing, name))]
        if not kept:
            return
        self.put(".coast/previous-hooks-path", (current + "\n").encode("utf-8"))
        self.say("note", ".coast/previous-hooks-path",
                 f"this project already had {', '.join(kept)} in {current}/ — they are kept and run after ours")
        installer = self.package_script_setting_hooks_path()
        if installer:
            self.say("note", "package.json",
                     f'its "{installer}" script sets core.hooksPath back to {current} — change that one word to '
                     f'{PROJECT_HOOKS_DIR} or the next install turns these checks off')

    def package_script_setting_hooks_path(self):
        """The npm script that resets core.hooksPath, if the project has one."""
        data = self.load_json("package.json") or {}
        for name, command in (data.get("scripts") or {}).items():
            if isinstance(command, str) and "core.hooksPath" in command:
                return name
        return None

    def secret_scan_tree(self):
        """The scanner's secret-literal group over every tracked file (the first-push scan). Returns the FAIL lines."""
        listed = git(self.project, "ls-files", "-z")
        files = [f for f in listed.split("\0") if f and os.path.isfile(self.path(f))]
        findings = []
        for start in range(0, len(files), 400):
            chunk = files[start:start + 400]
            done = subprocess.run([sys.executable, os.path.join(CHECKS_DIR, "check_rules.py"), "--platform", self.platform,
                                   "--only", ",".join(sorted(SECRET_IDS)), "--files", *chunk],
                                  cwd=self.project, capture_output=True, text=True)
            for line in done.stdout.splitlines():
                if line.startswith("FAIL ") and any(f":{sid}:" in line for sid in SECRET_IDS):
                    findings.append(line)
        return findings

    def check_claude_md(self):
        """Refuse before anything is written when CLAUDE.md's markers make no sense."""
        full = self.path("CLAUDE.md")
        if os.path.isfile(full):
            self.block_span(read_bytes(full).decode("utf-8"))

    def run(self):
        clean_git_env()
        self.check_claude_md()
        self.install_checks()
        self.install_hooks()
        self.remove_stale_governed()
        self.install_seeds()
        self.install_claude_md()
        self.bind_theme()
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
    parser = argparse.ArgumentParser(description="Install the Coast Standards enforcement layer into a project, idempotently.")
    parser.add_argument("project", help="the project's root (a git repository)")
    parser.add_argument("--platform", choices=PLATFORMS, help="one word; default: the project's .coast/platform, else detected from its manifests")
    parser.add_argument("--dry-run", action="store_true", help="print what would change and write nothing")
    parser.add_argument("--by", help="who is adopting (recorded in the baselines); default: git user.name")
    parser.add_argument("--today", help=argparse.SUPPRESS)
    parser.add_argument("--secret-scan", action="store_true", help="run the tracked-tree secret scan even after the first adoption")
    parser.add_argument("--jscpd-bin", help="a jscpd binary to use (default: JSCPD_BIN, PATH, then npx --no-install)")
    parser.add_argument("--release", metavar="VERSION",
                        help="install from a published release of the standards (e.g. 1.2.0, or 'latest') fetched into "
                             f"{CACHE_DIR} instead of from this copy; the way to adopt or upgrade without a clone")
    parser.add_argument("--measure-tools", nargs="?", const="build,format,lint,tests", metavar="SEATS",
                        help="re-measure the tool baselines (build-warnings, format-findings, lint-findings, tests-missing). "
                             "A FIRST adoption measures them anyway; this forces it on a later run. SEATS narrows the work, "
                             "e.g. --measure-tools format,lint to re-measure without building")
    args = parser.parse_args(argv)

    if args.release:
        version = latest_release() if args.release == "latest" else args.release.lstrip("v")
        if version != checks_version() or os.path.isdir(os.path.join(STANDARDS_ROOT, ".git")):
            # Not this copy: fetch the release and let its own installer do the work.
            release_dir = fetch_release(version)
            forwarded, skip = [], False
            for word in (argv if argv is not None else sys.argv[1:]):
                if skip or word.startswith("--release="):
                    skip = False
                    continue
                if word == "--release":
                    skip = True
                    continue
                forwarded.append(word)
            print(f"adopt.py — installing Coast Standards {version} from {release_dir}")
            done = subprocess.run([sys.executable, os.path.join(release_dir, "enforcement", "adopt.py"), *forwarded])
            return done.returncode

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
    adoption = Adoption(project, platform, args.dry_run, by, today, args.jscpd_bin, args.secret_scan, args.measure_tools)
    secrets = adoption.run()

    print(f"adopt.py — {project} ({platform}){' — DRY RUN, nothing written' if args.dry_run else ''}")
    for line in adoption.lines:
        print("  " + line)
    print(f"{adoption.changed} file(s) {'would change' if args.dry_run else 'changed'}. "
          f"Coast Standards {adoption.standards_commit} — the version this project now carries (.coast/standards-version).")
    if secrets:
        print("Secrets in the tracked tree — do not push until these are out of the history:")
        for line in secrets:
            print(line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
