"""docs/options.md is the complete settings reference, so it must name everything a person can set.

These tests read the names from the code (the installer's flags, the config defaults, the layout
table, and the lists of pre-push steps, session hooks and writing guides) and fail when the
reference page does not mention one. A change that adds an option therefore updates the page in
the same commit.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import json
import os
import re
import sys
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENFORCEMENT_DIR = os.path.dirname(CHECKS_DIR)
REPO_ROOT = os.path.dirname(ENFORCEMENT_DIR)
sys.path.insert(0, ENFORCEMENT_DIR)
sys.path.insert(0, CHECKS_DIR)

import adopt  # noqa: E402
import config as config_table  # noqa: E402
import layout as layout_table  # noqa: E402


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


OPTIONS = read(os.path.join(REPO_ROOT, "docs", "options.md"))


def missing(names):
    return sorted(name for name in names if f"`{name}" not in OPTIONS)


class OptionsReferenceTests(unittest.TestCase):
    def test_every_installer_flag_is_documented(self):
        source = read(os.path.join(ENFORCEMENT_DIR, "adopt.py"))
        flags = set()
        for match in re.finditer(r'add_argument\("(--[a-z-]+)"(?P<rest>[^\n]*)', source):
            if "SUPPRESS" not in match.group("rest"):
                flags.add(match.group(1))
        self.assertGreater(len(flags), 10, "the flag list was not read")
        self.assertEqual(missing(flags), [], "add these flags to the installer table in docs/options.md")

    def test_every_setting_is_documented(self):
        keys = set()
        for key, value in config_table.defaults().items():
            if isinstance(value, dict) and value and key != "layout":
                keys.update(f"{key}.{child}" for child in value)
            else:
                keys.add(key)
        self.assertIn("writing_guides.off", keys)
        self.assertEqual(missing(keys), [], "add these settings to the 'All keys' table in docs/options.md")

    def test_every_layout_key_is_documented(self):
        keys = [key for key in layout_table.KEYS if key != "state_dir"]
        self.assertEqual(missing(keys), [], "add these keys to the 'Layout keys' table in docs/options.md")
        self.assertIn("layout.state_dir", OPTIONS, "the page says the state folder cannot move")

    def test_every_switchable_name_is_documented(self):
        names = [name for name, _ in adopt.SEATS] + [name for name, _ in adopt.SESSION_HOOKS]
        names += [name for name, _ in adopt.WRITING_GUIDES]
        self.assertEqual(missing(names), [], "add these names to their tables in docs/options.md")

    def test_every_config_default_is_stated(self):
        defaults = config_table.defaults()
        for key in ("ratchet_days", "tests_deadline_seconds"):
            row = next((line for line in OPTIONS.splitlines() if line.startswith(f"| `{key}`")), "")
            self.assertIn(f"`{defaults[key]}`", row, f"the {key} row in docs/options.md states a different default")
        self.assertIn(json.dumps(defaults["version"]), OPTIONS)


if __name__ == "__main__":
    unittest.main()
