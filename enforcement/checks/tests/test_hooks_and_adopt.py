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
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
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

    def test_a_folder_that_case_folds_to_scripts_is_said_out_loud(self):
        # On a case-folding filesystem Scripts/checks lands inside an existing scripts/ and git
        # records it there, so a Linux clone finds nothing at Scripts/checks. The report says so.
        self.project.write("scripts/deploy.sh", "#!/bin/sh\n")
        self.project.commit("a scripts folder")
        code, out = self.project.adopt("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("already has scripts/", out)
        self.assertIn("a Linux clone will not find them", out)

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
        self.assertIn("Rules enforced by a check", claude_md)
        self.assertIn("coast-standards: end", claude_md)

        code, second = self.project.adopt()
        self.assertEqual(code, 0, second)
        self.assertEqual(self.project.snapshot(), before)
        self.assertIn("0 file(s) changed", second)
        self.assertNotIn("wrote", second.replace("would write", ""))

    def test_adoption_installs_the_claude_session_hooks_and_keeps_other_settings(self):
        self.project.write(".claude/settings.json", json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}, "model": "opus"}))
        code, _ = self.project.adopt()
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.project.path, "Scripts/hooks/claude-hook.py")))
        settings = json.loads(self.project.read(".claude/settings.json"))
        self.assertEqual(settings["permissions"]["allow"], ["Bash(ls:*)"], "the founder's own settings must survive")
        self.assertEqual(settings["model"], "opus")
        self.assertIn("Bash(git push --force*)", settings["permissions"]["deny"])
        self.assertIs(settings["disableAllHooks"], False)
        self.assertIn("PreToolUse", settings["hooks"])
        commands = json.dumps(settings["hooks"])
        for hook_id in ("governing-edit", "chained-cd", "infra-command", "no-verify", "force-push",
                        "scan-at-commit", "scan-on-edit", "unpushed-at-stop", "rules-at-start"):
            self.assertIn(hook_id, commands, f"the settings file must wire {hook_id}")
        self.assertIn("Scripts/hooks/claude-hook.py", commands)

    def test_adoption_merges_the_deny_rules_in_front_of_the_projects_own_and_resets_disable_all_hooks(self):
        # E2.8: the permission layer travels with the hooks. The shipped deny rules are written once each, before
        # the project's own; the project's ask list is untouched; a founder's `disableAllHooks: true` becomes false.
        self.project.write(".claude/settings.json", json.dumps({
            "disableAllHooks": True,
            "permissions": {"deny": ["Bash(rm -rf *)", "Bash(git push --force*)"], "ask": ["Bash(npm publish *)"]}}))
        code, _ = self.project.adopt()
        self.assertEqual(code, 0)
        settings = json.loads(self.project.read(".claude/settings.json"))
        with open(os.path.join(REPO_ROOT, "enforcement", "hooks", "claude-settings.json"), encoding="utf-8") as handle:
            shipped = json.load(handle)["permissions"]["deny"]
        deny = settings["permissions"]["deny"]
        self.assertEqual(deny[:len(shipped)], shipped)
        self.assertEqual(deny[len(shipped):], ["Bash(rm -rf *)"])
        self.assertEqual(settings["permissions"]["ask"], ["Bash(npm publish *)"])
        self.assertIs(settings["disableAllHooks"], False)
        before = self.project.snapshot()
        code, _ = self.project.adopt()
        self.assertEqual(code, 0)
        self.assertEqual(self.project.snapshot(), before, "a second run changes nothing")

    def test_session_start_reads_the_number_adopt_wrote_into_claude_md(self):
        # The verifier is not installed into a project (it reads the standards repo), so the
        # session-start hook used to say "unknown" in every adopted repository. adopt.py writes
        # the number into the CLAUDE.md block; the hook reads it from there.
        code, _ = self.project.adopt()
        self.assertEqual(code, 0)
        block = self.project.read("CLAUDE.md")
        self.assertRegex(block, r"Rules enforced by a check: \d+ of \d+")
        event = json.dumps({"session_id": "t", "cwd": self.project.path, "hook_event_name": "SessionStart", "source": "startup"})
        done = subprocess.run([sys.executable, os.path.join(self.project.path, "Scripts/hooks/claude-hook.py"), "rules-at-start"],
                              input=event, cwd=self.project.path, capture_output=True, text=True, env=clean_env())
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertRegex(done.stdout, r"rules enforced by a check: \d+ of \d+ in docs/domain-rules.md \(partly \d+")
        self.assertNotIn("unknown", done.stdout)

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
            handle.write("#!/bin/sh\necho \"$@\" >> " + json.dumps(record) + "\n"
                         "if [ \"$1\" = -list ]; then echo '{\"project\": {\"targets\": [\"App\"]}}'; fi\nexit 0\n")
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
        # No test target at all: measured as tests-missing 1, held with the deadline, and the
        # seat judges that instead of running a test action the project does not have.
        code, out = self.project.hook("pre-push", "--measure", "tests", env=env)
        self.assertEqual(code, 0, out)
        self.assertIn("MEASURE tests-missing 1", out)
        with unittest.mock.patch.dict(os.environ, {"PATH": env["PATH"]}):
            code, out = self.project.adopt("--measure-tools")
        self.assertEqual(code, 0, out)
        self.assertEqual(self._baseline_entries()["tests-missing"]["count"], 1)
        os.remove(record)
        code, out = self.project.hook("pre-push", "--seat", "tests", env=env)
        self.assertEqual(code, 0, out)
        self.assertIn("OK ratchet tests-missing: 1 reported, equal to the baseline", out)
        with open(record, encoding="utf-8") as handle:
            self.assertNotIn(" test ", " " + handle.read().replace("-list -json", "") + " ", "no test action ran")

    def test_adoption_binds_an_existing_theme_file_so_it_is_not_a_second_theme(self):
        self.project.write("Sources/App/DesignSystem/Theme.swift", "import SwiftUI\nenum Theme { static let accent = Color.accentColor }\n")
        self.project.commit("a theme")
        code, out = self.project.adopt()
        self.assertEqual(code, 0, out)
        bindings = json.loads(self.project.read(".coast/paths.json"))
        self.assertEqual(bindings["platforms"]["ios"]["classes"]["theme"], ["Sources/App/DesignSystem/Theme.swift"])
        self.assertEqual(bindings["platforms"]["ios"]["classes"]["ui_lib"], ["Sources/App/DesignSystem/**"])
        code, out = self.project.hook("pre-push", "--seat", "rules-scan")
        self.assertNotIn("second-theme-file", out)
        # bound once: a re-adopt leaves the founder's file alone
        self.project.write(".coast/paths.json", json.dumps({"platforms": {"ios": {"classes": {"theme": ["Elsewhere.swift"]}}}}))
        self.project.adopt()
        self.assertIn("Elsewhere.swift", self.project.read(".coast/paths.json"))

    def _stub_tools(self):
        """A `swift` and a `swift-format` on PATH that print STUB_WARNINGS / STUB_FINDINGS distinct
        finding lines and record their arguments; returns (env overrides, the calls file)."""
        stub_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, stub_dir, True)
        record = os.path.join(stub_dir, "calls.txt")
        for name, var, kind in (("swift", "STUB_WARNINGS", "warning: stubbed warning"),
                                ("swift-format", "STUB_FINDINGS", "warning: [Indentation] stubbed finding"),
                                ("swiftlint", "STUB_LINT", "error: Identifier Name Violation: stubbed")):
            with open(os.path.join(stub_dir, name), "w", encoding="utf-8") as handle:
                handle.write("#!/bin/sh\necho \"" + name + " $@\" >> " + json.dumps(record) + "\n"
                             "if [ \"$1\" = package ]; then echo '{\"targets\": [{\"name\": \"AppTests\", \"type\": \"test\"}]}'; exit 0; fi\n"
                             "i=0\nwhile [ $i -lt ${" + var + ":-0} ]; do\n"
                             "  echo \"Sources/App/One.swift:$((i+1)):5: " + kind + " $i\"\n  i=$((i+1))\ndone\nexit 0\n")
            os.chmod(os.path.join(stub_dir, name), 0o755)
        return {"PATH": stub_dir + os.pathsep + os.environ.get("PATH", "")}, record

    def _baseline_entries(self):
        return {e["id"]: e for e in json.loads(self.project.read(".coast/ratchet-baseline.json"))["baselines"]}

    def test_pre_push_build_seat_is_strict_without_a_baseline_and_a_ratchet_under_one(self):
        overrides, record = self._stub_tools()
        self.project.adopt()
        # No build-warnings entry: the build runs with warnings as errors.
        code, out = self.project.hook("pre-push", "--seat", "build", env=clean_env(STUB_WARNINGS="1", **overrides))
        self.assertEqual(code, 0, out)
        self.assertIn("gate: build (warnings-as-errors)", out)
        with open(record, encoding="utf-8") as handle:
            self.assertIn("-warnings-as-errors", handle.read())
        # Under an entry of 2 the same build is a ratchet: 2 passes, 3 refuses in the ratchet's own line.
        baseline = json.loads(self.project.read(".coast/ratchet-baseline.json"))
        baseline["baselines"].append({"id": "build-warnings", "count": 2, "deadline": "2026-12-03",
                                      "written": "2026-09-04", "by": "Tester", "moves": []})
        self.project.write(".coast/ratchet-baseline.json", json.dumps(baseline))
        os.remove(record)
        code, out = self.project.hook("pre-push", "--seat", "build", env=clean_env(STUB_WARNINGS="2", **overrides))
        self.assertEqual(code, 0, out)
        self.assertIn("gate: build (warnings ratchet", out)
        self.assertIn("OK ratchet build-warnings: 2 reported, equal to the baseline", out)
        with open(record, encoding="utf-8") as handle:
            self.assertIn("swift package describe", handle.read(), "a ratcheted build recompiles the package's own targets")
        with open(record, encoding="utf-8") as handle:
            self.assertNotIn("-warnings-as-errors", handle.read())
        code, out = self.project.hook("pre-push", "--seat", "build", env=clean_env(STUB_WARNINGS="3", **overrides))
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL ratchet .coast/ratchet-baseline.json:0:build-warnings:", out)
        self.assertIn("[C-4]", out)
        self.assertIn("the push was refused", out)
        # A FALL passes: a build prints warnings only for what it recompiles, so a smaller
        # number is an improvement or a warm build — never a reason to refuse a push.
        code, out = self.project.hook("pre-push", "--seat", "build", env=clean_env(STUB_WARNINGS="0", **overrides))
        self.assertEqual(code, 0, out)
        self.assertIn("below the baseline of 2", out)
        self.assertIn("lower the baseline", out)

    def test_adopt_measure_tools_writes_the_tool_baselines_from_what_the_tools_report(self):
        overrides, _ = self._stub_tools()
        with unittest.mock.patch.dict(os.environ, dict(overrides, STUB_WARNINGS="2", STUB_FINDINGS="3", STUB_LINT="4")):
            code, out = self.project.adopt("--measure-tools")
        self.assertEqual(code, 0, out)
        entries = self._baseline_entries()
        self.assertEqual((entries["build-warnings"]["count"], entries["build-warnings"]["deadline"]), (2, "2026-12-03"))
        self.assertEqual(entries["format-findings"]["count"], 3)
        self.assertEqual(entries["lint-findings"]["count"], 4)
        self.assertIn("build-warnings measured 2", out)
        # Under its entry the lint seat counts instead of running strict; one more finding refuses.
        code, out = self.project.hook("pre-push", "--seat", "lint", env=clean_env(STUB_LINT="4", **overrides))
        self.assertEqual(code, 0, out)
        self.assertIn("gate: lint (findings ratchet)", out)
        code, out = self.project.hook("pre-push", "--seat", "lint", env=clean_env(STUB_LINT="5", **overrides))
        self.assertEqual(code, 1, out)
        self.assertIn(":lint-findings:", out)
        # A re-measure that fell lowers the count; one that rose is not raised.
        with unittest.mock.patch.dict(os.environ, dict(overrides, STUB_WARNINGS="0", STUB_FINDINGS="5", STUB_LINT="4")):
            code, out = self.project.adopt("--measure-tools")
        self.assertEqual(code, 0, out)
        entries = self._baseline_entries()
        self.assertEqual(entries["build-warnings"]["count"], 0)
        self.assertEqual(entries["format-findings"]["count"], 3)
        self.assertIn("format-findings is 5 in the tree, above its baseline of 3", out)
        # A clean project writes no tool entry at all: its seats stay strict.
        fresh = Project()
        self.addCleanup(fresh.cleanup)
        with unittest.mock.patch.dict(os.environ, dict(overrides, STUB_WARNINGS="0", STUB_FINDINGS="0", STUB_LINT="0")):
            code, out = fresh.adopt("--measure-tools")
        self.assertEqual(code, 0, out)
        ids = {e["id"] for e in json.loads(fresh.read(".coast/ratchet-baseline.json"))["baselines"]}
        self.assertNotIn("build-warnings", ids)
        self.assertNotIn("format-findings", ids)
        self.assertIn("the seat stays strict", out)

    def test_pre_commit_holds_doc_comments_on_added_lines_only(self):
        self.project.adopt()
        self.project.write("Sources/App/Api.swift", "import Foundation\npublic struct Api {\n    public func go() {}\n}\n")
        sh(self.project.path, "git", "add", "-A")
        code, out = self.project.hook("pre-commit")
        self.assertEqual(code, 1, out)
        self.assertIn(":doc-comments:", out)
        self.assertIn("[DOC-1]", out)
        self.assertNotIn("doc-comments (staged)", out, "the whole-file seat is gone; the staged scan holds added lines")

    def test_a_project_with_its_own_hooks_keeps_them(self):
        # one adopting web project had scripts/git-hooks/pre-push running gitleaks; adopting pointed
        # core.hooksPath at .githooks and switched it off without a word.
        self.project.write("scripts/git-hooks/pre-push", "#!/bin/sh\necho 'the project own pre-push ran'\nexit 0\n")
        self.project.write("scripts/git-hooks/pre-commit", "#!/bin/sh\necho 'the project own pre-commit ran'\nexit 0\n")
        os.chmod(os.path.join(self.project.path, "scripts/git-hooks/pre-push"), 0o755)
        os.chmod(os.path.join(self.project.path, "scripts/git-hooks/pre-commit"), 0o755)
        self.project.write("package.json", json.dumps({"scripts": {"prepare": "git config core.hooksPath scripts/git-hooks"}}))
        self.project.commit("its own hooks")
        sh(self.project.path, "git", "config", "core.hooksPath", "scripts/git-hooks")
        code, out = self.project.adopt()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.project.read(".coast/previous-hooks-path").strip(), "scripts/git-hooks")
        self.assertIn("they are kept and run after ours", out)
        self.assertIn('its "prepare" script sets core.hooksPath back', out, "the script that would undo this is named")
        code, out = self.project.hook("pre-commit")
        self.assertEqual(code, 0, out)
        self.assertIn("the project own pre-commit ran", out)
        code, out = self.project.hook("pre-push", "--seat", "rules-scan")
        self.assertNotIn("the project own pre-push ran", out, "a named seat is not a whole push")

    def test_a_founder_can_excuse_one_seat_with_a_date_and_an_agent_cannot(self):
        # A wrong check would otherwise block every push: the rules forbid --no-verify, so an
        # agent that finds a false positive can only stop. The door is dated and recorded.
        self.project.adopt()
        today = _dt.date.today()
        def exceptions(entry):
            self.project.write(".coast/rules-exceptions.json", json.dumps({"exceptions": [entry]}))
        exceptions({"seat": "rules-scan", "reason": "the check misreads our path alias",
                    "who": "Pat Lee", "when": str(today), "until": str(today + _dt.timedelta(days=14))})
        code, out = self.project.hook("pre-push", "--seat", "rules-scan")
        self.assertEqual(code, 0, out)
        self.assertIn("rules-scan SKIPPED", out)
        self.assertIn("excused by Pat Lee", out)
        self.assertIn("the check misreads our path alias", out)
        # Expired: the seat runs again and says so.
        exceptions({"seat": "rules-scan", "reason": "stale", "who": "Pat Lee",
                    "when": "2026-01-01", "until": str(today - _dt.timedelta(days=1))})
        code, out = self.project.hook("pre-push", "--seat", "rules-scan")
        self.assertIn("the exception expired", out)
        self.assertIn("gate: rules-scan (tree + ratchets)", out)
        # No date at all is not a door.
        exceptions({"seat": "rules-scan", "reason": "forever please", "who": "an agent"})
        code, out = self.project.hook("pre-push", "--seat", "rules-scan")
        self.assertIn("names no 'until' date", out)
        self.assertIn("gate: rules-scan (tree + ratchets)", out)
        # The file is GOVERNING, so the session hook refuses an agent editing it.
        os.remove(os.path.join(self.project.path, ".coast/rules-exceptions.json"))

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
        self.assertEqual(text.count("coast-standards: begin"), 1)
        self.project.adopt()
        self.assertEqual(self.project.read("CLAUDE.md"), text)

    def test_a_block_under_the_old_markers_is_replaced_not_doubled(self):
        self.project.write("CLAUDE.md", "# My app\n\nMy own notes stay.\n\n"
                           "<!-- up-coast-standards: begin (old) -->\nold block\n<!-- up-coast-standards: end -->\n")
        self.project.adopt()
        text = self.project.read("CLAUDE.md")
        self.assertIn("My own notes stay.", text)
        self.assertNotIn("old block", text)
        self.assertNotIn("up-coast-standards", text)
        self.assertEqual(text.count("<!-- coast-standards: begin"), 1)
        self.assertEqual(text.count("<!-- coast-standards: end -->"), 1)

    def test_claude_md_markers_in_a_wrong_arrangement_refuse_before_anything_is_written(self):
        # The old rewrite appended a block on every run when the end marker came first, and after
        # an orphaned begin the next run deleted the founder's text up to the appended block.
        # Any arrangement but one begin followed by one end (or none) is refused, and nothing is written.
        wrong = {
            "end before begin": "# My app\n\n<!-- coast-standards: end -->\nMy notes.\n<!-- coast-standards: begin (x) -->\n",
            "orphaned begin": "# My app\n\n<!-- coast-standards: begin (x) -->\nMy notes after it.\n",
            "two blocks": "# My app\n\n<!-- up-coast-standards: begin (old) -->\nold\n<!-- up-coast-standards: end -->\n"
                          "<!-- coast-standards: begin (x) -->\nnew\n<!-- coast-standards: end -->\n",
        }
        for name, text in wrong.items():
            with self.subTest(name):
                self.project.write("CLAUDE.md", text)
                before = self.project.snapshot()
                with self.assertRaises(SystemExit) as caught:
                    self.project.adopt()
                self.assertIn("CLAUDE.md", str(caught.exception))
                self.assertIn("nothing was written", str(caught.exception))
                self.assertEqual(self.project.snapshot(), before, name)
        # A stray comment elsewhere is not a marker; the one true pair is found and replaced in place.
        self.project.write("CLAUDE.md", "# My app\n\nBefore.\n<!-- coast-standards: begin (x) -->\nstale\n<!-- coast-standards: end -->\nAfter.\n")
        code, out = self.project.adopt()
        self.assertEqual(code, 0, out)
        text = self.project.read("CLAUDE.md")
        self.assertNotIn("stale", text)
        self.assertLess(text.index("Before."), text.index("<!-- coast-standards: begin"))
        self.assertLess(text.index("<!-- coast-standards: end -->"), text.index("After."))

    def test_hooks_in_gits_own_hooks_dir_are_kept_and_an_executable_one_runs_as_itself(self):
        # pre-commit-framework, lefthook and the old husky install into .git/hooks with no
        # core.hooksPath; pointing it at .githooks switched them off. And a hook whose shebang
        # says python breaks when forced through sh — an executable one runs as itself.
        hooks = sh(self.project.path, "git", "rev-parse", "--git-path", "hooks")
        self.project.write(os.path.join(hooks, "pre-commit"),
                           "#!/usr/bin/env python3\nprint('the python pre-commit ran'); raise SystemExit(0)\n")
        os.chmod(os.path.join(self.project.path, hooks, "pre-commit"), 0o755)
        self.project.write(os.path.join(hooks, "commit-msg"), "#!/bin/sh\necho 'the plain commit-msg ran'\nexit 0\n")  # not executable: sh runs it
        code, out = self.project.adopt()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.project.read(".coast/previous-hooks-path").strip(), hooks)
        self.assertIn("they are kept and run after ours", out)
        code, out = self.project.hook("pre-commit")
        self.assertEqual(code, 0, out)
        self.assertIn("the python pre-commit ran", out)
        message = os.path.join(self.project.path, "MSG")
        with open(message, "w") as handle:
            handle.write("Fix the row\n")
        code, out = self.project.hook("commit-msg", message)
        self.assertEqual(code, 0, out)
        self.assertIn("the plain commit-msg ran", out)

    def test_a_governed_file_the_new_release_no_longer_ships_is_removed(self):
        # A module renamed upstream left its old file in Scripts/checks for ever. The manifest
        # says what was installed; what this release does not ship is removed. A file the
        # founder put there is not the installer's and stays.
        with tempfile.TemporaryDirectory() as older:
            shipped = os.path.join(older, "checks")
            shutil.copytree(CHECKS_DIR, shipped, ignore=shutil.ignore_patterns("__pycache__", "tests"))
            with open(os.path.join(shipped, "old_module.py"), "w") as handle:
                handle.write("# renamed upstream after this release\n")
            with unittest.mock.patch.object(adopt, "CHECKS_DIR", shipped):
                code, out = self.project.adopt()
            self.assertEqual(code, 0, out)
        self.assertTrue(os.path.isfile(os.path.join(self.project.path, "Scripts/checks/old_module.py")))
        manifest = json.loads(self.project.read(".coast/installed.json"))
        self.assertIn("Scripts/checks/old_module.py", manifest["files"])
        self.assertIn(".githooks/pre-push", manifest["files"])
        self.project.write("Scripts/checks/mine.py", "# the founder's own\n")
        code, out = self.project.adopt("--dry-run")
        self.assertIn("would remove", out)
        self.assertTrue(os.path.isfile(os.path.join(self.project.path, "Scripts/checks/old_module.py")))
        code, out = self.project.adopt()
        self.assertEqual(code, 0, out)
        self.assertIn("removed", out)
        self.assertIn("Scripts/checks/old_module.py", out)
        self.assertFalse(os.path.isfile(os.path.join(self.project.path, "Scripts/checks/old_module.py")))
        self.assertTrue(os.path.isfile(os.path.join(self.project.path, "Scripts/checks/mine.py")))
        self.assertNotIn("Scripts/checks/old_module.py", json.loads(self.project.read(".coast/installed.json"))["files"])

    def test_detect_platform_reads_the_pbxproj_of_an_xcodeproj_only_project(self):
        # Every one of the owner's apps is an .xcodeproj with no Package.swift; detection returned None for all of them.
        def pbxproj(*settings):
            folder = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, folder, True)
            os.makedirs(os.path.join(folder, "App.xcodeproj"))
            with open(os.path.join(folder, "App.xcodeproj", "project.pbxproj"), "w") as handle:
                handle.write("// !$*UTF8*$!\n{\n\tbuildSettings = {\n" + "".join(f"\t\t{line};\n" for line in settings) + "\t};\n}\n")
            return folder
        self.assertEqual(adopt.detect_platform(pbxproj("SDKROOT = iphoneos", "SWIFT_VERSION = 5.0")), "ios")
        self.assertEqual(adopt.detect_platform(pbxproj("SDKROOT = macosx")), "macos")
        self.assertEqual(adopt.detect_platform(pbxproj('SUPPORTED_PLATFORMS = "iphoneos iphonesimulator"', "SDKROOT = auto")), "ios")
        self.assertIsNone(adopt.detect_platform(pbxproj('SUPPORTED_PLATFORMS = "iphoneos iphonesimulator macosx"')), "both platforms: ask")
        self.assertIsNone(adopt.detect_platform(pbxproj("SWIFT_VERSION = 5.0")), "no SDK named: ask")

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
        # Unstage first: a test's `git add -A` stages the (untracked) adoption files, and a
        # `reset --hard` would delete them with the staging — found on CI, where no jscpd
        # meant no re-adoption to put them back.
        sh(self.project.path, "git", "reset", "-q")
        sh(self.project.path, "git", "checkout", "-q", "--", ".")
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

    def test_commit_msg_counts_characters_not_bytes(self):
        # wc -m counts bytes under a C locale: a 98-character subject with two em dashes read as 102.
        subject = "A wrong check is a founder's call — not a dead end — one seat excused, dated, recorded"
        self.assertLessEqual(len(subject), 100)
        path = os.path.join(self.project.path, "MSG")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(subject + "\n")
        code, out = self.project.hook("commit-msg", path, env=clean_env(LC_ALL="C", LANG="C"))
        self.assertEqual(code, 0, out)

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

    def test_commit_msg_keeps_an_issue_number_subject_and_accepts_gits_own_messages(self):
        # `#123 …` is a subject naming an issue, not a git comment (those are `#` alone or `# …`).
        code, out = self.commit_msg("#123 fix the crash on launch\n")
        self.assertEqual(code, 0, out)
        code, out = self.commit_msg("# On branch main\n#\n# Changes to be committed:\n")
        self.assertEqual(code, 1, out)
        self.assertIn(":empty-subject:", out)
        # git's own merge and revert messages carry no trailer and may run long; they are git's words.
        long_branch = "feature/" + "x" * 90
        for text in (f"Merge branch '{long_branch}'\n",
                     "Merge remote-tracking branch 'origin/main' into feature\n",
                     "Merge pull request #12 from someone/feature\n",
                     'Revert "Add the row"\n\nThis reverts commit 4b19181c1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c1c.\n'):
            code, out = self.commit_msg(text, agent=True)
            self.assertEqual(code, 0, text + out)
        # A hand-written message that only starts like one is not git's.
        code, out = self.commit_msg('Revert "Add the row"\n\nbecause it broke the build\n', agent=True)
        self.assertEqual(code, 1, out)
        self.assertIn(":attribution-trailer:", out)

    def test_pre_push_scans_the_pushed_sha_from_stdin_not_head(self):
        # `git push origin feature` from main: the ref line names feature's sha, and that is what
        # is scanned — HEAD (main) is clean here, feature carries the literal.
        start = sh(self.project.path, "git", "rev-parse", "HEAD")
        self.addCleanup(sh, self.project.path, "git", "reset", "-q", start)   # the adoption files go back to untracked
        sh(self.project.path, "git", "remote", "add", "origin", self.project.path)
        sh(self.project.path, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
        sh(self.project.path, "git", "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        sh(self.project.path, "git", "branch", "-q", "--set-upstream-to=origin/main")
        self.addCleanup(sh, self.project.path, "git", "remote", "remove", "origin")
        self.addCleanup(sh, self.project.path, "git", "branch", "-q", "-D", "feature")
        self.project.commit("adopt")
        sh(self.project.path, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
        base = sh(self.project.path, "git", "rev-parse", "HEAD")
        sh(self.project.path, "git", "checkout", "-q", "-b", "feature")
        self.project.write("Sources/App/Views/FeatureView.swift", PLANTED_VIEW.replace("HomeView", "FeatureView"))
        self.project.commit("on the branch")
        tip = sh(self.project.path, "git", "rev-parse", "HEAD")
        sh(self.project.path, "git", "checkout", "-q", "main")
        zero = "0" * 40
        # Pushing feature (a ref the remote has never seen) refuses, though HEAD is main and clean.
        code, out = self.project.hook("pre-push", "--seat", "rules-scan", stdin=f"refs/heads/feature {tip} refs/heads/feature {zero}\n")
        self.assertEqual(code, 1, out)
        self.assertIn("FeatureView.swift", out)
        self.assertIn(f"on {tip[:7]}", out)
        # Pushing main passes: nothing new on it.
        code, out = self.project.hook("pre-push", "--seat", "rules-scan", stdin=f"refs/heads/main {base} refs/heads/main {base}\n")
        self.assertEqual(code, 0, out)
        self.assertNotIn("FeatureView.swift", out)

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
        # A repeated block in a plan or a note is not duplicated code: not a clone.
        self.project.write("docs/plan.md", "## Steps\n" + "\n".join(f"- step {i}: compute the value, add it to the total, log it" for i in range(20)) + "\n")
        self.project.write("docs/notes.md", "## Steps again\n" + "\n".join(f"- step {i}: compute the value, add it to the total, log it" for i in range(20)) + "\n")
        code, out = self.project.hook("pre-push", "--seat", "jscpd", env=env)
        self.assertEqual(code, 0, out)
        # A copied 24-line block is a new clone: refused in the seat's own line.
        self.project.write("Sources/App/Two.swift", "import Foundation\nfunc two(input: Int) -> Int {\n    var total = 0\n" + BLOCK + "    return total\n}\n")
        code, out = self.project.hook("pre-push", "--seat", "jscpd", env=env)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL pre-push", out)
        self.assertIn(":jscpd:", out)
        self.assertIn("the push was refused", out)

    def test_the_first_push_after_adoption_holds_only_lines_from_the_adoption_on(self):
        # A literal committed BEFORE the adoption is legacy; one committed after is refused.
        # The "remote" is a ref at the pre-adoption commit (a real push would meet the installed hook).
        sh(self.project.path, "git", "remote", "add", "origin", self.project.path)
        sh(self.project.path, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
        sh(self.project.path, "git", "branch", "-q", "--set-upstream-to=origin/main")
        self.addCleanup(sh, self.project.path, "git", "remote", "remove", "origin")
        # The literal is committed alone, before the adoption files (still untracked here) are.
        self.project.write("Sources/App/Views/OldView.swift", PLANTED_VIEW.replace("HomeView", "OldView"))
        sh(self.project.path, "git", "add", "Sources/App/Views/OldView.swift")
        sh(self.project.path, "git", "-c", "core.hooksPath=.git/hooks", "commit", "-q", "-m", "before the checks existed")
        self.project.commit("adopt")
        code, out = self.project.hook("pre-push", "--seat", "rules-scan")
        self.assertEqual(code, 0, out)
        self.project.write("Sources/App/Views/NewView.swift", PLANTED_VIEW.replace("HomeView", "NewView"))
        self.project.commit("after")
        code, out = self.project.hook("pre-push", "--seat", "rules-scan")
        self.assertEqual(code, 1, out)
        self.assertIn("NewView.swift", out)
        self.assertNotIn("OldView.swift", out)

    def test_two_pushes_in_one_checkout_are_serialised_and_a_stale_lock_is_broken(self):
        # A held lock makes the second push wait rather than build alongside the first.
        lock = os.path.join(self.project.path, ".git", "coast-push.lock")
        os.makedirs(lock, exist_ok=True)   # a live lock: just made (its age is the directory's own mtime)
        waiting = subprocess.Popen(["sh", os.path.join(self.project.path, ".githooks", "pre-push"), "origin", "x"],
                                   cwd=self.project.path, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=clean_env())
        time.sleep(3)
        self.assertIsNone(waiting.poll(), "the second push must wait for the lock, not run alongside the first")
        waiting.kill()
        self.assertIn("another push is running in this checkout", waiting.communicate()[0])
        shutil.rmtree(lock, ignore_errors=True)
        # A lock left behind by a dead push is broken, not waited on for ever.
        os.makedirs(lock, exist_ok=True)
        two_hours_ago = time.time() - 7200
        os.utime(lock, (two_hours_ago, two_hours_ago))
        stale = subprocess.Popen(["sh", os.path.join(self.project.path, ".githooks", "pre-push"), "origin", "x"],
                                 cwd=self.project.path, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=clean_env())
        time.sleep(3)
        stale.kill()
        self.assertIn("breaking a push lock left behind", stale.communicate()[0])
        shutil.rmtree(lock, ignore_errors=True)

    def test_a_tsconfig_with_comments_and_a_path_star_is_read_correctly(self):
        # one adopting web project maps "@/*" to ["./src/*"]. A comment stripper that does not know
        # what a string is reads the /* inside that path as a comment, eats the rest of the
        # file, and the gate refuses the push claiming strict is not set when it is.
        import importlib.util
        spec = importlib.util.spec_from_file_location("jsonc", os.path.join(CHECKS_DIR, "jsonc.py"))
        jsonc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(jsonc)
        text = """{
          // the compiler
          "compilerOptions": {
            "strict": true,   /* every check on */
            "paths": { "@/*": ["./src/*"], "~/*": ["./lib/*"] },
          },
          "include": ["next-env.d.ts"],
        }"""
        data = json.loads(jsonc.strip(text))
        self.assertIs(data["compilerOptions"]["strict"], True)
        self.assertEqual(data["compilerOptions"]["paths"]["@/*"], ["./src/*"], "the path survived the comment stripper")
        self.assertEqual(data["include"], ["next-env.d.ts"], "the trailing commas were dropped")
        # A string containing a comment opener is left alone.
        kept = json.loads(jsonc.strip('{"url": "https://example.com/a", "glob": "src/**/*.ts"}'))
        self.assertEqual(kept["url"], "https://example.com/a")
        self.assertEqual(kept["glob"], "src/**/*.ts")

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


def release_tarball(path, number):
    """A release tarball of the working tree (what GitHub serves for a tag), named and prefixed as GitHub does."""
    import tarfile
    with tarfile.open(path, "w:gz") as tar:
        for name in sorted(os.listdir(REPO_ROOT)):
            if name in (".git", ".pytest_cache"):
                continue
            tar.add(os.path.join(REPO_ROOT, name), arcname=f"coast-standards-{number}/{name}",
                    filter=lambda m: None if "__pycache__" in m.name else m)


class ReleaseTests(unittest.TestCase):
    """The version a project records, and installing from a fetched release with no clone."""

    def test_the_version_is_the_number_in_checks_version_plus_the_commit_when_not_at_a_tag(self):
        with open(os.path.join(REPO_ROOT, "CHECKS-VERSION"), encoding="utf-8") as handle:
            number = handle.read().strip()
        self.assertRegex(number, r"^\d+\.\d+\.\d+$")
        version = adopt.standards_version()
        self.assertTrue(version == number or version.startswith(number + "+"), version)
        tags = sh(REPO_ROOT, "git", "tag", "--points-at", "HEAD").split()
        self.assertEqual(version == number, f"v{number}" in tags)

    def test_release_fetches_a_tarball_into_the_cache_and_installs_from_it(self):
        # A release tarball of this tree, served from a file:// base: what GitHub serves for a tag.
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        with open(os.path.join(REPO_ROOT, "CHECKS-VERSION"), encoding="utf-8") as handle:
            number = handle.read().strip()
        releases = os.path.join(work.name, "releases")
        os.makedirs(releases)
        release_tarball(os.path.join(releases, f"v{number}.tar.gz"), number)
        cache = os.path.join(work.name, "cache")
        project = Project()
        self.addCleanup(project.cleanup)
        env = clean_env(COAST_STANDARDS_RELEASES="file://" + releases + "/", COAST_STANDARDS_CACHE=cache)
        done = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "enforcement", "adopt.py"), project.path,
                               "--release", number, "--platform", "ios", "--by", "Tester", "--today", "2026-09-04"],
                              capture_output=True, text=True, env=env)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn(f"installing Coast Standards {number} from {os.path.join(cache, number)}", done.stdout)
        self.assertTrue(os.path.isfile(os.path.join(cache, number, "enforcement", "adopt.py")))
        self.assertEqual(project.read(".coast/standards-version").strip(), number, "a tarball copy is the release itself")
        self.assertTrue(os.path.isfile(os.path.join(project.path, ".githooks", "pre-push")))
        # Fetched once: a second run with the tarball gone still installs from the cache.
        os.remove(os.path.join(releases, f"v{number}.tar.gz"))
        again = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "enforcement", "adopt.py"), project.path,
                                "--release", number, "--today", "2026-09-04"], capture_output=True, text=True, env=env)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)

    def test_a_mislabelled_release_is_refused(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        releases = os.path.join(work.name, "releases")
        os.makedirs(releases)
        release_tarball(os.path.join(releases, "v9.9.9.tar.gz"), "9.9.9")
        project = Project()
        self.addCleanup(project.cleanup)
        env = clean_env(COAST_STANDARDS_RELEASES="file://" + releases + "/", COAST_STANDARDS_CACHE=os.path.join(work.name, "cache"))
        done = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "enforcement", "adopt.py"), project.path,
                               "--release", "9.9.9", "--platform", "ios"], capture_output=True, text=True, env=env)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("release 9.9.9 says it is", done.stderr)
