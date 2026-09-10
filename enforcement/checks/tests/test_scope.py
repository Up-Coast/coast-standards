"""Tests for scope.py — what a push changed, and what the battery therefore runs (task E8).

Documents and plans alone are 'none'; a source file is 'files' with its target and every
dependent; a manifest, a governing file and a file no target owns are 'all'; the
environment word forces 'all'; the closure follows the graph, not the folder.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CHECKS_DIR)

import check_rules as cr  # noqa: E402
import scope  # noqa: E402

GRAPH = [
    {"name": "Core", "type": "library", "path": "Sources/Core", "sources": ["Core.swift"], "deps": []},
    {"name": "App", "type": "library", "path": "Sources/App", "sources": ["One.swift", "Views/HomeView.swift"], "deps": ["Core"]},
    {"name": "Tool", "type": "executable", "path": "Sources/Tool", "sources": ["main.swift"], "deps": ["Core"]},
    {"name": "CoreTests", "type": "test", "path": "Tests/CoreTests", "sources": ["CoreTests.swift"], "deps": ["Core"]},
    {"name": "AppTests", "type": "test", "path": "Tests/AppTests", "sources": ["AppTests.swift"], "deps": ["App"]},
]


def ios_paths():
    with open(cr.PATHS_FILE, encoding="utf-8") as handle:
        return cr.PathClasses(json.load(handle)["platforms"]["ios"])


class DecideTests(unittest.TestCase):
    def setUp(self):
        self.paths = ios_paths()
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.cwd = os.getcwd()
        os.chdir(self.work.name)
        self.addCleanup(os.chdir, self.cwd)
        for relative in ("Sources/Core/Core.swift", "Sources/App/One.swift", "Sources/App/Views/HomeView.swift",
                         "Sources/Tool/main.swift", "Tests/CoreTests/CoreTests.swift", "Tests/AppTests/AppTests.swift",
                         "docs/notes.md", "README.md", "Sources/App/Resources/data.json"):
            os.makedirs(os.path.dirname(relative) or ".", exist_ok=True)
            with open(relative, "w", encoding="utf-8") as handle:
                handle.write("x\n")

    def decide(self, paths, graph=GRAPH, forced=False):
        return scope.decide(paths, self.paths, self.paths.extensions, graph, forced=forced)

    def test_documents_and_plans_alone_are_none(self):
        answer = self.decide(["docs/notes.md", "README.md", "plans/F-1/plan.md"])
        self.assertEqual(answer.kind, "none")
        self.assertIn("documents and plans only", answer.reason)
        self.assertEqual(self.decide([]).reason, "nothing changed")

    def test_a_source_file_is_files_with_its_target_and_every_dependent(self):
        answer = self.decide(["Sources/Core/Core.swift", "docs/notes.md"])
        self.assertEqual(answer.kind, "files")
        self.assertTrue(answer.modules)
        self.assertEqual(answer.targets, ["App", "Core", "Tool"])
        self.assertEqual(answer.test_targets, ["AppTests", "CoreTests"])
        self.assertEqual(scope.test_filter(answer.test_targets), r"^(AppTests|CoreTests)\.")
        self.assertEqual(answer.files, ["Sources/Core/Core.swift"])
        self.assertEqual(answer.measured, ["Sources/App/One.swift", "Sources/App/Views/HomeView.swift",
                                           "Sources/Core/Core.swift", "Sources/Tool/main.swift"])

    def test_a_leaf_target_affects_only_itself_and_its_tests(self):
        answer = self.decide(["Sources/App/Views/HomeView.swift"])
        self.assertEqual((answer.targets, answer.test_targets), (["App"], ["AppTests"]))
        untested = self.decide(["Sources/Tool/main.swift"])
        self.assertEqual((untested.targets, untested.test_targets), (["Tool"], []))
        self.assertEqual(scope.test_filter([]), "")

    def test_a_resource_inside_a_target_is_that_targets_change_but_no_linters_file(self):
        answer = self.decide(["Sources/App/Resources/data.json"])
        self.assertEqual(answer.kind, "files")
        self.assertEqual(answer.targets, ["App"])
        self.assertEqual(answer.files, [], "a .json is not a Swift source the linter takes")

    def test_a_manifest_a_governing_file_and_an_unowned_file_run_everything(self):
        self.assertEqual(self.decide(["Package.swift"]).kind, "all")
        self.assertIn("the checks themselves changed", self.decide([".coast/config.json", "docs/x.md"]).reason)
        self.assertEqual(self.decide([".swiftlint.yml"]).kind, "all")
        unowned = self.decide(["Scripts/build.sh"])
        self.assertEqual(unowned.kind, "all")
        self.assertIn("belongs to no target", unowned.reason)

    def test_without_a_graph_code_is_files_but_the_modules_flag_is_off(self):
        answer = self.decide(["Sources/App/One.swift"], graph=None)
        self.assertEqual((answer.kind, answer.modules), ("files", False))
        self.assertEqual(answer.files, ["Sources/App/One.swift"])

    def test_the_environment_word_forces_everything(self):
        answer = self.decide(["docs/notes.md"], forced=True)
        self.assertEqual(answer.kind, "all")

    def test_a_deleted_source_file_still_counts_as_its_targets_change(self):
        answer = self.decide(["Sources/App/Gone.swift"])
        self.assertEqual((answer.kind, answer.targets), ("files", ["App"]))
        self.assertEqual(answer.files, [], "a deleted file is not handed to the linter")

    def test_the_shell_form_is_evaluable(self):
        answer = self.decide(["Sources/Core/Core.swift"])
        script = answer.to_sh() + 'printf "%s|%s|%s|%s\\n" "$scope_kind" "$scope_test_filter" "$scope_files" "$scope_measured"\n'
        done = subprocess.run(["sh", "-c", script], capture_output=True, text=True)
        self.assertEqual(done.stdout.strip(), r"files|^(AppTests|CoreTests)\.|1|4")


class ChangedPathsTests(unittest.TestCase):
    def test_every_pushed_range_contributes_its_paths_deletions_included(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        cwd = os.getcwd()
        os.chdir(work.name)
        self.addCleanup(os.chdir, cwd)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update({"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x"})

        def git(*args):
            return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], capture_output=True, text=True, env=env, check=True).stdout.strip()

        def commit(message, **files):
            for name, content in files.items():
                if content is None:
                    os.remove(name)
                    continue
                os.makedirs(os.path.dirname(name) or ".", exist_ok=True)
                with open(name, "w", encoding="utf-8") as handle:
                    handle.write(content)
            git("add", "-A")
            git("commit", "-q", "-m", message)
            return git("rev-parse", "HEAD")

        git("init", "-q", "-b", "main")
        start = commit("start", **{"a.swift": "1\n", "docs/n.md": "n\n"})
        second = commit("edit", **{"a.swift": "2\n"})
        third = commit("delete the doc", **{"docs/n.md": None, "b.swift": "b\n"})
        self.assertEqual(scope.changed_paths([(start, second)]), ["a.swift"])
        self.assertEqual(scope.changed_paths([(second, third)]), ["b.swift", "docs/n.md"])
        self.assertEqual(scope.changed_paths([(start, second), (second, third)]), ["a.swift", "b.swift", "docs/n.md"])
        self.assertEqual(scope.changed_paths([(scope.EMPTY_TREE, third)]), ["a.swift", "b.swift"])


if __name__ == "__main__":
    unittest.main()


class OtherGraphsTests(unittest.TestCase):
    """The Gradle, npm-workspace and Python graphs (E8.6), each on a throwaway tree."""

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.cwd = os.getcwd()
        os.chdir(self.work.name)
        self.addCleanup(os.chdir, self.cwd)

    def write(self, relative, content):
        os.makedirs(os.path.dirname(relative) or ".", exist_ok=True)
        with open(relative, "w", encoding="utf-8") as handle:
            handle.write(content)

    def test_gradle_modules_come_from_settings_and_their_edges_from_the_build_files(self):
        self.write("settings.gradle.kts", 'rootProject.name = "app"\ninclude(":app", ":core")\ninclude(":feature:home")\n')
        self.write("app/build.gradle.kts", 'plugins { id("com.android.application") }\ndependencies { implementation(project(":core")); implementation(project(":feature:home")) }\n')
        self.write("core/build.gradle.kts", 'plugins { id("com.android.library") }\n')
        self.write("feature/home/build.gradle", "apply plugin: 'com.android.library'\ndependencies { implementation project(':core') }\n")
        graph = scope.gradle_graph()
        self.assertEqual([(t["name"], t["type"], t["path"], t["deps"]) for t in graph],
                         [(":app", "app", "app", [":core", ":feature:home"]), (":core", "library", "core", []),
                          (":feature:home", "library", "feature/home", [":core"])])
        self.write("core/src/main/kotlin/Core.kt", "class Core\n")
        table = ios_paths()
        answer = scope.decide(["core/src/main/kotlin/Core.kt"], table, (".kt",), graph, flavour="gradle")
        self.assertEqual((answer.kind, answer.targets, answer.test_targets), ("files", [":app", ":core", ":feature:home"], [":app", ":core", ":feature:home"]))
        answer = scope.decide(["app/src/main/kotlin/Main.kt"], table, (".kt",), graph, flavour="gradle")
        self.assertEqual(answer.test_targets, [":app"])
        self.assertIsNone(scope.npm_graph())

    def test_npm_workspaces_are_modules_and_their_dependencies_the_edges(self):
        self.write("package.json", json.dumps({"name": "root", "workspaces": ["packages/*"]}))
        self.write("packages/ui/package.json", json.dumps({"name": "@x/ui", "dependencies": {"@x/core": "*", "react": "*"}}))
        self.write("packages/core/package.json", json.dumps({"name": "@x/core"}))
        self.write("packages/app/package.json", json.dumps({"name": "@x/app", "dependencies": {"@x/ui": "*"}}))
        graph = scope.npm_graph()
        self.assertEqual([(t["name"], t["path"], t["deps"]) for t in graph],
                         [("@x/app", "packages/app", ["@x/ui"]), ("@x/core", "packages/core", []), ("@x/ui", "packages/ui", ["@x/core"])])
        with open(os.path.join(CHECKS_DIR, "..", "checks", "paths.json"), encoding="utf-8") as handle:
            table = cr.PathClasses(json.load(handle)["platforms"]["web"])
        self.write("packages/core/src/index.ts", "export const one = 1;\n")
        answer = scope.decide(["packages/core/src/index.ts"], table, table.extensions, graph)
        self.assertEqual((answer.kind, answer.targets), ("files", ["@x/app", "@x/core", "@x/ui"]))
        self.assertEqual(answer.test_targets, [], "workspaces have no separate test targets; the hook runs npm test -w for the affected ones")
        self.write("package.json", json.dumps({"name": "single"}))
        self.assertIsNone(scope.npm_graph(), "no workspaces, no module graph — the hook uses the runner's related-tests mode")

    def test_python_files_are_nodes_and_their_imports_the_edges(self):
        subprocess.run(["git", "init", "-q"], check=True)
        self.write("src/pkg/__init__.py", "")
        self.write("src/pkg/a.py", "from pkg import b\nfrom .c import thing\n")
        self.write("src/pkg/b.py", "import json\n")
        self.write("src/pkg/c.py", "thing = 1\n")
        self.write("src/pkg/lonely.py", "x = 1\n")
        self.write("tests/test_a.py", "from pkg.a import *\n")
        self.write("tests/test_b.py", "import pkg.b\n")
        self.write("tests/test_nothing.py", "import os\n")
        subprocess.run(["git", "add", "-A"], check=True)
        with open(cr.PATHS_FILE, encoding="utf-8") as handle:
            table = cr.PathClasses(json.load(handle)["platforms"]["python"])
        graph = scope.python_graph(lambda p: table.classify(p) == "tests")
        by = {t["name"]: t for t in graph}
        self.assertEqual(by["src/pkg/a.py"]["deps"], ["src/pkg/__init__.py", "src/pkg/b.py", "src/pkg/c.py"], "`from pkg import b` reads the package too")
        self.assertEqual(by["tests/test_a.py"]["deps"], ["src/pkg/a.py"])
        self.assertEqual(by["tests/test_a.py"]["type"], "test")
        # c is imported by a, which test_a imports: the change reaches one test file.
        answer = scope.decide(["src/pkg/c.py"], table, (".py",), graph, flavour="files")
        self.assertEqual((answer.kind, answer.tests), ("files", ["tests/test_a.py"]))
        # b is reached by a (so test_a) and by test_b directly.
        self.assertEqual(scope.decide(["src/pkg/b.py"], table, (".py",), graph, flavour="files").tests, ["tests/test_a.py", "tests/test_b.py"])
        # nothing imports lonely: no test file to run, and the hook says so.
        self.assertEqual(scope.decide(["src/pkg/lonely.py"], table, (".py",), graph, flavour="files").tests, [])
        # a changed test file is itself the test to run.
        self.assertEqual(scope.decide(["tests/test_nothing.py"], table, (".py",), graph, flavour="files").tests, ["tests/test_nothing.py"])
