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
            {"id": "scrim-modal", "path": "Sources/App/StatusPanel.swift", "reason": "legacy", "who": "Abbey", "when": "2026-09-04"}]})
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
        self.repo.write("tables/rules_signatures.json", {"platforms": {"ios": {"signatures": [
            {"id": "inline-comment", "rule": "02", "severity": "ratchet", "scope": "added", "applies_to": ["source", "ui"], "excludes": ["tests"],
             "pattern": r"^\s*//(?!/)", "words": "an inline comment"},
            {"id": "type-size", "rule": "A-3", "severity": "advisory", "scope": "added", "applies_to": ["source", "ui"],
             "pattern": r"\bclass\s+Huge\b", "words": "a huge type"},
            {"id": "second-theme-file", "rule": "DRY-2", "severity": "block", "scope": "tree", "applies_to": ["source", "ui"],
             "files": ["**/*Theme.swift"], "pattern": r"struct \w*Theme\b", "words": "a second theme file"},
        ]}}})
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


class PlantTests(unittest.TestCase):
    """Every folded native-pattern signature: its fail plant hits, its pass plant does not."""

    def test_every_signature_has_both_plants_and_they_behave(self):
        with open(cr.SIGNATURES_FILE, encoding="utf-8") as handle:
            tables = json.load(handle)["platforms"]
        checked = 0
        for platform, entry in tables.items():
            for signature in entry["signatures"]:
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


if __name__ == "__main__":
    unittest.main()
