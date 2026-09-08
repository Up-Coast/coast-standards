"""E0.3's guard: every app platform document carries the DRY, strings and
design-token rules with their checks named, and the numbered files no longer
hold a second copy (one home per rule).

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import os
import re
import sys
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(CHECKS_DIR))
sys.path.insert(0, CHECKS_DIR)

import verify_rules as vr  # noqa: E402

APP_PLATFORMS = ("ios", "macos", "android", "react-native", "web")
EXPECTED = [f"DRY-{n}" for n in range(1, 8)] + [f"L-{n}" for n in range(1, 13)] + [f"DES-{n}" for n in range(1, 5)]


def rules_in(relative):
    with open(os.path.join(REPO_ROOT, relative), encoding="utf-8") as handle:
        return vr.parse_document(handle.read(), relative)


class CorpusSectionsTests(unittest.TestCase):
    def test_every_app_platform_document_carries_dry_l_and_des_with_checks(self):
        for platform in APP_PLATFORMS:
            path = f"rules/platform/domain-rules-{platform}.md"
            by_id = {rule.id: rule for rule in rules_in(path)}
            for rule_id in EXPECTED:
                self.assertIn(rule_id, by_id, f"{path} lacks {rule_id}")
                self.assertIsNotNone(by_id[rule_id].tag_text, f"{path} {rule_id} names no check")
            self.assertEqual([r.id for r in rules_in(path) if r.id in EXPECTED], EXPECTED, f"{path}: order and count")

    def test_the_python_document_keeps_its_own_equivalents(self):
        ids = {rule.id for rule in rules_in("rules/platform/domain-rules-python.md")}
        self.assertFalse(ids & set(EXPECTED), "backend rules come from ARCH/OBS, not the app sections")
        self.assertTrue({"ARCH-6", "OBS-4"} <= ids)

    def test_the_numbered_files_point_at_the_ids_instead_of_restating_them(self):
        for path, forbidden in (("rules/04-localization.md", re.compile(r"^L-\d+$")),
                                ("rules/00-priority-rules.md", re.compile(r"^styling-lives|^strings-live|^one-name-per")),
                                ("rules/05-design-and-ui.md", re.compile(r"^one-theme-file$|^all-visual-values"))):
            ids = [rule.id for rule in rules_in(path)]
            self.assertFalse([i for i in ids if forbidden.match(i)], f"{path} still restates rules that now live in the platform documents")
        with open(os.path.join(REPO_ROOT, "rules/00-priority-rules.md"), encoding="utf-8") as handle:
            self.assertIn("DRY-1 to DRY-7", handle.read())


if __name__ == "__main__":
    unittest.main()
