"""Tests for the git hooks and adopt.py (enforcement tasks E1.7 and E2.2).

Every promise has a plant on a throwaway git repository shaped like an iOS
project: adopting twice changes nothing the second time; a seed the
founder edited survives a re-adopt while an unedited one takes the new
shipped version; the installed pre-commit hook refuses a staged
ui-string-literal and passes a clean file; commit-msg refuses an empty
subject, a bare "Claude Code" trailer, and an agent-session commit with no
model named; and the pre-push jscpd seat refuses a copied block that is not
in the baseline. The jscpd plant needs the pinned jscpd (enforcement/
TOOLCHAIN.md): JSCPD_BIN, PATH, or `npx --no-install`; when none of those
has it the test FAILS out loud — it never skips.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import glob
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENFORCEMENT_DIR = os.path.dirname(CHECKS_DIR)
REPO_ROOT = os.path.dirname(ENFORCEMENT_DIR)
sys.path.insert(0, ENFORCEMENT_DIR)

import adopt  # noqa: E402

BLOCK = "".join(f"    let value{i} = compute(input: {i}, scale: {i * 3})\n    total += value{i} * factor\n" for i in range(12))
CLEAN_VIEW = "import SwiftUI\nstruct HomeView: View { var body: some View { Text(Copy.title) } }\n"
PLANTED_VIEW = 'import SwiftUI\nstruct HomeView: View { var body: some View { Text("Welcome back to the app") } }\n'


def clean_env(**overrides):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.pop("CLAUDECODE", None)
    env.update({"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x"})
    for key, value in overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def sh(cwd, *args, env=None):
    done = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env or clean_env())
    if done.returncode != 0:
        raise RuntimeError(f"{args} failed:\n{done.stdout}\n{done.stderr}")
    return done.stdout.strip()


def find_jscpd():
    """The pinned jscpd, or None — the caller fails loudly."""
    candidates = [os.environ.get("JSCPD_BIN"), shutil.which("jscpd")]
    candidates += sorted(glob.glob("/private/tmp/claude-501/*/*/scratchpad/jscpd-home/node_modules/.bin/jscpd"))
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    probe = subprocess.run(["npx", "--no-install", "jscpd", "--version"], capture_output=True, text=True)
    if probe.returncode == 0:
        return "npx --no-install jscpd"
    return None


class Project:
    """A throwaway iOS-shaped git repository adopt.py installs into."""

    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.realpath(self.dir.name)
        sh(self.path, "git", "init", "-q", "-b", "main")
        self.write("Package.swift", '// swift-tools-version:6.0\nimport PackageDescription\nlet package = Package(name: "App", platforms: [.iOS(.v17)])\n')
        self.write("Sources/App/Views/HomeView.swift", CLEAN_VIEW)
        self.write("Sources/App/One.swift", "import Foundation\nfunc one(input: Int) -> Int {\n    var total = 0\n" + BLOCK + "    return total\n}\n")
        self.commit("start")

    def write(self, relative, content):
        full = os.path.join(self.path, relative)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(content)

    def read(self, relative):
        with open(os.path.join(self.path, relative), encoding="utf-8") as handle:
            return handle.read()

    def commit(self, message):
        sh(self.path, "git", "add", "-A")
        sh(self.path, "git", "-c", "core.hooksPath=.git/hooks", "commit", "-q", "-m", message)

    def adopt(self, *extra):
        out = io.StringIO()
        with redirect_stdout(out):
            code = adopt.main([self.path, "--platform", "ios", "--by", "Tester", "--today", "2026-09-04", *extra])
        return code, out.getvalue()

    def snapshot(self):
        """Every file outside .git with its checksum, plus the hooks path."""
        files = {}
        for root, dirs, names in os.walk(self.path):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for name in names:
                full = os.path.join(root, name)
                with open(full, "rb") as handle:
                    files[os.path.relpath(full, self.path)] = hashlib.sha256(handle.read()).hexdigest()
        hooks_path = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=self.path, capture_output=True, text=True, env=clean_env())
        files["<core.hooksPath>"] = hooks_path.stdout.strip()  # exit 1 when unset is not an error here
        return files

    def hook(self, name, *args, stdin="", env=None):
        done = subprocess.run(["sh", os.path.join(self.path, ".githooks", name), *args], cwd=self.path,
                              capture_output=True, text=True, input=stdin, env=env or clean_env())
        return done.returncode, done.stdout + done.stderr

    def cleanup(self):
        self.dir.cleanup()


class AdoptTests(unittest.TestCase):
    def setUp(self):
        self.project = Project()
        self.addCleanup(self.project.cleanup)

    def test_adopting_twice_changes_nothing_the_second_time(self):
        code, first = self.project.adopt()
        self.assertEqual(code, 0, first)
        before = self.project.snapshot()
        self.assertIn("Scripts/checks/check_rules.py", before)
        for hook in ("pre-commit", "pre-push", "commit-msg"):
            self.assertIn(f".githooks/{hook}", before)
            self.assertTrue(os.access(os.path.join(self.project.path, ".githooks", hook), os.X_OK))
        self.assertEqual(before["<core.hooksPath>"], ".githooks")
        self.assertEqual(self.project.read(".coast/platform").strip(), "ios")
        baseline = json.loads(self.project.read(".coast/ratchet-baseline.json"))
        ids = {entry["id"]: entry for entry in baseline["baselines"]}
        self.assertIn("spacing-literal", ids)
        self.assertEqual(ids["spacing-literal"]["deadline"], "2026-12-03")
        self.assertEqual(ids["spacing-literal"]["written"], "2026-09-04")
        self.assertEqual(ids["spacing-literal"]["by"], "Tester")
        claude_md = self.project.read("CLAUDE.md")
        self.assertIn("Rules held by a machine", claude_md)
        self.assertIn("up-coast-standards: end", claude_md)

        code, second = self.project.adopt()
        self.assertEqual(code, 0, second)
        self.assertEqual(self.project.snapshot(), before)
        self.assertIn("0 file(s) changed", second)
        self.assertNotIn("wrote", second.replace("would write", ""))

    def test_adoption_installs_the_claude_session_hooks_and_keeps_other_settings(self):
        self.project.write(".claude/settings.json", json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}}))
        code, _ = self.project.adopt()
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.project.path, "Scripts/hooks/claude-hook.py")))
        settings = json.loads(self.project.read(".claude/settings.json"))
        self.assertEqual(settings["permissions"], {"allow": ["Bash(ls:*)"]}, "the founder's own settings must survive")
        self.assertIn("PreToolUse", settings["hooks"])
        commands = json.dumps(settings["hooks"])
        for hook_id in ("governing-edit", "chained-cd", "infra-command", "no-verify", "force-push",
                        "scan-at-commit", "scan-on-edit", "unpushed-at-stop", "rules-at-start"):
            self.assertIn(hook_id, commands, f"the settings file must wire {hook_id}")
        self.assertIn("Scripts/hooks/claude-hook.py", commands)

    def test_pre_push_builds_an_xcode_project_through_xcodebuild_with_warnings_as_errors(self):
        # An xcodegen app: no Package.swift, an .xcodeproj, a stub xcodebuild on PATH that records its arguments.
        os.remove(os.path.join(self.project.path, "Package.swift"))
        os.makedirs(os.path.join(self.project.path, "App.xcodeproj"), exist_ok=True)
        self.project.write(".coast/xcode-scheme", "App\n")
        self.project.commit("xcode layout")
        self.project.adopt()
        stub_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, stub_dir, True)
        record = os.path.join(stub_dir, "calls.txt")
        stub = os.path.join(stub_dir, "xcodebuild")
        with open(stub, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\necho \"$@\" >> " + json.dumps(record) + "\nexit 0\n")
        os.chmod(stub, 0o755)
        env = clean_env(PATH=stub_dir + os.pathsep + os.environ.get("PATH", ""))
        code, out = self.project.hook("pre-push", "--seat", "build", env=env)
        self.assertEqual(code, 0, out)
        with open(record, encoding="utf-8") as handle:
            calls = handle.read()
        self.assertIn("build", calls)
        self.assertIn("-scheme App", calls)
        self.assertIn("SWIFT_TREAT_WARNINGS_AS_ERRORS=YES", calls)
        self.assertNotIn("swift build", out)

    def test_dry_run_writes_nothing(self):
        before = self.project.snapshot()
        code, out = self.project.adopt("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("would write", out)
        self.assertEqual(self.project.snapshot(), before)

    def test_founder_text_outside_the_claude_block_survives(self):
        self.project.write("CLAUDE.md", "# My app\n\nMy own notes stay.\n")
        self.project.adopt()
        text = self.project.read("CLAUDE.md")
        self.assertIn("My own notes stay.", text)
        self.assertEqual(text.count("up-coast-standards: begin"), 1)
        self.project.adopt()
        self.assertEqual(self.project.read("CLAUDE.md"), text)

    def test_founder_edited_seed_survives_a_re_adopt(self):
        """A shipped lint seed the founder edited is kept; one still equal to the old shipped seed takes the new one."""
        with tempfile.TemporaryDirectory() as fake_standards:
            lint = os.path.join(fake_standards, "enforcement", "lint")
            os.makedirs(lint)
            shutil.copytree(os.path.join(REPO_ROOT, "rules"), os.path.join(fake_standards, "rules"))
            with open(os.path.join(lint, "swiftlint.yml"), "w") as handle:
                handle.write("opt_in_rules:\n  - force_unwrapping\n")
            with open(os.path.join(lint, "swift-format.json"), "w") as handle:
                handle.write('{"version": 1}\n')
            original_root = adopt.STANDARDS_ROOT
            adopt.STANDARDS_ROOT = fake_standards
            try:
                code, out = self.project.adopt()
                self.assertEqual(code, 0, out)
                self.assertIn("wrote                  .swiftlint.yml", out)
                self.assertEqual(self.project.read(".swiftlint.yml"), "opt_in_rules:\n  - force_unwrapping\n")
                # The founder edits one seed; the other stays as shipped. Then the shipped seeds change.
                self.project.write(".swiftlint.yml", "opt_in_rules:\n  - force_unwrapping\n  - my_own_rule\n")
                with open(os.path.join(lint, "swiftlint.yml"), "w") as handle:
                    handle.write("opt_in_rules:\n  - force_unwrapping\n  - force_try\n")
                with open(os.path.join(lint, "swift-format.json"), "w") as handle:
                    handle.write('{"version": 2}\n')
                code, out = self.project.adopt()
                self.assertEqual(code, 0, out)
                self.assertIn("kept (founder-edited)  .swiftlint.yml", out)
                self.assertEqual(self.project.read(".swiftlint.yml"), "opt_in_rules:\n  - force_unwrapping\n  - my_own_rule\n")
                self.assertIn("replaced               .swift-format", out)
                self.assertEqual(self.project.read(".swift-format"), '{"version": 2}\n')
                # The rules document is a seed that is never replaced, edited or not.
                self.project.write("docs/domain-rules.md", "# mine\n")
                self.project.adopt()
                self.assertEqual(self.project.read("docs/domain-rules.md"), "# mine\n")
            finally:
                adopt.STANDARDS_ROOT = original_root

    def test_first_adoption_secret_scan_reports_a_planted_secret(self):
        self.project.write("Sources/App/Keys.swift", 'let apiKey = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"\n')
        self.project.commit("plant")
        code, out = self.project.adopt()
        self.assertEqual(code, 1, out)
        self.assertIn("secret-literal", out)
        self.assertIn("Sources/App/Keys.swift", out)


class HookTests(unittest.TestCase):
    """One adopted project for the class (an adoption is seconds of scanning); each test leaves the tree as it found it."""

    @classmethod
    def setUpClass(cls):
        cls.project = Project()
        code, out = cls.project.adopt()
        if code != 0:
            raise AssertionError(out)

    @classmethod
    def tearDownClass(cls):
        cls.project.cleanup()

    def tearDown(self):
        sh(self.project.path, "git", "reset", "-q", "--hard")
        sh(self.project.path, "git", "clean", "-qfd", "--exclude=.coast", "--exclude=Scripts", "--exclude=.githooks",
           "--exclude=CLAUDE.md", "--exclude=docs")

    def test_pre_commit_refuses_a_staged_ui_string_literal_and_passes_a_clean_file(self):
        self.project.write("Sources/App/Views/HomeView.swift", PLANTED_VIEW)
        sh(self.project.path, "git", "add", "-A")
        code, out = self.project.hook("pre-commit")
        self.assertEqual(code, 1, out)
        self.assertIn("gate: rules-scan (staged)", out)
        self.assertIn(":ui-string-literal:", out)
        self.assertIn("Sources/App/Views/HomeView.swift", out)

        self.project.write("Sources/App/Views/HomeView.swift", CLEAN_VIEW.replace("Copy.title", "Copy.home"))
        sh(self.project.path, "git", "add", "-A")
        code, out = self.project.hook("pre-commit")
        self.assertEqual(code, 0, out)
        self.assertIn("every pre-commit check green", out)
        self.assertFalse(os.path.isdir(os.path.join(self.project.path, "Scripts", "checks", "__pycache__")), "the hook must leave no __pycache__ in the project")

    def commit_msg(self, text, agent=False):
        path = os.path.join(self.project.path, "MSG")
        with open(path, "w") as handle:
            handle.write(text)
        return self.project.hook("commit-msg", path, env=clean_env(CLAUDECODE="1" if agent else None))

    def test_commit_msg_refuses_an_empty_subject(self):
        code, out = self.commit_msg("\n\n# a comment only\n")
        self.assertEqual(code, 1, out)
        self.assertIn(":empty-subject:", out)

    def test_commit_msg_refuses_a_long_subject_and_passes_a_plain_one(self):
        code, out = self.commit_msg("x" * 101 + "\n")
        self.assertEqual(code, 1, out)
        self.assertIn(":subject-length:", out)
        code, out = self.commit_msg("Fix the settings row's missing label\n")
        self.assertEqual(code, 0, out)

    def test_commit_msg_holds_the_attribution_trailer(self):
        code, out = self.commit_msg("Fix the row\n\nCo-Authored-By: Claude Code <noreply@anthropic.com>\n")
        self.assertEqual(code, 1, out)
        self.assertIn(":attribution-trailer:", out)
        code, out = self.commit_msg("Fix the row\n", agent=True)
        self.assertEqual(code, 1, out)
        self.assertIn(":attribution-trailer:", out)
        code, out = self.commit_msg("Fix the row\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>\n", agent=True)
        self.assertEqual(code, 0, out)

    def test_pre_push_jscpd_seat_refuses_a_copied_block(self):
        jscpd = find_jscpd()
        if jscpd is None:
            self.fail("jscpd is not installed; the pre-push seat cannot be proven — npm install -g jscpd@5.1.2, or set JSCPD_BIN")
        env = clean_env(JSCPD_BIN=jscpd)
        # The baseline adopt.py wrote holds no clones; the seat passes on the clean tree.
        code, out = self.project.adopt("--jscpd-bin", jscpd)
        self.assertEqual(code, 0, out)
        baseline = json.loads(self.project.read(".coast/jscpd-baseline.json"))
        self.assertEqual(baseline["clones"], 0)
        self.assertEqual(baseline["deadline"], "2026-12-03")
        code, out = self.project.hook("pre-push", "--seat", "jscpd", env=env)
        self.assertEqual(code, 0, out)
        self.assertIn("gate: jscpd (no new clones)", out)
        # A copied 24-line block is a new clone: refused in the seat's own line.
        self.project.write("Sources/App/Two.swift", "import Foundation\nfunc two(input: Int) -> Int {\n    var total = 0\n" + BLOCK + "    return total\n}\n")
        code, out = self.project.hook("pre-push", "--seat", "jscpd", env=env)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL pre-push", out)
        self.assertIn(":jscpd:", out)
        self.assertIn("the push was refused", out)

    def test_pre_push_rules_scan_seat_runs_the_scanner_on_the_tree(self):
        code, out = self.project.hook("pre-push", "--seat", "rules-scan")
        self.assertEqual(code, 0, out)
        self.assertIn("gate: rules-scan (tree + ratchets)", out)
        self.assertIn("PASS rules", out)

    def test_pre_push_names_every_tool_the_battery_manifest_claims(self):
        with open(os.path.join(CHECKS_DIR, "battery.json")) as handle:
            battery = json.load(handle)
        text = self.project.read(".githooks/pre-push")
        for platform, entry in battery["platforms"].items():
            for tool, spec in entry.get("tools", {}).items():
                self.assertEqual(spec["runner"], "enforcement/hooks/pre-push", (platform, tool))
                self.assertIn(tool, text, f"pre-push never mentions {tool}")


if __name__ == "__main__":
    unittest.main()
