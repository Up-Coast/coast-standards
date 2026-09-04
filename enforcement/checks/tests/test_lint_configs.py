"""The shipped linter configs hold every linter rule the documents name (enforcement task E1.6).

Two claims, both read from the files on disk:

* every config file ``battery.json`` names for a linter exists;
* for every ``<linter>:<rule>`` tag in the rule documents, on every platform the
  document applies to, that platform's shipped config names the rule ENABLED as
  ``verify_rules.config_enables`` reads it — so a future edit that drops
  ``force_unwrapping`` from ``swiftlint.yml`` or flips ``HardcodedText`` to
  ``ignore`` fails here, not silently in a customer's battery.

The tags are collected from the corpus by the verifier's own parser, so a rule
added later is covered without touching this file.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import json
import os
import sys
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(CHECKS_DIR))
sys.path.insert(0, CHECKS_DIR)

import verify_rules as vr  # noqa: E402

MANIFEST = os.path.join(CHECKS_DIR, "battery.json")


def load_battery():
    with open(MANIFEST, encoding="utf-8") as handle:
        return vr.Battery(json.load(handle), REPO_ROOT)


def linter_tags():
    """Every (document, platform, linter, rule-or-None) the corpus names, in document order."""
    battery = load_battery()
    report = vr.run(REPO_ROOT, MANIFEST)
    found = []
    for document in report["documents"]:
        for rule in document["rules"]:
            for raw in rule["checks"]:
                ref = vr.parse_ref(raw, battery.linter_kinds)
                if ref.kind != "linter":
                    continue
                for platform in document["platforms"]:
                    found.append((document["path"], rule["id"], platform, ref.linter, ref.name or None))
    return found


class LinterConfigFilesExist(unittest.TestCase):
    def test_every_config_the_battery_names_exists(self):
        battery = load_battery()
        missing = []
        for platform, entry in battery.platforms.items():
            for linter, spec in entry.get("linters", {}).items():
                if not battery.exists(spec.get("config")):
                    missing.append(f"{platform}/{linter}: {spec.get('config')}")
        self.assertEqual(missing, [], "battery.json names a linter config that does not exist")


class LinterTagsResolveAgainstTheShippedConfigs(unittest.TestCase):
    def test_the_corpus_names_linter_rules_at_all(self):
        tags = linter_tags()
        self.assertTrue(tags, "no linter tag found in the corpus — the parser or the documents changed shape")
        self.assertTrue(any(rule for *_, rule in tags), "no <linter>:<rule> tag found in the corpus")

    def test_every_named_linter_rule_is_enabled_in_the_shipped_config(self):
        battery = load_battery()
        not_held = []
        for path, rule_id, platform, linter, rule in linter_tags():
            linters = battery.platforms[platform].get("linters", {})
            if linter not in linters:
                not_held.append(f"{path}:{rule_id}: the {platform} battery runs no {linter}")
                continue
            config = linters[linter].get("config")
            if not battery.exists(config):
                not_held.append(f"{path}:{rule_id}: {config} does not exist")
                continue
            if rule and not vr.config_enables(linter, battery.text(config), rule):
                not_held.append(f"{path}:{rule_id}: {config} does not enable {linter}:{rule}")
        self.assertEqual(not_held, [])

    def test_the_verifier_reports_no_linter_gap(self):
        report = vr.run(REPO_ROOT, MANIFEST)
        battery = load_battery()
        linter_gaps = [
            vr.fail_line(gap) for gap in report["gaps"]
            if vr.parse_ref(gap["words"].split(":", 1)[0], battery.linter_kinds).kind == "linter"
        ]
        self.assertEqual(linter_gaps, [])


class TheOptInsTheDesignNames(unittest.TestCase):
    """README section 4.3 names these by hand; they hold even where no tag names them yet."""

    def read(self, relative):
        return load_battery().text(relative)

    def test_swiftlint_opt_ins(self):
        text = self.read("enforcement/lint/swiftlint.yml")
        for rule in ("force_unwrapping", "force_cast", "force_try", "type_body_length"):
            self.assertTrue(vr.swiftlint_enables(text, rule), rule)
        self.assertIn("baseline: .coast/lint/swiftlint-baseline.json", text, "Coast's ratchet note must survive")

    def test_eslint_is_type_checked_with_react_hooks(self):
        text = self.read("enforcement/lint/eslint.config.mjs")
        self.assertIn("recommendedTypeChecked", text)
        self.assertIn("projectService: true", text)
        for rule in ("react-hooks/rules-of-hooks", "react-hooks/exhaustive-deps", "@typescript-eslint/no-floating-promises"):
            self.assertTrue(vr.eslint_enables(text, rule), rule)

    def test_android_lint_hardcoded_text_is_an_error(self):
        text = self.read("enforcement/lint/lint.xml")
        self.assertTrue(vr.androidlint_enables(text, "HardcodedText"))
        self.assertRegex(text, r'id="HardcodedText"\s+severity="error"')

    def test_detekt_tsc_mypy_ruff(self):
        self.assertTrue(vr.detekt_enables(self.read("enforcement/lint/detekt.yml"), "UnsafeCallOnNullableType"))
        self.assertTrue(vr.tsc_enables(self.read("enforcement/lint/tsconfig.seed.json"), "strict"))
        self.assertTrue(vr.mypy_enables(self.read("enforcement/lint/mypy.ini"), "strict"))
        self.assertTrue(vr.ruff_enables(self.read("enforcement/lint/ruff.toml"), "B006"))


if __name__ == "__main__":
    unittest.main()
