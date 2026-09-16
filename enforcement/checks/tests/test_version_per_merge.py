"""Every merge to main raises this repository's version.

tools/version.py bump raises CHECKS-VERSION, moves the Unreleased changelog entries into a
dated section and stamps the rule files. The pre-push hook (tools/version.py check) refuses
a push to main that does not raise the version or has no changelog section for it. These
tests run both on a throwaway git repository.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import datetime as _dt
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(CHECKS_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import release_notes  # noqa: E402
import version  # noqa: E402

CHANGELOG = """# Changelog

Intro.

## Unreleased

### Fixed

- **A fix.** It works now.

## 1.0.0 — 2026-01-01

The first one.
"""


def env():
    base = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    base.update({"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x"})
    return base


def git(root, *args):
    done = subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True, env=env())
    return done.stdout.strip()


class Repo:
    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.dir.name)
        os.makedirs(os.path.join(self.root, "rules", "platform"))
        git(self.root, "init", "-q", "-b", "main")
        self.write("CHECKS-VERSION", "1.0.0\n")
        self.write("CHANGELOG.md", CHANGELOG)
        self.write("rules/platform/domain-rules-ios.md", "<!-- coast-standards-release: 1.0.0 -->\n# Rules\n")
        self.first = self.commit()
        git(self.root, "tag", "v1.0.0")

    def write(self, relative, text):
        with open(os.path.join(self.root, relative), "w", encoding="utf-8") as handle:
            handle.write(text)

    def read(self, relative):
        with open(os.path.join(self.root, relative), encoding="utf-8") as handle:
            return handle.read()

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "--allow-empty", "-m", "x")
        return git(self.root, "rev-parse", "HEAD")


class BumpTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.dir.cleanup)
        self.today = _dt.date(2026, 9, 16)

    def test_each_part_raises_the_right_number(self):
        self.assertEqual(version.raised("1.6.2", "patch"), "1.6.3")
        self.assertEqual(version.raised("1.6.2", "minor"), "1.7.0")
        self.assertEqual(version.raised("1.6.2", "major"), "2.0.0")

    def test_bump_writes_the_version_and_its_changelog_section(self):
        new = version.bump("minor", "A summary.", root=self.repo.root, today=self.today)
        self.assertEqual(new, "1.1.0")
        self.assertEqual(self.repo.read("CHECKS-VERSION"), "1.1.0\n")
        text = self.repo.read("CHANGELOG.md")
        self.assertIn("## Unreleased\n\n## 1.1.0 — 2026-09-16\n\nA summary.\n\n### Fixed\n\n- **A fix.** It works now.\n\n## 1.0.0", text)

    def test_bump_stamps_a_changed_rules_file(self):
        self.repo.write("rules/platform/domain-rules-ios.md", "<!-- coast-standards-release: 1.0.0 -->\n# Rules\n\nNew.\n")
        version.bump("patch", "A summary.", root=self.repo.root, today=self.today)
        self.assertTrue(self.repo.read("rules/platform/domain-rules-ios.md").startswith("<!-- coast-standards-release: 1.0.1 -->\n"))

    def test_bump_refuses_without_a_summary_or_entries(self):
        with self.assertRaises(ValueError):
            version.bump("patch", "  ", root=self.repo.root)
        self.repo.write("CHANGELOG.md", "# Changelog\n\n## Unreleased\n\n## 1.0.0 — 2026-01-01\n")
        with self.assertRaises(ValueError):
            version.bump("patch", "A summary.", root=self.repo.root)
        with self.assertRaises(ValueError):
            version.bump("huge", "A summary.", root=self.repo.root)


class ReleaseNotesTests(unittest.TestCase):
    def test_the_notes_are_one_version_section(self):
        text = CHANGELOG.replace("## 1.0.0 — ", "## 1.1.0 — 2026-02-02\n\nSummary.\n\n- **Thing.** Detail.\n\n## 1.0.0 — ")
        self.assertEqual(release_notes.notes("1.1.0", text), "## 1.1.0 — 2026-02-02\n\nSummary.\n\n- **Thing.** Detail.\n")
        self.assertEqual(release_notes.notes("1.0.0", text), "## 1.0.0 — 2026-01-01\n\nThe first one.\n")
        self.assertIsNone(release_notes.notes("1.0", text), "a partial version never matches a longer one")
        self.assertIsNone(release_notes.notes("2.0.0", text))


class PushCheckTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.dir.cleanup)

    def test_a_push_that_does_not_raise_the_version_is_refused(self):
        self.repo.write("README.md", "change\n")
        same = self.repo.commit()
        problems = version.check(self.repo.first, same, root=self.repo.root)
        self.assertTrue(any("CHECKS-VERSION is still 1.0.0" in p for p in problems), problems)

    def test_a_raised_version_without_a_changelog_section_is_refused(self):
        self.repo.write("CHECKS-VERSION", "1.0.1\n")
        raised = self.repo.commit()
        problems = version.check(self.repo.first, raised, root=self.repo.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("no '## 1.0.1 — YYYY-MM-DD' section", problems[0])

    def test_a_bumped_push_passes(self):
        version.bump("patch", "A summary.", root=self.repo.root)
        bumped = self.repo.commit()
        self.assertEqual(version.check(self.repo.first, bumped, root=self.repo.root), [])
        self.assertEqual(version.check("", bumped, root=self.repo.root), [], "a first push is checked for its section only")

    def test_the_installed_hook_refuses_a_push_to_main_and_ignores_other_branches(self):
        shutil.copytree(os.path.join(REPO_ROOT, "tools"), os.path.join(self.repo.root, "tools"))
        os.makedirs(os.path.join(self.repo.root, ".githooks"))
        hook = os.path.join(self.repo.root, ".githooks", "pre-push")
        shutil.copy(os.path.join(REPO_ROOT, ".githooks", "pre-push"), hook)
        same = self.repo.commit()

        def push(ref):
            line = f"refs/heads/x {same} {ref} {self.repo.first}\n"
            return subprocess.run(["sh", hook], input=line, cwd=self.repo.root, capture_output=True, text=True, env=env())
        done = push("refs/heads/main")
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("FAIL version: CHECKS-VERSION is still 1.0.0", done.stdout)
        self.assertEqual(push("refs/heads/feature").returncode, 0)


if __name__ == "__main__":
    unittest.main()
