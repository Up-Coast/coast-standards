"""Tests for check_rules.py (enforcement task E1.1).

A synthetic git repository shaped like a Coast-scaffolded iOS project proves
every mode and every mechanism with zero spend: a hatch on an added line
fails, the same hatch under a plan-approved deviation passes, a governed
exception passes, tests are exempt, a governance-only diff passes, the
ratchet refuses a rise and a fall, advisories never fail, the import
matrix judges a feature-imports-feature package, and every folded
native-pattern signature has a fail plant that hits and a pass plant that
does not.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANTS = os.path.join(CHECKS_DIR, "tests", "plants")
sys.path.insert(0, CHECKS_DIR)

import check_rules as cr  # noqa: E402
import import_matrix as im  # noqa: E402

# A git hook hands its children GIT_DIR and GIT_INDEX_FILE (always, in a linked
# worktree). The throwaway repositories below must never see them, or every
# `git` call here — and the scanner's own, run in-process — lands in the hook's
# repository instead: this file once committed its fixtures onto the branch
# being committed. Dropped once, for the whole test process.
for _name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
              "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX", "GIT_NAMESPACE"):
    os.environ.pop(_name, None)

SCRIM = 'struct StatusPanel { var scrim: some View { Color.black.opacity(0.4) } }\n'
CLEAN = 'struct StatusPanel: View { var body: some View { Text(Copy.title) } }\n'


def sh(cwd, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@x")
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"{args} failed:\n{result.stderr}")
    return result.stdout.strip()


class Repo:
    """A throwaway git repository the scanner runs inside."""

    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = self.dir.name
        sh(self.path, "git", "init", "-q", "-b", "main")
        self.write("Package.swift", "// swift-tools-version:6.0\n")
        self.write("Sources/App/App.swift", "import SwiftUI\n@main struct App {}\n")
        self.commit("start")

    def write(self, relative, content):
        full = os.path.join(self.path, relative)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(content if isinstance(content, str) else json.dumps(content, indent=2))

    def commit(self, message):
        sh(self.path, "git", "add", "-A")
        sh(self.path, "git", "commit", "-q", "-m", message)
        return sh(self.path, "git", "rev-parse", "HEAD")

    def run(self, *argv):
        out = io.StringIO()
        cwd = os.getcwd()
        os.chdir(self.path)
        try:
            with redirect_stdout(out):
                code = cr.main(list(argv))
        except SystemExit as stop:   # a broken baseline file exits early, like the real process
            code = stop.code
        finally:
            os.chdir(cwd)
        return code, out.getvalue()

    def cleanup(self):
        self.dir.cleanup()


def proof(deviations):
    return {"proof_schema_version": 1, "feature_id": "F-1", "plan_approval": [
        {"verdict": "approved", "context": {"approved_native_deviations": deviations}}]}


class GlobAndClassTests(unittest.TestCase):
    def test_glob_semantics_match_coast(self):
        self.assertTrue(cr.glob_matches("docs/**", "docs"))
        self.assertTrue(cr.glob_matches("docs/**", "docs/a/b.md"))
        self.assertTrue(cr.glob_matches("**/*.xcstrings", "Localizable.xcstrings"))
        self.assertTrue(cr.glob_matches("**/*.xcstrings", "Modules/Strings/Localizable.xcstrings"))
        self.assertFalse(cr.glob_matches("*.xcodeproj/**", "ios/App.xcodeproj/project.pbxproj"))
        self.assertTrue(cr.glob_matches("Modules/Shared/Sources/Theme/Theme.swift", "modules/shared/sources/theme/theme.swift"))
        self.assertFalse(cr.glob_matches("src/*.ts", "src/a/b.ts"))

    def test_classification_is_ordered_first_match(self):
        signatures, paths = cr.load_tables("ios")
        self.assertEqual(paths.classify(".github/workflows/gates.yml"), "governing")
        self.assertEqual(paths.classify("docs/domain-rules.md"), "governing")
        self.assertEqual(paths.classify("docs/diagrams/system.md"), "generated")
        self.assertEqual(paths.classify("docs/plan.md"), "docs")
        self.assertEqual(paths.classify("Modules/Shared/Sources/Theme/Theme.swift"), "theme")
        self.assertEqual(paths.classify("Modules/Strings/Localizable.xcstrings"), "strings")
        self.assertEqual(paths.classify("Tests/AppTests/AppTests.swift"), "tests")
        self.assertEqual(paths.classify("Modules/Home/Sources/HomeView.swift"), "ui")
        self.assertEqual(paths.classify("Modules/Home/Sources/HomeModel.swift"), "source")

    def test_unknown_platform_refuses(self):
        with self.assertRaises(SystemExit):
            cr.load_tables("tvos")
        with self.assertRaises(SystemExit):
            cr.load_tables(None)


class DiffModeTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.base = sh(self.repo.path, "git", "rev-parse", "HEAD")

    def test_a_hatch_on_an_added_line_fails_in_the_line_format(self):
        self.repo.write("Sources/App/StatusPanel.swift", "import SwiftUI\n" + SCRIM)
        head = self.repo.commit("hatch")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL native-pattern Sources/App/StatusPanel.swift:2:scrim-modal: ", out)
        self.assertIn("[A-7]", out)
        self.assertTrue(out.strip().splitlines()[-1].startswith('{"result": "fail"'))

    def test_a_clean_change_passes(self):
        self.repo.write("Sources/App/StatusPanel.swift", "import SwiftUI\n" + CLEAN)
        head = self.repo.commit("clean")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 0, out)
        self.assertIn("PASS rules", out)

    def test_a_legacy_hatch_nobody_touched_is_not_this_changes_fault(self):
        self.repo.write("Sources/App/Old.swift", SCRIM)
        base = self.repo.commit("legacy")
        self.repo.write("Sources/App/New.swift", CLEAN)
        head = self.repo.commit("new")
        code, _ = self.repo.run(base, head, "--platform", "ios")
        self.assertEqual(code, 0)

    def test_tests_are_exempt(self):
        self.repo.write("Tests/AppTests/ScrimTests.swift", SCRIM)
        head = self.repo.commit("test")
        code, _ = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 0)

    def test_a_governance_only_diff_passes(self):
        self.repo.write(".github/workflows/gates.yml", "name: gates\n")
        head = self.repo.commit("gates")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 0)
        self.assertIn("governance-only", out)

    def test_a_plan_approved_deviation_covers_the_hatch(self):
        self.repo.write("Sources/App/StatusPanel.swift", SCRIM)
        self.repo.write("plans/F-1/proof.json", proof([{"file": "Sources/App/StatusPanel.swift", "signatures": ["scrim-modal"]}]))
        head = self.repo.commit("approved")
        code, _ = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 0)

    def test_an_approval_for_another_signature_or_file_does_not_cover_it(self):
        self.repo.write("Sources/App/StatusPanel.swift", SCRIM)
        self.repo.write("plans/F-1/proof.json", proof([{"file": "Sources/App/Other.swift", "signatures": ["scrim-modal"]}]))
        head = self.repo.commit("wrong file")
        self.assertEqual(self.repo.run(self.base, head, "--platform", "ios")[0], 1)
        self.repo.write("plans/F-1/proof.json", proof([{"file": "Sources/App/**", "signatures": ["custom-tab-bar"]}]))
        head = self.repo.commit("wrong signature")
        self.assertEqual(self.repo.run(self.base, head, "--platform", "ios")[0], 1)
        self.repo.write("plans/F-1/proof.json", proof([{"file": "Sources/App/**", "signatures": ["scrim-modal"]}]))
        head = self.repo.commit("glob covers")
        self.assertEqual(self.repo.run(self.base, head, "--platform", "ios")[0], 0)

    def test_a_governed_exception_covers_the_hatch(self):
        self.repo.write("Sources/App/StatusPanel.swift", SCRIM)
        self.repo.write(".coast/rules-exceptions.json", {"exceptions": [
            {"id": "scrim-modal", "path": "Sources/App/StatusPanel.swift", "reason": "legacy", "who": "Pat Lee", "when": "2026-09-04"}]})
        head = self.repo.commit("excepted")
        self.assertEqual(self.repo.run(self.base, head, "--platform", "ios")[0], 0)

    def test_a_paired_signature_needs_both_halves(self):
        self.repo.write("Sources/App/Search.swift", 'Image(systemName: "magnifyingglass")\n')
        head = self.repo.commit("icon only")
        self.assertEqual(self.repo.run(self.base, head, "--platform", "ios")[0], 0)
        self.repo.write("Sources/App/Search.swift", 'Image(systemName: "magnifyingglass")\nTextField(Copy.search, text: $q)\n')
        head = self.repo.commit("both")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn(":hand-rolled-search-field:", out)

    def test_a_hatch_split_across_chained_lines_is_still_the_hatch(self):
        self.repo.write("Sources/App/StatusPanel.swift", "Color.black\n    .opacity(0.4)\n")
        head = self.repo.commit("split")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("StatusPanel.swift:1:scrim-modal", out)

    def test_worktree_head_sees_tracked_changes_and_untracked_files(self):
        self.repo.write("Sources/App/Untracked.swift", SCRIM)
        code, out = self.repo.run(self.base, "WORKTREE", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("Untracked.swift:1:scrim-modal", out)
        os.remove(os.path.join(self.repo.path, "Sources/App/Untracked.swift"))
        self.repo.write("Sources/App/App.swift", "import SwiftUI\n@main struct App {}\n" + SCRIM)
        code, out = self.repo.run(self.base, "WORKTREE", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("App.swift:3:scrim-modal", out)

    def test_staged_mode_scans_the_index_only(self):
        self.repo.write("Sources/App/Staged.swift", SCRIM)
        sh(self.repo.path, "git", "add", "Sources/App/Staged.swift")
        self.repo.write("Sources/App/Unstaged.swift", SCRIM)
        code, out = self.repo.run("--staged", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("Staged.swift:1:scrim-modal", out)
        self.assertNotIn("Unstaged.swift", out)

    def test_files_mode_reads_whole_files(self):
        self.repo.write("Sources/App/One.swift", "import SwiftUI\n\n" + SCRIM)
        code, out = self.repo.run("--files", "Sources/App/One.swift", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("One.swift:3:scrim-modal", out)

    def test_exactly_one_mode(self):
        self.assertEqual(self.repo.run("--platform", "ios")[0], 2)
        self.assertEqual(self.repo.run(self.base, "--platform", "ios")[0], 2)
        self.assertEqual(self.repo.run("--tree", "--staged", "--platform", "ios")[0], 2)


class TreeRatchetAndAdvisoryTests(unittest.TestCase):
    """The severities the folded tables don't use yet, proven through a private table."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.original = (cr.SIGNATURES_FILE, cr.PATHS_FILE)
        self.repo.write("tables/rules_signatures.json", {"signatures": [
            {"id": "inline-comment", "rule": "02", "severity": "ratchet", "scope": "added", "applies_to": ["source", "ui"], "excludes": ["tests"],
             "words": "an inline comment", "platforms": {"ios": {"pattern": r"^\s*//(?!/)"}}},
            {"id": "type-size", "rule": "A-3", "severity": "advisory", "scope": "added", "applies_to": ["source", "ui"],
             "words": "a huge type", "platforms": {"ios": {"pattern": r"\bclass\s+Huge\b"}}},
            {"id": "second-theme-file", "rule": "DRY-2", "severity": "block", "scope": "tree", "applies_to": ["source", "ui"],
             "words": "a second theme file", "platforms": {"ios": {"files": ["**/*Theme.swift"], "pattern": r"struct \w*Theme\b"}}},
        ]})
        with open(cr.PATHS_FILE, encoding="utf-8") as handle:
            ios_paths = json.load(handle)["platforms"]["ios"]
        self.repo.write("tables/paths.json", {"platforms": {"ios": ios_paths}})
        cr.SIGNATURES_FILE = os.path.join(self.repo.path, "tables/rules_signatures.json")
        cr.PATHS_FILE = os.path.join(self.repo.path, "tables/paths.json")
        self.addCleanup(self.restore)

    def restore(self):
        cr.SIGNATURES_FILE, cr.PATHS_FILE = self.original

    def baseline(self, count, deadline="2026-12-03"):
        self.repo.write(".coast/ratchet-baseline.json", {"baselines": [
            {"id": "inline-comment", "count": count, "deadline": deadline, "written": "2026-09-04", "by": "adopt.py", "moves": []}]})

    def test_ratchet_equal_passes_rise_and_fall_fail_and_the_deadline_flips_it(self):
        self.repo.write("Sources/App/A.swift", "// one\n// two\nlet a = 1\n")
        self.baseline(2)
        self.repo.commit("two comments")
        code, out = self.repo.run("--tree", "--platform", "ios", "--today", "2026-09-04")
        self.assertEqual(code, 0, out)
        self.assertIn("OK ratchet inline-comment: 2 in the tree, equal to the baseline; deadline 2026-12-03", out)
        self.repo.write("Sources/App/B.swift", "// three\n")
        self.repo.commit("a third")
        code, out = self.repo.run("--tree", "--platform", "ios", "--today", "2026-09-04")
        self.assertEqual(code, 1)
        self.assertIn("FAIL ratchet inline-comment: 3 in the tree, above the baseline of 2", out)
        self.assertIn("FAIL ratchet Sources/App/B.swift:1:inline-comment:", out)
        self.baseline(5)
        self.repo.commit("stale baseline")
        code, out = self.repo.run("--tree", "--platform", "ios", "--today", "2026-09-04")
        self.assertEqual(code, 1)
        self.assertIn("below the baseline of 5 — lower the baseline to 3", out)
        self.baseline(3)
        self.repo.commit("baseline 3")
        code, out = self.repo.run("--tree", "--platform", "ios", "--today", "2026-12-04")
        self.assertEqual(code, 1)
        self.assertIn("the baseline deadline 2026-12-03 has passed — this check is now blocking", out)

    def test_staged_and_files_modes_leave_the_ratchets_to_the_push(self):
        # Two ratchet hits in the tree and no baseline: --tree refuses, but a commit-time or
        # editor-time scan judges only the lines and files it was given.
        self.repo.write("Sources/App/A.swift", "// one\nlet a = 1\n")
        self.repo.write("Sources/App/B.swift", "// two\nlet b = 2\n")
        sh(self.repo.path, "git", "add", "-A")
        code, out = self.repo.run("--tree", "--platform", "ios")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL ratchet inline-comment", out)
        code, out = self.repo.run("--staged", "--platform", "ios")
        self.assertNotIn("ratchet", out)
        code, out = self.repo.run("--files", "Sources/App/A.swift", "--platform", "ios")
        self.assertNotIn("ratchet", out)

    def test_a_ratchet_with_no_baseline_entry_allows_nothing(self):
        self.repo.write("Sources/App/A.swift", "// one\n")
        self.repo.commit("one comment")
        code, out = self.repo.run("--tree", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("above the baseline of 0", out)

    def test_advisory_prints_and_never_fails(self):
        base = sh(self.repo.path, "git", "rev-parse", "HEAD")
        self.repo.write("Sources/App/Huge.swift", "class Huge {}\n")
        head = self.repo.commit("huge")
        code, out = self.repo.run(base, head, "--platform", "ios")
        self.assertEqual(code, 0, out)
        self.assertIn("ADVISORY rules Sources/App/Huge.swift:1:type-size: a huge type [A-3]", out)

    def test_a_tree_scope_block_signature_fails_wherever_it_sits(self):
        self.repo.write("Modules/Shared/Sources/Theme/Theme.swift", "struct Theme {}\n")
        self.repo.write("Modules/Home/Sources/DarkTheme.swift", "struct DarkTheme {}\n")
        self.repo.commit("two themes")
        code, out = self.repo.run("--tree", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL rules Modules/Home/Sources/DarkTheme.swift:1:second-theme-file: a second theme file [DRY-2]", out)
        self.assertNotIn("Theme/Theme.swift", out, "the bound theme file is the one home, not a second file")


class WaveOneThroughTheRunnerTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.base = sh(self.repo.path, "git", "rev-parse", "HEAD")

    def test_a_literal_in_a_view_fails_and_the_same_words_in_a_model_do_not(self):
        self.repo.write("Sources/App/Views/HomeView.swift", 'import SwiftUI\nstruct HomeView: View { var body: some View { Text("Save your changes now") } }\n')
        self.repo.write("Sources/App/Prompts.swift", 'let prompt = "Write a plan for the feature below."\n')
        head = self.repo.commit("copy")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL rules Sources/App/Views/HomeView.swift:2:ui-string-literal: ", out)
        self.assertIn("[L-1]", out)
        self.assertNotIn("Prompts.swift", out)

    def test_only_the_added_lines_of_a_view_count(self):
        self.repo.write("Sources/App/Views/HomeView.swift", 'import SwiftUI\nstruct HomeView: View { var body: some View { Text("Old words nobody touched") } }\n')
        base = self.repo.commit("legacy")
        self.repo.write("Sources/App/Views/HomeView.swift", 'import SwiftUI\nimport Foundation\nstruct HomeView: View { var body: some View { Text("Old words nobody touched") } }\n')
        head = self.repo.commit("import only")
        self.assertEqual(self.repo.run(base, head, "--platform", "ios")[0], 0)

    def test_the_theme_file_may_hold_colours_and_a_project_override_moves_it(self):
        self.repo.write("Modules/Shared/Sources/Theme/Theme.swift", "enum Theme { static let accent = Color(red: 0.2, green: 0.4, blue: 0.9) }\n")
        head = self.repo.commit("theme")
        self.assertEqual(self.repo.run(self.base, head, "--platform", "ios")[0], 0)
        self.repo.write("App/DesignSystem/Theme.swift", "enum Theme { static let accent = Color(red: 0.2, green: 0.4, blue: 0.9) }\n")
        head = self.repo.commit("theme elsewhere")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("styling-literal", out)
        os.remove(os.path.join(self.repo.path, "Modules/Shared/Sources/Theme/Theme.swift"))  # or it is the second theme file
        self.repo.write(".coast/paths.json", {"classes": {"theme": ["App/DesignSystem/Theme.swift"]}})
        head = self.repo.commit("override")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 0, out)

    def test_a_second_theme_file_fails_once_per_file_on_the_tree(self):
        self.repo.write("Modules/Shared/Sources/Theme/Theme.swift", "enum Theme {}\n")
        self.repo.write("Modules/Home/Sources/HomeTheme.swift", "enum HomeTheme {\n  static let a = 1\n  static let b = 2\n}\n")
        self.repo.commit("two")
        code, out = self.repo.run("--tree", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertEqual(sum(1 for line in out.splitlines() if line.startswith("FAIL rules") and ":second-theme-file:" in line), 1)

    def test_a_secret_file_fails_and_its_example_does_not(self):
        self.repo.write(".env", "ANTHROPIC_API_KEY=sk-ant-not-really\n")
        self.repo.write(".env.example", "ANTHROPIC_API_KEY=\n")
        head = self.repo.commit("env")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL secret-literal .env:1:secret-file:", out)
        self.assertNotIn(".env.example", out)

    def test_a_secret_literal_fails_in_any_file_including_tests(self):
        self.repo.write("Tests/AppTests/KeyTests.swift", 'let k = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789"\n')
        head = self.repo.commit("leak")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn(":secret-literal:", out)


class ImportMatrixTests(unittest.TestCase):
    def test_a_feature_importing_a_feature_fails_through_the_runner(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        repo.write("Sources/Home/HomeView.swift", "import Profile\nstruct HomeView {}\n")
        repo.write("Sources/Profile/ProfileView.swift", "struct ProfileView {}\n")
        repo.commit("cross import")
        code, out = repo.run("--tree", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL import-matrix Sources/Home/HomeView.swift:0:import-matrix: Home imports Profile", out)
        self.assertIn("[A-2]", out)


class PushPathCorrectnessTests(unittest.TestCase):
    """E2.10: the six ways the push path misjudged a change, each held by one test."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.base = sh(self.repo.path, "git", "rev-parse", "HEAD")

    def test_a_binary_secret_file_is_caught_by_its_name_in_a_commit_and_in_the_index(self):
        # A .p12 adds no "+" line to any diff; the old content regex never saw it.
        full = os.path.join(self.repo.path, "Certificates/dist.p12")
        os.makedirs(os.path.dirname(full))
        with open(full, "wb") as handle:
            handle.write(b"\x30\x82\x0b\x00\x02\x01\x03\x30\x82\x0a\xff\xfe" * 20)
        head = self.repo.commit("certificate")
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL secret-literal Certificates/dist.p12:1:secret-file:", out)
        with open(os.path.join(self.repo.path, "release.jks"), "wb") as handle:
            handle.write(b"\xfe\xed\xfe\xed\x00\x00\x00\x02" * 8)
        sh(self.repo.path, "git", "add", "release.jks")
        code, out = self.repo.run("--staged", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL secret-literal release.jks:1:secret-file:", out)

    def test_a_git_mv_adds_nothing_and_a_line_added_in_the_move_is_the_only_hit(self):
        legacy = "import SwiftUI\n" + SCRIM + "".join(f"let filler{n} = {n}\n" for n in range(8))
        self.repo.write("Sources/App/Old.swift", legacy)
        base = self.repo.commit("legacy hatch")
        sh(self.repo.path, "git", "mv", "Sources/App/Old.swift", "Sources/App/Renamed.swift")
        head = self.repo.commit("moved")
        code, out = self.repo.run(base, head, "--platform", "ios")
        self.assertEqual(code, 0, out)
        self.repo.write("Sources/App/Renamed.swift", legacy + SCRIM.replace("StatusPanel", "OtherPanel"))
        sh(self.repo.path, "git", "mv", "Sources/App/Renamed.swift", "Sources/App/Moved.swift")
        head2 = self.repo.commit("moved again, one hatch added")
        code, out = self.repo.run(head, head2, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("Moved.swift:11:scrim-modal", out)
        self.assertNotIn("Moved.swift:2:scrim-modal", out, "the legacy line moved with the file; it is not new")

    def test_a_builtin_reads_the_index_and_the_commit_not_the_worktree_file(self):
        view = "Sources/App/Views/HomeView.swift"
        self.repo.write(view, "import SwiftUI\nstruct HomeView: View { var body: some View { Text(Copy.title) } }\n")
        base = self.repo.commit("clean view")
        self.repo.write(view, 'import SwiftUI\nstruct HomeView: View { var body: some View { Text("Save your changes now") } }\n')
        sh(self.repo.path, "git", "add", view)
        # The worktree moves on: three imports above, and the literal gone. The index still holds it at line 2.
        self.repo.write(view, "import SwiftUI\nimport Foundation\nimport Combine\nstruct HomeView: View { var body: some View { Text(Copy.title) } }\n")
        code, out = self.repo.run("--staged", "--platform", "ios")
        self.assertEqual(code, 1, out)
        self.assertIn("HomeView.swift:2:ui-string-literal", out)
        sh(self.repo.path, "git", "commit", "-q", "-m", "literal")   # the index alone; the worktree stays dirty
        head = sh(self.repo.path, "git", "rev-parse", "HEAD")
        code, out = self.repo.run(base, head, "--platform", "ios")
        self.assertEqual(code, 1, out)
        self.assertIn("HomeView.swift:2:ui-string-literal", out)

    def test_flipping_a_plist_toggle_or_a_manifest_attribute_under_an_existing_key_is_caught(self):
        plist = "App/Info.plist"
        off = "<plist version=\"1.0\">\n<dict>\n\t<key>NSAppTransportSecurity</key>\n\t<dict>\n\t\t<key>NSAllowsArbitraryLoads</key>\n\t\t<false/>\n\t</dict>\n</dict>\n</plist>\n"
        self.repo.write(plist, off)
        base = self.repo.commit("ats off")
        self.repo.write(plist, off.replace("<false/>", "<true/>"))
        head = self.repo.commit("ats on")
        code, out = self.repo.run(base, head, "--platform", "ios")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL rules App/Info.plist:6:plaintext-http:", out)
        android = Repo()
        self.addCleanup(android.cleanup)
        manifest = "app/src/main/AndroidManifest.xml"
        closed = ('<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n<application>\n'
                  '    <receiver\n        android:name=".SyncReceiver"\n        android:exported="false">\n'
                  '        <intent-filter><action android:name="com.example.SYNC_NOW" /></intent-filter>\n'
                  '    </receiver>\n</application>\n</manifest>\n')
        android.write(manifest, closed)
        base = android.commit("closed")
        android.write(manifest, closed.replace('android:exported="false"', 'android:exported="true"'))
        head = android.commit("opened")
        code, out = android.run(base, head, "--platform", "android")
        self.assertEqual(code, 1, out)
        self.assertIn("app/src/main/AndroidManifest.xml:5:exported-component:", out)

    def test_the_tree_and_ratchet_pass_belongs_to_tree_mode_alone(self):
        # One trailing comment in the tree and no baseline: --tree refuses on the ratchet; the diff
        # scan the push runs beside it does not judge the ratchets at all — but it still holds the
        # tree-scope block signatures on the files the change touched.
        self.repo.write("Sources/App/A.swift", "let a = 1 // one\n")
        self.repo.write("Modules/Shared/Sources/Theme/Theme.swift", "enum Theme {}\n")
        self.repo.write("Modules/Home/Sources/HomeTheme.swift", "enum HomeTheme {}\n")
        head = self.repo.commit("a comment and a second theme")
        code, out = self.repo.run("--tree", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL ratchet inline-comment", out)
        code, out = self.repo.run(self.base, head, "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertNotIn("ratchet", out)
        self.assertIn("HomeTheme.swift:1:second-theme-file", out)
        code, out = self.repo.run(self.base, "WORKTREE", "--platform", "ios")
        self.assertNotIn("ratchet", out)

    def test_a_baseline_entry_without_a_deadline_is_refused(self):
        self.repo.write("Sources/App/A.swift", "let a = 1 // one\n")
        self.repo.write(".coast/ratchet-baseline.json", {"baselines": [
            {"id": "inline-comment", "count": 1, "written": "2026-09-04", "by": "adopt.py", "moves": []}]})
        self.repo.commit("undated")
        code, out = self.repo.run("--tree", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("FAIL ratchet .coast/ratchet-baseline.json:0:inline-comment: the baseline entry for inline-comment has no deadline", out)
        self.assertEqual(self.repo.run("--has-baseline", "inline-comment")[0], 1)
        code, out = self.repo.run("--ratchet", "build-warnings", "--count", "0", "--platform", "ios")
        self.assertEqual(code, 1)
        self.assertIn("has no deadline", out)


class PlantTests(unittest.TestCase):
    """Every folded native-pattern signature: its fail plant hits, its pass plant does not."""

    def test_every_signature_has_both_plants_and_they_behave(self):
        tables = cr.load_signature_tables()
        checked = 0
        for platform, signatures in tables.items():
            for signature in signatures:
                if signature.get("scope") == "tree" and signature.get("kind") == "builtin":
                    continue
                folder = os.path.join(PLANTS, platform)
                names = os.listdir(folder) if os.path.isdir(folder) else []
                fail = [n for n in names if n.startswith(signature["id"] + ".fail")]
                ok = [n for n in names if n.startswith(signature["id"] + ".pass")]
                self.assertEqual(len(fail), 1, f"{platform}/{signature['id']} needs one fail plant")
                self.assertEqual(len(ok), 1, f"{platform}/{signature['id']} needs one pass plant")
                fail_path = os.path.join(folder, fail[0])
                ok_path = os.path.join(folder, ok[0])
                if signature.get("kind") == "builtin":
                    with open(fail_path, encoding="utf-8") as handle:
                        fail_hits = cr.builtin_hits(signature, fail_path.replace(".fail", ""), handle.read())
                    with open(ok_path, encoding="utf-8") as handle:
                        ok_hits = cr.builtin_hits(signature, ok_path.replace(".pass", ""), handle.read())
                else:
                    fail_hits = cr.signature_hits(signature, list(enumerate(cr.read_lines(fail_path), 1)))
                    ok_hits = cr.signature_hits(signature, list(enumerate(cr.read_lines(ok_path), 1)))
                self.assertTrue(fail_hits, f"{platform}/{signature['id']}: the fail plant did not hit")
                self.assertFalse(ok_hits, f"{platform}/{signature['id']}: the pass plant hit")
                checked += 1
        self.assertGreaterEqual(checked, 52)


class SignatureTableShapeTests(unittest.TestCase):
    """E5.2: one row per signature; the loader flattens it to the per-platform lists the
    scanner, the plants and the verifier read. The ids per platform are pinned in order so a
    row that drops a platform or moves shows here, not in a hook."""

    EXPECTED_IDS = {
        "ios": [
            "appkit-reach-through", "representable-window-reach", "window-chrome-override",
            "hidden-window-toolbar", "hand-rolled-router", "scrim-modal", "nsevent-key-monitor",
            "focus-key-override", "custom-title-bar", "custom-tab-bar", "hand-rolled-search-field",
            "custom-sidebar", "hand-drawn-progress", "custom-picker-control", "import-matrix",
            "ui-string-literal", "styling-literal", "spacing-literal", "second-theme-file",
            "env-literal", "secret-literal", "secret-file", "plaintext-http", "raw-html",
            "sql-string-assembly", "cdn-script", "blocking-call", "layer-import",
            "viewmodel-ui-import", "destructive-default-key", "manual-plural", "ui-string-concat",
            "baked-case", "one-catalog-per-locale", "english-key", "fixed-text-size",
            "fixed-screen-size", "test-criterion-tag", "hermetic-test", "test-weakened",
            "pii-in-log", "inline-comment", "retired-wording", "type-size", "money-float",
            "doc-comments"],
        "macos": [
            "appkit-reach-through", "representable-window-reach", "window-chrome-override",
            "hidden-window-toolbar", "hand-rolled-router", "scrim-modal", "nsevent-key-monitor",
            "focus-key-override", "custom-title-bar", "custom-tab-bar", "hand-rolled-search-field",
            "custom-sidebar", "hand-drawn-progress", "custom-picker-control", "import-matrix",
            "ui-string-literal", "styling-literal", "spacing-literal", "second-theme-file",
            "env-literal", "secret-literal", "secret-file", "plaintext-http", "raw-html",
            "sql-string-assembly", "cdn-script", "blocking-call", "layer-import",
            "viewmodel-ui-import", "destructive-default-key", "manual-plural", "ui-string-concat",
            "baked-case", "one-catalog-per-locale", "english-key", "fixed-text-size",
            "fixed-screen-size", "test-criterion-tag", "hermetic-test", "test-weakened",
            "pii-in-log", "inline-comment", "retired-wording", "type-size", "money-float",
            "doc-comments"],
        "android": [
            "androidview-bridge", "window-flags-override", "on-back-pressed-override",
            "scrim-modal", "hand-rolled-navigator", "custom-tab-bar", "hand-drawn-progress",
            "reflection-reach", "custom-picker-control", "import-matrix", "ui-string-literal",
            "styling-literal", "spacing-literal", "second-theme-file", "env-literal",
            "secret-literal", "secret-file", "plaintext-http", "raw-html", "exported-component",
            "sql-string-assembly", "cdn-script", "blocking-call", "layer-import",
            "viewmodel-ui-import", "destructive-default-key", "manual-plural", "ui-string-concat",
            "baked-case", "one-catalog-per-locale", "english-key", "fixed-text-size",
            "fixed-screen-size", "test-criterion-tag", "hermetic-test", "test-weakened",
            "pii-in-log", "inline-comment", "retired-wording", "type-size", "money-float",
            "doc-comments"],
        "web": [
            "dom-reach-through", "inner-html-write", "div-as-button", "scrim-modal",
            "history-reach", "positive-tabindex", "custom-select", "hand-drawn-progress",
            "import-matrix", "ui-string-literal", "styling-literal", "spacing-literal",
            "second-theme-file", "env-literal", "secret-literal", "secret-file", "plaintext-http",
            "raw-html", "sql-string-assembly", "cdn-script", "blocking-call", "layer-import",
            "destructive-default-key", "manual-plural", "ui-string-concat", "baked-case",
            "one-catalog-per-locale", "english-key", "fixed-text-size", "fixed-screen-size",
            "test-criterion-tag", "hermetic-test", "test-weakened", "pii-in-log", "inline-comment",
            "retired-wording", "type-size", "money-float", "doc-comments"],
        "react-native": [
            "scrim-modal", "native-module-reach", "uimanager-reach", "hand-rolled-navigator",
            "custom-tab-bar", "hand-drawn-progress", "dangerous-navigation-state", "import-matrix",
            "ui-string-literal", "styling-literal", "spacing-literal", "second-theme-file",
            "env-literal", "secret-literal", "secret-file", "plaintext-http", "raw-html",
            "sql-string-assembly", "cdn-script", "blocking-call", "layer-import",
            "destructive-default-key", "manual-plural", "ui-string-concat", "baked-case",
            "one-catalog-per-locale", "english-key", "fixed-text-size", "fixed-screen-size",
            "test-criterion-tag", "hermetic-test", "test-weakened", "pii-in-log", "inline-comment",
            "retired-wording", "type-size", "money-float", "doc-comments"],
        "python": [
            "import-matrix", "ui-string-literal", "env-literal", "secret-literal", "secret-file",
            "plaintext-http", "raw-html", "dangerous-eval", "shell-injection",
            "sql-string-assembly", "cdn-script", "blocking-call", "layer-import",
            "hand-rolled-password-hash", "hand-rolled-query-parse", "hand-rolled-arg-parse",
            "fixed-screen-size", "test-criterion-tag", "hermetic-test", "test-weakened",
            "pii-in-log", "inline-comment", "retired-wording", "type-size", "money-float",
            "doc-comments"],
    }

    def test_every_platform_list_has_the_same_ids_in_the_same_order(self):
        tables = cr.load_signature_tables()
        self.assertEqual({platform: [s["id"] for s in sigs] for platform, sigs in tables.items()}, self.EXPECTED_IDS)

    def test_every_flattened_entry_carries_the_fields_the_scanner_reads(self):
        for platform, signatures in cr.load_signature_tables().items():
            for signature in signatures:
                where = f"{platform}/{signature.get('id')}"
                for key in ("id", "rule", "severity", "scope", "words"):
                    self.assertIsInstance(signature.get(key), str, f"{where}: {key}")
                self.assertIn(signature["severity"], ("block", "ratchet", "advisory"), where)
                self.assertIn(signature["scope"], ("added", "tree"), where)
                if signature.get("kind") == "builtin":
                    self.assertIsInstance(signature.get("applies_to", []), list, where)  # a tree built-in walks on its own
                else:
                    self.assertIsInstance(signature.get("applies_to"), list, where)
                    self.assertIsInstance(signature.get("pattern"), str, f"{where}: a regex signature needs a pattern")
                self.assertNotIn("platforms", signature, f"{where}: the platform entry is flattened, not carried")

    def test_the_platform_entry_lays_over_the_row(self):
        tables = cr.flatten_signatures({"signatures": [
            {"id": "x", "rule": "R-1", "severity": "block", "scope": "added", "applies_to": ["*"], "words": "shared",
             "platforms": {"ios": {"files": ["**/*.swift"], "pattern": "a"}, "web": {"pattern": "b", "words": "web's own"}}},
            {"id": "y", "rule": "R-2", "severity": "advisory", "scope": "tree", "applies_to": ["ui"], "words": "only web",
             "platforms": {"web": {"pattern": "c"}}}]})
        self.assertEqual(list(tables), ["ios", "web"])
        self.assertEqual(tables["ios"], [{"id": "x", "rule": "R-1", "severity": "block", "scope": "added", "applies_to": ["*"],
                                         "words": "shared", "files": ["**/*.swift"], "pattern": "a"}])
        self.assertEqual([s["id"] for s in tables["web"]], ["x", "y"])
        self.assertEqual((tables["web"][0]["words"], tables["web"][0]["pattern"]), ("web's own", "b"))
        self.assertNotIn("files", tables["web"][0])
        self.assertEqual(cr.flatten_signatures({}), {})

    def test_no_platform_entry_repeats_the_rows_value(self):
        """A platform value equal to the row's is a copy; the row already says it."""
        with open(cr.SIGNATURES_FILE, encoding="utf-8") as handle:
            document = json.load(handle)
        for row in document["signatures"]:
            self.assertTrue(row.get("platforms"), f"{row['id']}: a row with no platform runs nowhere")
            for platform, own in row["platforms"].items():
                for key, value in own.items():
                    if key in row:
                        self.assertNotEqual(value, row[key], f"{row['id']}/{platform}: {key} repeats the row")


class WebPrecisionTests(unittest.TestCase):
    """E2.11: ordinary TypeScript is not copy, the bound strings home is the one catalog, and
    prettier's one-name-per-line imports reach the import matrix."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.base = sh(self.repo.path, "git", "rev-parse", "HEAD")

    def plant(self, name):
        with open(os.path.join(PLANTS, "web", name), encoding="utf-8") as handle:
            return handle.read()

    def hits_of(self, out, signature_id):
        return [line for line in out.splitlines() if line.startswith("FAIL") and f":{signature_id}:" in line]

    def test_named_imports_comparisons_and_generics_are_not_copy(self):
        self.repo.write("src/pages/Home.tsx", self.plant("ui-string-literal.pass.tsx"))
        head = self.repo.commit("ordinary code")
        _, out = self.repo.run(self.base, head, "--platform", "web")
        self.assertEqual(self.hits_of(out, "ui-string-literal"), [])
        self.repo.write("src/pages/Home.tsx", self.plant("ui-string-literal.fail.tsx"))
        head = self.repo.commit("copy")
        code, out = self.repo.run(self.base, head, "--platform", "web")
        self.assertEqual(code, 1)
        lines = [line.split(":")[1] for line in self.hits_of(out, "ui-string-literal")]
        self.assertEqual(lines, ["3", "5", "8"], out)  # between tags, and bare text on its own line — twice

    def test_the_bound_strings_home_is_the_one_catalog_and_rebinding_moves_it(self):
        for path in ("locales/en.json", "locales/fr.json", "locales/en/common.json", "src/i18n/en.json"):
            self.repo.write(path, {"home": {"save": "Save"}})
        self.repo.commit("catalogs in the strings home")
        _, out = self.repo.run("--tree", "--platform", "web")
        self.assertEqual(self.hits_of(out, "one-catalog-per-locale"), [], out)
        self.repo.write("src/features/billing/messages.json", {"billing": {"pay": "Pay now"}})
        self.repo.commit("a second catalog beside a feature")
        _, out = self.repo.run("--tree", "--platform", "web")
        self.assertEqual([line.split(" ")[2].split(":")[0] for line in self.hits_of(out, "one-catalog-per-locale")],
                         ["src/features/billing/messages.json"])
        self.repo.write(".coast/paths.json", {"classes": {"strings": ["src/features/**/messages.json"]}})
        self.repo.commit("the project binds its strings home elsewhere")
        _, out = self.repo.run("--tree", "--platform", "web")
        flagged = sorted(line.split(" ")[2].split(":")[0] for line in self.hits_of(out, "one-catalog-per-locale"))
        self.assertNotIn("src/features/billing/messages.json", flagged)
        self.assertIn("locales/en.json", flagged)

    def test_a_named_list_broken_over_lines_reaches_the_import_matrix(self):
        multi_line = 'import type {\n  Thing,\n  Other as Renamed,\n} from "../../Profile/src/thing";\nexport const home = 1;\n'
        self.assertEqual(im.typescript_imports(multi_line), ["../../Profile/src/thing"])
        self.repo.write("package.json", {"name": "shop"})
        self.repo.write("Modules/Home/src/index.ts", multi_line)
        self.repo.write("Modules/Profile/src/thing.ts", "export const Thing = 1;\nexport const Other = 2;\n")
        self.repo.commit("cross import over several lines")
        code, out = self.repo.run("--tree", "--platform", "web")
        self.assertEqual(code, 1)
        self.assertIn("FAIL import-matrix Modules/Home/src/index.ts:0:import-matrix: Home imports Profile", out)


if __name__ == "__main__":
    unittest.main()
