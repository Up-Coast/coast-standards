"""The platform rule files carry one version: the release in which their text last changed.

tools/build_rules.py marks a changed file ``unreleased`` and replaces that mark with the
release number when a release is cut. These tests prove the check refuses a stale stamp,
a mark left behind at release time, and a stamp newer than the release, on a throwaway git
repository, and that this repository's own files are stamped right.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(CHECKS_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import build_rules  # noqa: E402


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x"})
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, env=env)


class Repo:
    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.dir.name)
        os.makedirs(os.path.join(self.root, "rules", "platform", "shared"))
        git(self.root, "init", "-q", "-b", "main")
        self.write("CHECKS-VERSION", "1.0.0\n")
        self.write("rules/platform/domain-rules-ios.md", "<!-- coast-standards-release: 1.0.0 -->\n# Project rules\n\nOne rule.\n")
        self.commit_and_tag("1.0.0")

    def write(self, relative, text):
        with open(os.path.join(self.root, relative), "w", encoding="utf-8") as handle:
            handle.write(text)

    def read(self, relative):
        with open(os.path.join(self.root, relative), encoding="utf-8") as handle:
            return handle.read()

    def commit_and_tag(self, release=None):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "x")
        if release:
            git(self.root, "tag", f"v{release}")

    def run(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = build_rules.main(list(argv), root=self.root)
        return code, out.getvalue()


class ReleaseStampTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.dir.cleanup)
        self.rules = "rules/platform/domain-rules-ios.md"

    def test_a_changed_file_is_marked_unreleased_then_stamped_at_release(self):
        self.assertEqual(self.repo.run("--check"), (0, ""))
        self.repo.write(self.rules, self.repo.read(self.rules) + "Another rule.\n")
        code, out = self.repo.run("--check")
        self.assertEqual(code, 1)
        self.assertIn("changed since release 1.0.0 but is still stamped 1.0.0", out)
        self.repo.run()
        self.assertTrue(self.repo.read(self.rules).startswith("<!-- coast-standards-release: unreleased -->\n"))
        self.assertEqual(self.repo.run("--check")[0], 0, "unreleased is fine between releases")
        self.repo.commit_and_tag()
        # Cutting 1.1.0: the mark must not survive the release commit.
        self.repo.write("CHECKS-VERSION", "1.1.0\n")
        code, out = self.repo.run("--check")
        self.assertEqual(code, 1)
        self.assertIn("still marked unreleased while CHECKS-VERSION is 1.1.0", out)
        self.repo.run("--release", "1.1.0")
        self.assertTrue(self.repo.read(self.rules).startswith("<!-- coast-standards-release: 1.1.0 -->\n"))
        self.assertEqual(self.repo.run("--check")[0], 0)

    def test_an_unchanged_file_keeps_its_stamp(self):
        self.repo.write("CHECKS-VERSION", "1.1.0\n")
        self.repo.run("--release", "1.1.0")
        self.assertTrue(self.repo.read(self.rules).startswith("<!-- coast-standards-release: 1.0.0 -->\n"))

    def test_a_stamp_newer_than_the_release_or_missing_is_refused(self):
        self.repo.write(self.rules, "<!-- coast-standards-release: 2.0.0 -->\n# Project rules\n\nOne rule.\n")
        code, out = self.repo.run("--check")
        self.assertEqual(code, 1)
        self.assertIn("newer than CHECKS-VERSION 1.0.0", out)
        self.repo.write(self.rules, "# Project rules\n\nOne rule.\n")
        code, out = self.repo.run("--check")
        self.assertEqual(code, 1)
        self.assertIn("has no release stamp", out)
        self.assertEqual(self.repo.run("--release", "v1")[0], 2)

    def test_old_number_stamps_sort_below_every_release(self):
        key = build_rules.release_key
        self.assertLess(key("9"), key("1.0.0"))
        self.assertLess(key("8"), key("9"))
        self.assertLess(key(None), key("8"))
        self.assertLess(key("1.6.0"), key("1.10.0"))
        self.assertLess(key("1.6.1"), key("unreleased"))


class ThisRepositoryTests(unittest.TestCase):
    def test_every_platform_file_is_stamped_right(self):
        problems = []
        for path in build_rules.platform_files():
            with open(path, encoding="utf-8") as handle:
                problem = build_rules.stamp_problem(path, handle.read())
            if problem:
                problems.append(problem)
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
