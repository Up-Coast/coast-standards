"""Tests for the ``unreached-view`` built-in (rule 08, task E4.5).

Plants in throwaway git repositories, one per platform family: a public view
constructed only by a gallery, a preview or a test FAILS; the same view
constructed on a route PASSES; a view behind a feature flag passes (a
construction inside ``if flag`` is a construction); a ``not-mounted-yet:`` tag
above the declaration passes and names its task; a non-public view is never
judged. Run from the repo root:
python3 -m unittest discover -s enforcement/checks/tests
"""

import os
import sys
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CHECKS_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_rules as cr  # noqa: E402
import unreached_views as uv  # noqa: E402
from test_check_rules import Repo  # noqa: E402

SWIFT_VIEW = "import SwiftUI\n/// The map.\npublic struct StrategyMapView: View { public var body: some View { Text(\"m\") } }\n"
SWIFT_TAGGED = ("import SwiftUI\n/// The map.\n/// not-mounted-yet: S12 — the empty-map home\n"
                "public struct StrategyMapView: View { public var body: some View { Text(\"m\") } }\n")
SWIFT_PREVIEW_ONLY = SWIFT_VIEW + "#Preview {\n    StrategyMapView()\n}\n"


def failures(repo, platform):
    code, out = repo.run("--tree", "--platform", platform)
    lines = [line for line in out.splitlines() if "unreached-view" in line and line.startswith("FAIL")]
    return code, lines


class SwiftUnreachedViewTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def test_criterion_gallery_only_fails(self):
        self.repo.write("Sources/StrategyUI/StrategyMapView.swift", SWIFT_VIEW)
        self.repo.write("Sources/StrategyUI/MapEntries.swift", "let entry = StrategyMapView()\n")
        self.repo.write("Tests/StrategyUITests/MapTests.swift", "let v = StrategyMapView()\n")
        self.repo.commit("gallery only")
        code, lines = failures(self.repo, "ios")
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("StrategyMapView.swift:3", lines[0])
        self.assertIn("not-mounted-yet", lines[0])

    def test_criterion_preview_only_fails(self):
        self.repo.write("Sources/StrategyUI/StrategyMapView.swift", SWIFT_PREVIEW_ONLY)
        self.repo.commit("preview only")
        code, lines = failures(self.repo, "ios")
        self.assertEqual(len(lines), 1, lines)

    def test_criterion_a_route_passes(self):
        self.repo.write("Sources/StrategyUI/StrategyMapView.swift", SWIFT_VIEW)
        self.repo.write("Sources/StrategyUI/MapEntries.swift", "let entry = StrategyMapView()\n")
        self.repo.write("Sources/App/Views/StrategyMapPane.swift", "struct Pane: View { var body: some View { StrategyMapView() } }\n")
        self.repo.commit("mounted")
        code, lines = failures(self.repo, "ios")
        self.assertEqual(lines, [])

    def test_criterion_a_feature_flag_is_a_route(self):
        self.repo.write("Sources/StrategyUI/StrategyMapView.swift", SWIFT_VIEW)
        self.repo.write("Sources/App/Views/Shell.swift",
                        "struct Shell: View { var body: some View { if Flags.map { StrategyMapView() } else { Text(\"\") } } }\n")
        self.repo.commit("flagged")
        code, lines = failures(self.repo, "ios")
        self.assertEqual(lines, [])

    def test_criterion_a_named_deferral_passes(self):
        self.repo.write("Sources/StrategyUI/StrategyMapView.swift", SWIFT_TAGGED)
        self.repo.write("Sources/StrategyUI/MapEntries.swift", "let entry = StrategyMapView()\n")
        self.repo.commit("deferred")
        code, lines = failures(self.repo, "ios")
        self.assertEqual(lines, [])

    def test_criterion_an_empty_tag_does_not_excuse(self):
        self.repo.write("Sources/StrategyUI/StrategyMapView.swift", SWIFT_VIEW.replace("/// The map.", "/// not-mounted-yet:"))
        self.repo.commit("empty tag")
        code, lines = failures(self.repo, "ios")
        self.assertEqual(len(lines), 1, lines)

    def test_criterion_a_helper_used_where_declared_is_reached(self):
        self.repo.write("Sources/StrategyUI/Bits.swift",
                        SWIFT_VIEW + "public struct Host: View { public var body: some View { StrategyMapView() } }\n")
        self.repo.write("Sources/App/Views/Shell.swift", "struct Shell: View { var body: some View { Host() } }\n")
        self.repo.commit("helper")
        code, lines = failures(self.repo, "ios")
        self.assertEqual(lines, [])

    def test_criterion_a_non_public_view_is_not_judged(self):
        self.repo.write("Sources/StrategyUI/Inner.swift", "struct Inner: View { var body: some View { Text(\"\") } }\n")
        self.repo.commit("internal")
        code, lines = failures(self.repo, "ios")
        self.assertEqual(lines, [])


class KotlinAndWebUnreachedViewTests(unittest.TestCase):
    """The unit, without git: the module's own reader over in-memory files."""

    class Paths:
        def __init__(self, classes):
            self.classes = classes

        def classify(self, path):
            return self.classes.get(path, "source")

    def test_criterion_kotlin_screen_reached_only_by_a_preview_fails(self):
        texts = {
            "app/src/main/java/app/ui/HomeScreen.kt": "@Composable\nfun HomeScreen() {}\n\n@Preview\n@Composable\nfun HomeScreenPreview() { HomeScreen() }\n",
        }
        paths = self.Paths({k: "ui" for k in texts})
        out = uv.failures_for("android", paths, list(texts), dict(texts))
        self.assertEqual([(p, l) for p, l, _ in out], [("app/src/main/java/app/ui/HomeScreen.kt", 2)])
        texts["app/src/main/java/app/Nav.kt"] = "fun graph() { composable(\"home\") { HomeScreen() } }\n"
        paths = self.Paths({"app/src/main/java/app/ui/HomeScreen.kt": "ui"})
        self.assertEqual(uv.failures_for("android", paths, list(texts), dict(texts)), [])

    def test_criterion_web_component_reached_only_by_a_story_fails(self):
        texts = {
            "src/components/Banner.tsx": "export function Banner() { return <div/> }\n",
            "src/components/Banner.stories.tsx": "export const Primary = () => <Banner />\n",
        }
        paths = self.Paths({"src/components/Banner.tsx": "ui_lib", "src/components/Banner.stories.tsx": "gallery"})
        out = uv.failures_for("web", paths, list(texts), dict(texts))
        self.assertEqual([(p, l) for p, l, _ in out], [("src/components/Banner.tsx", 1)])
        texts["src/pages/Home.tsx"] = "export function Home() { return <Banner /> }\n"
        paths = self.Paths({"src/components/Banner.tsx": "ui_lib", "src/components/Banner.stories.tsx": "gallery", "src/pages/Home.tsx": "ui"})
        out = uv.failures_for("web", paths, list(texts), dict(texts))
        self.assertEqual([p for p, _, _ in out], ["src/pages/Home.tsx"])   # Home itself is on no route

    def test_criterion_a_route_table_entry_counts(self):
        texts = {
            "src/pages/Home.tsx": "export function Home() { return <div/> }\n",
            "src/routes.ts": "export const routes = [{ path: '/', component: Home }]\n",
        }
        paths = self.Paths({"src/pages/Home.tsx": "ui"})
        self.assertEqual(uv.failures_for("web", paths, list(texts), dict(texts)), [])

    def test_criterion_python_has_nothing_to_judge(self):
        self.assertEqual(uv.failures_for("python", self.Paths({}), ["app/views.py"], {"app/views.py": "class X: pass\n"}), [])

    def test_criterion_the_gallery_class_is_ordered_after_tests(self):
        signatures, paths = cr.load_tables("ios")
        self.assertEqual(paths.classify("Sources/StrategyUI/MapEntries.swift"), "gallery")
        self.assertEqual(paths.classify("Tests/UITests/MapEntries.swift"), "tests")
        self.assertEqual(paths.classify("Sources/App/Views/Home.swift"), "ui")
        self.assertIn("unreached-view", {s["id"] for s in signatures})


if __name__ == "__main__":
    unittest.main()
