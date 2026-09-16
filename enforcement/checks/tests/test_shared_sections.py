"""A section that applies to more than one platform is written once.

The shared text lives in rules/platform/shared/, and tools/build_rules.py fills it into
each platform file between markers. These tests refuse a platform file that no longer
matches its shared source, a shared file only one platform uses, and a section copied
by hand into two platform files instead of being shared.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import os
import re
import sys
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(CHECKS_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import build_rules  # noqa: E402

SECTION = re.compile(r"(?m)^(?=## |# )")


def unmarked_sections(text):
    """The level-2 sections outside any shared-section block, as {heading: text}."""
    outside = build_rules.BLOCK.sub("", text)
    return {part.split("\n", 1)[0]: part.strip() for part in SECTION.split(outside) if part.startswith("## ")}


class SharedSectionsTests(unittest.TestCase):
    def test_every_platform_file_matches_its_shared_sections(self):
        stale = []
        for path in build_rules.platform_files():
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            if build_rules.render(text) != text:
                stale.append(os.path.basename(path))
        self.assertEqual(stale, [], "edit the file under rules/platform/shared/, then run python3 tools/build_rules.py")

    def test_every_shared_file_is_used_by_at_least_two_platforms(self):
        uses = build_rules.uses()
        on_disk = {f"shared/{name}" for name in os.listdir(build_rules.SHARED_DIR) if name.endswith(".md")}
        self.assertEqual(on_disk - set(uses), set(), "a shared file no platform file includes")
        single = {source: files for source, files in uses.items() if len(files) < 2}
        self.assertEqual(single, {}, "a section one platform uses belongs in that platform's file, not in shared/")

    def test_no_section_is_copied_by_hand_into_two_platform_files(self):
        seen = {}
        copies = []
        for path in build_rules.platform_files():
            with open(path, encoding="utf-8") as handle:
                sections = unmarked_sections(handle.read())
            for heading, body in sections.items():
                if heading.startswith("## Sources"):
                    continue
                key = body
                if key in seen:
                    copies.append(f"{heading} in {seen[key]} and {os.path.basename(path)}")
                else:
                    seen[key] = os.path.basename(path)
        self.assertEqual(copies, [], "move the section into rules/platform/shared/ and mark it in both files")


if __name__ == "__main__":
    unittest.main()
