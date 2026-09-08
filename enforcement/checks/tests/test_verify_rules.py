"""Tests for verify_rules.py (enforcement task E0.1).

Every behaviour the docstring promises has a plant here: a fixture document
or config that must FAIL and one that must PASS. The last class runs the
real corpus and proves the honest starting line: the committed baseline
equals today's gap count, and without the baseline the corpus fails.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import datetime
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(CHECKS_DIR))
sys.path.insert(0, CHECKS_DIR)

import verify_rules as vr  # noqa: E402


# ---------------------------------------------------------------- fixtures


class Fixture:
    """A throwaway repo root with a battery manifest and whatever files a test plants."""

    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = self.dir.name
        self.manifest = {
            "scanner": "enforcement/checks/check_rules.py",
            "signatures_file": "enforcement/checks/rules_signatures.json",
            "session_hook_files": ["enforcement/hooks/claude-settings.json"],
            "documents": [],
            "platforms": {
                "ios": {"linters": {"swiftlint": {"config": "lint/swiftlint.yml"},
                                    "swiftformat": {"config": "lint/swift-format.json"}},
                        "tools": {"jscpd": {"runner": "hooks/pre-push"}}},
                "android": {"linters": {"detekt": {"config": "lint/detekt.yml"},
                                        "androidlint": {"config": "lint/lint.xml"},
                                        "ktlint": {"config": "lint/.editorconfig"}},
                            "tools": {"jscpd": {"runner": "hooks/pre-push"}}},
                "web": {"linters": {"eslint": {"config": "lint/eslint.config.mjs"},
                                    "tsc": {"config": "lint/tsconfig.json"}},
                        "tools": {"jscpd": {"runner": "hooks/pre-push"}}},
                "python": {"linters": {"ruff": {"config": "lint/ruff.toml"},
                                       "mypy": {"config": "lint/mypy.ini"}},
                           "tools": {}},
            },
        }

    def write(self, relative, content):
        full = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(content if isinstance(content, str) else json.dumps(content, indent=2))
        return full

    def document(self, relative, content, platforms="all"):
        self.write(relative, content)
        self.manifest["documents"].append({"path": relative, "platforms": platforms})

    def signatures(self, table):
        """table: {platform: {id: severity}}"""
        self.write("enforcement/checks/check_rules.py", "#!/usr/bin/env python3\n")
        rows = {}
        for platform, ids in table.items():
            for sid, severity in ids.items():
                rows.setdefault(sid, {"id": sid, "severity": severity, "platforms": {}})["platforms"][platform] = {}
        self.write("enforcement/checks/rules_signatures.json", {"signatures": list(rows.values())})

    def run(self, **kwargs):
        manifest_path = self.write("enforcement/checks/battery.json", self.manifest)
        return vr.run(self.root, manifest_path, kwargs.get("documents"), kwargs.get("platforms"))

    def main(self, *argv):
        self.write("enforcement/checks/battery.json", self.manifest)
        out = io.StringIO()
        with redirect_stdout(out):
            code = vr.main(["--root", self.root, *argv])
        return code, out.getvalue()

    def cleanup(self):
        self.dir.cleanup()


def rule(document_report, rule_id):
    return next(r for r in document_report["rules"] if r["id"] == rule_id)


SIMPLE_DOC = """# Project rules

Intro prose is not a rule.

## Money (PAY)

- **PAY-1** Money uses decimal types. [Industry practice; check: scan:money-double]
- **PAY-2** Every amount carries its currency.
  Continuation line of PAY-2. [Industry practice]
- **PAY-3** Rounding is decided once. [check: review]

## Sources

- **OWASP ASVS** — <https://owasp.org/>
"""


# ---------------------------------------------------------------- parsing


class ParsingTests(unittest.TestCase):
    def parse(self, text):
        return vr.parse_document(text, "doc.md")

    def test_id_bullets_are_rules_and_sources_and_h1_are_not(self):
        rules = self.parse(SIMPLE_DOC)
        self.assertEqual([r.id for r in rules], ["PAY-1", "PAY-2", "PAY-3"])
        self.assertEqual(rules[0].line, 7)
        self.assertEqual(rules[0].kind, "bullet")

    def test_continuation_lines_join_the_rule_and_a_blank_line_ends_it(self):
        rules = self.parse(SIMPLE_DOC)
        self.assertIn("Continuation line of PAY-2. [Industry practice]", rules[1].text)
        self.assertNotIn("Sources", rules[1].text)

    def test_id_with_em_dash_title_keeps_the_id(self):
        rules = self.parse("# T\n\n## L\n\n- **L-1 — No hardcoded text.** Every string lives in the catalog.\n")
        self.assertEqual(rules[0].id, "L-1")
        self.assertEqual(rules[0].title, "L-1 — No hardcoded text.")

    def test_anonymous_bold_bullet_gets_a_slug(self):
        rules = self.parse("# T\n\n## Communication\n\n- **Plain words, never internal labels.** Don't cite doc names.\n")
        self.assertEqual(rules[0].id, "plain-words-never-internal-labels")
        self.assertEqual(rules[0].title, "Plain words, never internal labels.")

    def test_bold_title_spanning_two_lines_is_read_whole(self):
        text = "# T\n\n## Mocks\n\n- **A mock draws the thing that changed. Chrome it doesn't redraw is still\n  there.** Infer the container.\n"
        rules = self.parse(text)
        self.assertEqual(rules[0].title, "A mock draws the thing that changed. Chrome it doesn't redraw is still there.")

    def test_leaf_prose_section_is_one_rule(self):
        text = "# T\n\n## Run atomic commands\n\nRun one command at a time. **Never chain `cd X && …`.** [check: session:chained-cd]\n\n## Disk\n\n- **Check free space** first.\n"
        rules = self.parse(text)
        self.assertEqual([(r.kind, r.id) for r in rules], [("prose", "run-atomic-commands"), ("bullet", "check-free-space")])
        self.assertEqual(rules[0].line, 3)
        self.assertEqual(rules[0].tag_text, "session:chained-cd")

    def test_container_section_with_children_is_not_a_rule(self):
        text = "# T\n\n## Parent\n\nIntro for the children.\n\n### Child one\n\nA rule stated in prose.\n\n### Child two\n\n- **Bullet rule** here.\n"
        rules = self.parse(text)
        self.assertEqual([r.id for r in rules], ["child-one", "bullet-rule"])

    def test_empty_section_is_not_a_rule_but_a_plain_list_section_is_one_prose_rule(self):
        text = "# T\n\n## Empty\n\n## Plain list\n\n- not bold\n- also not bold\n"
        rules = self.parse(text)
        self.assertEqual([(r.kind, r.id) for r in rules], [("prose", "plain-list")])

    def test_plain_bullets_after_a_bold_bullet_do_not_join_it(self):
        text = "# T\n\n## S\n\n- **X-1** The rule. [check: review]\n- a plain bullet after it\n"
        rules = self.parse(text)
        self.assertEqual(len(rules), 1)
        self.assertNotIn("plain bullet", rules[0].text)

    def test_last_bracket_with_check_wins(self):
        text = "# T\n\n## S\n\n- **X-1** Text [check: review] more text [Source; check: scan:one] tail [plain source].\n"
        self.assertEqual(self.parse(text)[0].tag_text, "scan:one")

    def test_untagged_rule_has_no_tag_text(self):
        self.assertIsNone(self.parse(SIMPLE_DOC)[1].tag_text)

    def test_legacy_deterministic_check_wording_is_read_as_a_tag(self):
        text = "# T\n\n## S\n\n- **C-3** No force unwraps. [Swift practice; deterministic check: SwiftLint force_unwrapping / force_try]\n"
        self.assertEqual(self.parse(text)[0].tag_text, "SwiftLint force_unwrapping / force_try")


# ---------------------------------------------------------------- references


class ReferenceParsingTests(unittest.TestCase):
    KINDS = {"swiftlint", "eslint", "tsc"}

    def test_every_grammar_form(self):
        cases = {
            "scan:ui-string-literal": ("scan", "ui-string-literal", "block"),
            "ratchet:inline-comment": ("scan", "inline-comment", "ratchet"),
            "advisory:type-size": ("scan", "type-size", "advisory"),
            "tool:jscpd": ("tool", "jscpd", ""),
            "session:chained-cd": ("session", "chained-cd", ""),
            "review": ("review", "", ""),
            "process": ("process", "", ""),
            "context": ("context", "", ""),
        }
        for raw, (kind, name, severity) in cases.items():
            ref = vr.parse_ref(raw, self.KINDS)
            self.assertEqual((ref.kind, ref.name, ref.severity), (kind, name, severity), raw)

    def test_linter_forms(self):
        ref = vr.parse_ref("swiftlint:force_unwrapping", self.KINDS)
        self.assertEqual((ref.kind, ref.linter, ref.name), ("linter", "swiftlint", "force_unwrapping"))
        bare = vr.parse_ref("swiftlint", self.KINDS)
        self.assertEqual((bare.kind, bare.linter, bare.name), ("linter", "swiftlint", ""))
        scoped = vr.parse_ref("eslint:@typescript-eslint/no-floating-promises", self.KINDS)
        self.assertEqual(scoped.name, "@typescript-eslint/no-floating-promises")

    def test_unknown_forms(self):
        for raw in ("detekt:Foo", "SwiftLint force_unwrapping / force_try", "scan:", "tool", "grep the diff"):
            self.assertEqual(vr.parse_ref(raw, self.KINDS).kind, "unknown", raw)


# ---------------------------------------------------------------- linter config readers


class ConfigReaderTests(unittest.TestCase):
    def test_swiftlint(self):
        config = "disabled_rules:\n  - line_length\nopt_in_rules:\n  - force_unwrapping # opt-in\ntype_body_length:\n  warning: 300\nforce_cast: error\n"
        self.assertTrue(vr.swiftlint_enables(config, "force_unwrapping"))
        self.assertTrue(vr.swiftlint_enables(config, "type_body_length"))
        self.assertTrue(vr.swiftlint_enables(config, "force_cast"))
        self.assertFalse(vr.swiftlint_enables(config, "line_length"))
        self.assertFalse(vr.swiftlint_enables(config, "force_try"), "a default rule the config never names is not proven on")
        self.assertFalse(vr.swiftlint_enables("opt_in_rules:\n  - force_unwrapping\ndisabled_rules:\n  - force_unwrapping\n", "force_unwrapping"))
        self.assertTrue(vr.swiftlint_enables("only_rules:\n  - force_try\n", "force_try"))
        self.assertTrue(vr.swiftlint_enables("opt_in_rules:\n- force_unwrapping\n", "force_unwrapping"), "list items at column 0 are valid YAML")
        self.assertFalse(vr.swiftlint_enables("only_rules:\n  - force_try\nopt_in_rules:\n  - force_cast\n", "force_cast"))

    def test_detekt(self):
        config = "potential-bugs:\n  active: true\n  UnsafeCallOnNullableType:\n    active: true\n  LateinitUsage:\n    active: false\n  Unlabelled:\n    excludes: []\n"
        self.assertTrue(vr.detekt_enables(config, "UnsafeCallOnNullableType"))
        self.assertFalse(vr.detekt_enables(config, "LateinitUsage"))
        self.assertFalse(vr.detekt_enables(config, "Unlabelled"))
        self.assertFalse(vr.detekt_enables(config, "Missing"))

    def test_eslint(self):
        config = """export default [{
  rules: {
    "@typescript-eslint/no-floating-promises": "error",
    'react-hooks/rules-of-hooks': 'error',
    "react-hooks/exhaustive-deps": ["warn", { additionalHooks: "x" }],
    "max-lines": ["warn", 300],
    "no-console": "off",
    eqeqeq: 2,
    curly: 0,
  },
}];
"""
        self.assertTrue(vr.eslint_enables(config, "@typescript-eslint/no-floating-promises"))
        self.assertTrue(vr.eslint_enables(config, "react-hooks/rules-of-hooks"))
        self.assertTrue(vr.eslint_enables(config, "react-hooks/exhaustive-deps"))
        self.assertTrue(vr.eslint_enables(config, "max-lines"))
        self.assertTrue(vr.eslint_enables(config, "eqeqeq"))
        self.assertFalse(vr.eslint_enables(config, "no-console"))
        self.assertFalse(vr.eslint_enables(config, "curly"))
        self.assertFalse(vr.eslint_enables(config, "no-var"))

    def test_androidlint(self):
        config = '<?xml version="1.0"?>\n<lint>\n  <issue id="HardcodedText" severity="error" />\n  <issue id="UnusedResources" severity="ignore"/>\n  <issue id="Typos"/>\n</lint>\n'
        self.assertTrue(vr.androidlint_enables(config, "HardcodedText"))
        self.assertFalse(vr.androidlint_enables(config, "UnusedResources"))
        self.assertTrue(vr.androidlint_enables(config, "Typos"))
        self.assertFalse(vr.androidlint_enables(config, "Missing"))

    def test_tsc(self):
        config = '{\n  // the seed\n  "compilerOptions": {"strict": true, "noImplicitAny": false}\n}\n'
        self.assertTrue(vr.tsc_enables(config, "strict"))
        self.assertFalse(vr.tsc_enables(config, "noImplicitAny"))
        self.assertFalse(vr.tsc_enables(config, "noUnusedLocals"))
        self.assertFalse(vr.tsc_enables("not json", "strict"))

    def test_mypy_and_ruff(self):
        self.assertTrue(vr.mypy_enables("[mypy]\nstrict = True\n", "strict"))
        self.assertFalse(vr.mypy_enables("[mypy]\nstrict = False\n", "strict"))
        ruff = '[lint]\nselect = ["E", "F", "B006"]\nignore = ["E501"]\n'
        self.assertTrue(vr.ruff_enables(ruff, "B006"))
        self.assertTrue(vr.ruff_enables(ruff, "E401"))
        self.assertFalse(vr.ruff_enables(ruff, "E501"))
        self.assertFalse(vr.ruff_enables(ruff, "S101"))
        self.assertTrue(vr.ruff_enables('select = ["ALL"]\n', "S101"))

    def test_generic_reader_is_whole_word(self):
        self.assertTrue(vr.generic_enables("run: jscpd --min-tokens 50", "jscpd"))
        self.assertFalse(vr.generic_enables("run: jscpd-fork", "jscpd"))


# ---------------------------------------------------------------- resolution


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def doc(self, body, platforms=("ios",), path="docs/rules.md"):
        self.fx.document(path, "# T\n\n## S\n\n" + body + "\n", platforms if isinstance(platforms, str) else list(platforms))

    def gaps_of(self, rule_id, report_index=0):
        report = self.fx.run()
        return rule(report["documents"][report_index], rule_id)["gaps"], report

    def test_untagged_and_empty_tags(self):
        self.doc("- **X-1** No tag.\n- **X-2** Empty. [check: ]\n")
        report = self.fx.run()
        self.assertEqual(rule(report["documents"][0], "X-1")["gaps"], ["no check tag"])
        self.assertEqual(rule(report["documents"][0], "X-2")["gaps"], ["empty check tag"])
        self.assertEqual(report["totals"]["open"], 2)

    def test_legacy_wording_is_an_unknown_check(self):
        self.doc("- **C-3** Text. [Swift practice; deterministic check: SwiftLint force_unwrapping / force_try]\n")
        gaps, _ = self.gaps_of("C-3")
        self.assertEqual(len(gaps), 1)
        self.assertTrue(gaps[0].startswith("unknown check 'SwiftLint force_unwrapping / force_try'"), gaps[0])

    def test_scan_resolves_only_with_scanner_table_id_and_severity(self):
        self.doc("- **X-1** Text. [check: scan:one]\n- **X-2** Text. [check: ratchet:one]\n- **X-3** Text. [check: scan:missing]\n")
        gaps, _ = self.gaps_of("X-1")
        self.assertIn("the scanner enforcement/checks/check_rules.py does not exist", gaps[0])
        self.assertIn("the signatures file enforcement/checks/rules_signatures.json does not exist", gaps[1])
        self.fx.signatures({"ios": {"one": "block"}})
        report = self.fx.run()
        doc = report["documents"][0]
        self.assertEqual(rule(doc, "X-1")["gaps"], [])
        self.assertEqual(rule(doc, "X-2")["gaps"], ["ratchet:one: signature 'one' is block in the ios table, the rule says ratchet"])
        self.assertEqual(rule(doc, "X-3")["gaps"], ["scan:missing: no signature 'missing' in the ios table"])

    def test_all_platform_document_needs_the_signature_on_every_platform(self):
        self.doc("- **X-1** Text. [check: scan:one]\n", platforms=("ios", "android"))
        self.fx.signatures({"ios": {"one": "block"}})
        gaps, _ = self.gaps_of("X-1")
        self.assertEqual(gaps, ["scan:one: the signatures file has no android table"])
        self.fx.signatures({"ios": {"one": "block"}, "android": {"two": "block"}})
        gaps, _ = self.gaps_of("X-1")
        self.assertEqual(gaps, ["scan:one: no signature 'one' in the android table"])

    def test_a_group_name_resolves_and_covers_its_members(self):
        self.doc("- **A-7** [check: scan:native-pattern]\n")
        self.fx.write("enforcement/checks/check_rules.py", "#!/usr/bin/env python3\n")
        self.fx.write("enforcement/checks/rules_signatures.json", {"signatures": [
            {"id": "scrim-modal", "group": "native-pattern", "severity": "block", "platforms": {"ios": {"pattern": "x"}}},
            {"id": "custom-tab-bar", "group": "native-pattern", "severity": "block", "platforms": {"ios": {"pattern": "y"}}}]})
        report = self.fx.run()
        self.assertEqual(rule(report["documents"][0], "A-7")["gaps"], [])
        self.assertEqual(report["gaps"], [], "members of a named group are not unnamed signatures")

    def test_unnamed_signature_is_a_gap(self):
        self.doc("- **X-1** Text. [check: scan:one]\n")
        self.fx.signatures({"ios": {"one": "block", "orphan": "block"}})
        report = self.fx.run()
        orphan = [g for g in report["gaps"] if g["id"] == "orphan"]
        self.assertEqual(len(orphan), 1)
        self.assertEqual(orphan[0]["words"], "signature 'orphan' in the ios table is named by no rule")
        self.assertEqual(orphan[0]["path"], "enforcement/checks/rules_signatures.json")

    def test_linter_rule_needs_platform_linter_config_and_the_rule_on(self):
        self.doc("- **C-3** Text. [check: swiftlint:force_unwrapping]\n- **C-4** Text. [check: swiftlint, swiftformat]\n- **C-5** Text. [check: detekt:X]\n")
        report = self.fx.run()
        doc = report["documents"][0]
        self.assertEqual(rule(doc, "C-3")["gaps"], ["swiftlint:force_unwrapping: the ios swiftlint config lint/swiftlint.yml does not exist"])
        self.assertEqual(rule(doc, "C-5")["gaps"], ["detekt:X: the ios battery runs no detekt"])
        self.fx.write("lint/swiftlint.yml", "disabled_rules:\n  - line_length\n")
        self.fx.write("lint/swift-format.json", "{}")
        report = self.fx.run()
        doc = report["documents"][0]
        self.assertEqual(rule(doc, "C-3")["gaps"], ["swiftlint:force_unwrapping: lint/swiftlint.yml does not enable force_unwrapping"])
        self.assertEqual(rule(doc, "C-4")["gaps"], [])
        self.fx.write("lint/swiftlint.yml", "opt_in_rules:\n  - force_unwrapping\n")
        report = self.fx.run()
        self.assertEqual(rule(report["documents"][0], "C-3")["gaps"], [])
        self.assertEqual(rule(report["documents"][0], "C-3")["category"], "machine")

    def test_each_config_format_resolves_through_the_battery(self):
        self.doc("- **A-1** [check: detekt:UnsafeCallOnNullableType, androidlint:HardcodedText, ktlint]\n", platforms=("android",))
        self.doc("- **W-1** [check: eslint:react-hooks/rules-of-hooks, tsc:strict]\n", platforms=("web",), path="docs/web.md")
        self.doc("- **P-1** [check: ruff:B006, mypy:strict]\n", platforms=("python",), path="docs/py.md")
        self.fx.write("lint/detekt.yml", "potential-bugs:\n  UnsafeCallOnNullableType:\n    active: true\n")
        self.fx.write("lint/lint.xml", '<lint><issue id="HardcodedText" severity="error"/></lint>')
        self.fx.write("lint/.editorconfig", "root = true\n")
        self.fx.write("lint/eslint.config.mjs", 'export default [{rules: {"react-hooks/rules-of-hooks": "error"}}];')
        self.fx.write("lint/tsconfig.json", '{"compilerOptions": {"strict": true}}')
        self.fx.write("lint/ruff.toml", '[lint]\nselect = ["B006"]\n')
        self.fx.write("lint/mypy.ini", "[mypy]\nstrict = True\n")
        report = self.fx.run()
        for index, rule_id in enumerate(("A-1", "W-1", "P-1")):
            self.assertEqual(rule(report["documents"][index], rule_id)["gaps"], [], rule_id)
            self.assertEqual(rule(report["documents"][index], rule_id)["category"], "machine")

    def test_tool_needs_a_runner_that_exists_and_names_it(self):
        self.doc("- **X-1** [check: tool:jscpd]\n- **X-2** [check: tool:semgrep]\n")
        report = self.fx.run()
        doc = report["documents"][0]
        self.assertEqual(rule(doc, "X-1")["gaps"], ["tool:jscpd: the ios runner for jscpd, hooks/pre-push, does not exist"])
        self.assertEqual(rule(doc, "X-2")["gaps"], ["tool:semgrep: the ios battery runs no tool 'semgrep'"])
        self.fx.write("hooks/pre-push", "#!/bin/sh\nswiftlint\n")
        report = self.fx.run()
        self.assertEqual(rule(report["documents"][0], "X-1")["gaps"], ["tool:jscpd: hooks/pre-push never mentions jscpd"])
        self.fx.write("hooks/pre-push", "#!/bin/sh\njscpd --fail-on-new-clones\n")
        report = self.fx.run()
        self.assertEqual(rule(report["documents"][0], "X-1")["gaps"], [])

    def test_session_needs_a_hook_file_naming_the_id(self):
        self.doc("- **S-1** [check: session:chained-cd]\n")
        gaps, _ = self.gaps_of("S-1")
        self.assertEqual(gaps, ["session:chained-cd: no session hook file exists (enforcement/hooks/claude-settings.json)"])
        self.fx.write("enforcement/hooks/claude-settings.json", '{"hooks": {"PreToolUse": [{"command": "python3 claude-hook.py governing-edit"}]}}')
        gaps, _ = self.gaps_of("S-1")
        self.assertEqual(gaps, ["session:chained-cd: no session hook file names 'chained-cd'"])
        self.fx.write("enforcement/hooks/claude-settings.json", '{"hooks": {"PreToolUse": [{"command": "python3 claude-hook.py chained-cd"}]}}')
        gaps, _ = self.gaps_of("S-1")
        self.assertEqual(gaps, [])

    def test_unknown_reference_lists_the_grammar(self):
        self.doc("- **X-1** [check: grep the diff]\n")
        gaps, _ = self.gaps_of("X-1")
        self.assertTrue(gaps[0].startswith("unknown check 'grep the diff' (expected one of: advisory, "), gaps[0])
        self.assertIn("swiftlint", gaps[0])

    def test_categories_and_context(self):
        self.doc("- **M-1** [check: scan:one, tool:jscpd]\n"
                 "- **P-1** [check: scan:one, review]\n"
                 "- **A-1** [check: advisory:soft]\n"
                 "- **R-1** [check: review]\n"
                 "- **Q-1** [check: process]\n"
                 "- **K-1** [check: context]\n"
                 "- **K-2** [check: context, review]\n"
                 "- **O-1** [check: scan:none]\n")
        self.fx.signatures({"ios": {"one": "block", "soft": "advisory"}})
        self.fx.write("hooks/pre-push", "jscpd\n")
        report = self.fx.run()
        doc = report["documents"][0]
        expected = {"M-1": "machine", "P-1": "partly", "A-1": "advisory", "R-1": "review", "Q-1": "process",
                    "K-1": "context", "K-2": "open", "O-1": "open"}
        for rule_id, category in expected.items():
            self.assertEqual(rule(doc, rule_id)["category"], category, rule_id)
        self.assertEqual(rule(doc, "K-2")["gaps"], ["'context' cannot share a tag with a check"])
        counts = doc["counts"]
        self.assertEqual(counts["total"], 7, "context rows are not counted")
        self.assertEqual(counts["context"], 1)
        self.assertEqual((counts["machine"], counts["partly"], counts["advisory"], counts["review"], counts["process"], counts["open"]),
                         (1, 1, 1, 1, 1, 2))

    def test_a_bare_platform_string_is_one_platform_and_an_unknown_one_is_a_gap(self):
        self.doc("- **X-1** [check: review]\n", platforms="ios")
        report = self.fx.run()
        self.assertEqual(report["documents"][0]["platforms"], ["ios"])
        self.assertEqual(report["gaps"], [])
        self.fx.manifest["documents"][0]["platforms"] = ["ios", "tvos"]
        report = self.fx.run()
        self.assertEqual(report["gaps"][0]["words"], "the document names platform 'tvos', which the battery does not know")

    def test_missing_document_is_a_gap(self):
        self.fx.manifest["documents"].append({"path": "docs/missing.md", "platforms": "all"})
        report = self.fx.run()
        self.assertEqual(report["gaps"][0]["words"], "document does not exist")

    def test_document_override_does_not_report_unnamed_signatures(self):
        # One project's document names the checks its rules use, not every signature in
        # the platform table: a single iOS document reported 198 false gaps and exit 1.
        self.doc("- **X-1** [check: scan:one]\n")
        self.fx.signatures({"ios": {"one": "block", "orphan": "block"}})
        report = self.fx.run(documents=["docs/rules.md"], platforms=["ios"])
        self.assertEqual(report["gaps"], [])
        self.assertEqual(report["gap_count"], 0)

    def test_document_override_replaces_the_manifest_list(self):
        self.doc("- **X-1** [check: scan:one]\n")
        self.fx.write("docs/other.md", "# T\n\n## S\n\n- **Y-1** [check: review]\n")
        report = self.fx.run(documents=["docs/other.md"], platforms=["android"])
        self.assertEqual([d["path"] for d in report["documents"]], ["docs/other.md"])
        self.assertEqual(report["documents"][0]["platforms"], ["android"])
        self.assertEqual(report["totals"]["review"], 1)


# ---------------------------------------------------------------- output and exit codes


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.document("docs/rules.md", "# T\n\n## S\n\n- **X-1** Text. [check: review]\n- **X-2** No tag.\n", ["ios"])

    def test_fail_lines_summary_and_exit_code(self):
        code, out = self.fx.main()
        self.assertEqual(code, 1)
        self.assertIn("FAIL verify-rules docs/rules.md:6:X-2: no check tag", out)
        self.assertIn("docs/rules.md [ios]: enforced by a check 0 of 2 · partly 0 · advisory 0 · reviewer 1 · process 0 · open 1", out)
        self.assertIn("TOTAL: enforced by a check 0 of 2", out)
        self.assertTrue(out.strip().endswith("FAIL verify-rules: 1 gaps — every rule names its check and every check runs, or this fails"))

    def test_summary_mode_drops_the_per_rule_lines(self):
        code, out = self.fx.main("--summary")
        self.assertEqual(code, 1)
        self.assertNotIn("X-2: no check tag", out)
        self.assertIn("TOTAL:", out)

    def test_json_mode_is_valid_json_with_the_verdict(self):
        code, out = self.fx.main("--json")
        self.assertEqual(code, 1)
        report = json.loads(out)
        self.assertEqual(report["gap_count"], 1)
        self.assertTrue(report["verdict"].startswith("FAIL verify-rules: 1 gaps"))
        self.assertEqual(report["documents"][0]["rules"][1]["gaps"], ["no check tag"])

    def test_green_corpus_exits_zero(self):
        self.fx.manifest["documents"] = []
        self.fx.document("docs/green.md", "# T\n\n## S\n\n- **X-1** [check: review]\n", ["ios"])
        code, out = self.fx.main()
        self.assertEqual(code, 0)
        self.assertIn("OK verify-rules: every rule names its check and every check runs", out)

    def test_missing_manifest_fails_in_the_line_format(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = vr.main(["--root", self.fx.root, "--battery", os.path.join(self.fx.root, "nope.json")])
        self.assertEqual(code, 1)
        self.assertIn("FAIL verify-rules", out.getvalue())
        self.assertIn("the battery manifest does not exist", out.getvalue())


class RatchetTests(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.document("docs/rules.md", "# T\n\n## S\n\n- **X-1** [check: review]\n- **X-2** No tag.\n- **X-3** No tag.\n", ["ios"])

    def baseline(self, count, deadline="2026-12-03"):
        return self.fx.write("baseline.json", {"id": "verify-rules-gaps", "count": count, "deadline": deadline})

    def test_equal_count_passes_and_names_the_days_left(self):
        code, out = self.fx.main("--baseline", self.baseline(2), "--today", "2026-09-04")
        self.assertEqual(code, 0)
        self.assertIn("OK verify-rules baseline: 2 gaps, equal to the baseline; 90 days until the deadline 2026-12-03", out)

    def test_a_rise_fails(self):
        code, out = self.fx.main("--baseline", self.baseline(1), "--today", "2026-09-04")
        self.assertEqual(code, 1)
        self.assertIn("FAIL verify-rules baseline: the gap count rose from 1 to 2", out)

    def test_a_fall_fails_until_the_baseline_is_lowered(self):
        code, out = self.fx.main("--baseline", self.baseline(5), "--today", "2026-09-04")
        self.assertEqual(code, 1)
        self.assertIn("the gap count fell from 5 to 2 — lower the baseline to 2 in the same commit", out)

    def test_past_the_deadline_any_gap_fails(self):
        code, out = self.fx.main("--baseline", self.baseline(2), "--today", "2026-12-04")
        self.assertEqual(code, 1)
        self.assertIn("the baseline deadline 2026-12-03 has passed with 2 gaps still open — the check is now blocking", out)

    def test_zero_gaps_past_the_deadline_still_passes(self):
        self.fx.manifest["documents"] = []
        self.fx.document("docs/green.md", "# T\n\n## S\n\n- **X-1** [check: review]\n", ["ios"])
        code, _ = self.fx.main("--baseline", self.baseline(0), "--today", "2027-01-01")
        self.assertEqual(code, 0)

    def test_malformed_baseline_fails(self):
        path = self.fx.write("baseline.json", {"count": "two", "deadline": "2026-12-03"})
        code, out = self.fx.main("--baseline", path)
        self.assertEqual(code, 1)
        self.assertIn("needs an integer 'count' and a 'deadline'", out)
        path = self.fx.write("baseline.json", {"count": 2, "deadline": "soon"})
        code, out = self.fx.main("--baseline", path)
        self.assertEqual(code, 1)
        self.assertIn("is not a date", out)


# ---------------------------------------------------------------- the real corpus


class TodaysCorpusTests(unittest.TestCase):
    """The honest starting line, proven on the repo as it stands."""

    BASELINE = os.path.join(REPO_ROOT, "enforcement", "checks", "verify-baseline.json")
    SCRIPT = os.path.join(CHECKS_DIR, "verify_rules.py")

    def run_script(self, *argv):
        result = subprocess.run([sys.executable, self.SCRIPT, *argv], cwd=REPO_ROOT, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    def test_every_platform_document_rule_is_counted_once(self):
        code, out = self.run_script("--json")
        report = json.loads(out)
        by_path = {d["path"]: d for d in report["documents"]}
        for path, doc in by_path.items():
            if not path.startswith("rules/platform/"):
                continue
            with open(os.path.join(REPO_ROOT, path), encoding="utf-8") as handle:
                text = handle.read()
            body = text.split("\n## Sources", 1)[0]
            expected = len(re.findall(r"^- \*\*[A-Z][A-Z0-9]*-\d+\b", body, re.MULTILINE))
            self.assertEqual(len(doc["rules"]), expected, path)
            self.assertEqual(len({r["id"] for r in doc["rules"]}), expected, f"duplicate ids in {path}")

    def test_the_committed_baseline_equals_todays_gap_count(self):
        with open(self.BASELINE, encoding="utf-8") as handle:
            baseline = json.load(handle)
        code, out = self.run_script("--baseline", self.BASELINE, "--summary")
        self.assertEqual(code, 0, out)
        code, out = self.run_script("--json")
        report = json.loads(out)
        self.assertEqual(report["gap_count"], baseline["count"])
        self.assertEqual(code, 0 if baseline["count"] == 0 else 1, "without the baseline, a corpus with gaps fails")
        deadline = datetime.date.fromisoformat(baseline["deadline"])
        written = datetime.date.fromisoformat(baseline["written"])
        self.assertEqual((deadline - written).days, 90, "the default deadline is 90 days from the day the baseline was written")


if __name__ == "__main__":
    unittest.main()
