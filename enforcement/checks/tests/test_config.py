"""Tests for the layout table, the config file and the switches (enforcement tasks
E5.1, E5.3, E5.4, E5.5, E5.6, E5.7).

Each guard the plan names has a plant: no shipped file carries the old path
literals; an `off` signature produces no hit on its fail plant; an `off` seat
prints `gate: <name> OFF (config)` and runs nothing; an `off` session hook exits
0 with a one-line note; a severity raised in the config is refused with a
sentence; the verifier's number falls by exactly the rules switched off; a
scripted answer file drives the prompt; `--yes` writes the default config
byte-for-byte; the configured names reach the sentences and no shipped file
carries them; no document names a path the layout table does not.

Run from the repo root:  python3 -m unittest discover -s enforcement/checks/tests
"""

import io
import json
import os
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENFORCEMENT_DIR = os.path.dirname(CHECKS_DIR)
REPO_ROOT = os.path.dirname(ENFORCEMENT_DIR)
sys.path.insert(0, CHECKS_DIR)
sys.path.insert(0, ENFORCEMENT_DIR)

import adopt  # noqa: E402
import config as cfg  # noqa: E402
import layout as lay  # noqa: E402
import verify_rules as vr  # noqa: E402
from test_hooks_and_adopt import Project, clean_env  # noqa: E402

OLD_LITERALS = ("Scripts/checks", "Scripts/hooks")
SHIPPED = [os.path.join(CHECKS_DIR, name) for name in os.listdir(CHECKS_DIR) if os.path.isfile(os.path.join(CHECKS_DIR, name))]
SHIPPED += [os.path.join(ENFORCEMENT_DIR, "hooks", name) for name in os.listdir(os.path.join(ENFORCEMENT_DIR, "hooks"))]
SHIPPED += [os.path.join(ENFORCEMENT_DIR, "lint", name) for name in os.listdir(os.path.join(ENFORCEMENT_DIR, "lint"))]
SHIPPED += [os.path.join(ENFORCEMENT_DIR, "adopt.py"), os.path.join(ENFORCEMENT_DIR, "TEMPLATE-PROJECT-CLAUDE.md"),
            os.path.join(REPO_ROOT, "skills", "adopt-coast-standards", "SKILL.md")]
DOCS = [os.path.join(REPO_ROOT, "README.md"), os.path.join(ENFORCEMENT_DIR, "DEVELOPER-GUIDE.md"),
        os.path.join(ENFORCEMENT_DIR, "TOOLCHAIN.md"), os.path.join(REPO_ROOT, "docs", "quickstart.md"),
        os.path.join(REPO_ROOT, "skills", "adopt-coast-standards", "SKILL.md")]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class LayoutTableTests(unittest.TestCase):
    def test_no_shipped_file_carries_the_old_literals(self):
        # E5.1's guard: the paths live in layout.json and nowhere else.
        for path in SHIPPED:
            if path.endswith("layout.json") or not os.path.isfile(path):
                continue
            # the installer's one legitimate mention: the folders of the layout before 1.1.0, which it moves out of
            text = "\n".join(line for line in read(path).splitlines() if "layout before 1.1.0" not in line and "LEGACY_FOLDERS = " not in line)
            for literal in OLD_LITERALS:
                self.assertNotIn(literal, text, f"{os.path.relpath(path, REPO_ROOT)} still names {literal}")

    def test_no_document_names_a_path_the_table_does_not(self):
        # E5.7's guard. The plan document (enforcement/README.md) and the changelog record history and are not held.
        for path in DOCS:
            if not os.path.isfile(path):
                continue
            for literal in OLD_LITERALS:
                self.assertNotIn(literal, read(path), f"{os.path.relpath(path, REPO_ROOT)} names {literal}")

    def test_the_defaults_put_the_checks_and_the_session_hook_under_the_state_dir(self):
        table = lay.defaults()
        self.assertEqual(table["checks_dir"], ".coast/checks")
        self.assertEqual(table["session_hook"], ".coast/hooks/claude-hook.py")
        self.assertEqual(table.session_hook_dir, ".coast/hooks")
        self.assertEqual(table.settings_local_file, ".claude/settings.local.json")
        self.assertIn("**/.coast/**", table.jscpd_ignore)

    def test_the_settings_template_and_the_governing_classes_render_from_the_table(self):
        table = lay.defaults()
        rendered = table.expand(read(os.path.join(ENFORCEMENT_DIR, "hooks", "claude-settings.json")))
        self.assertIsNone(re.search(r"\{[a-z_]+\}", rendered), "no layout placeholder is left unfilled")
        settings = json.loads(rendered)
        self.assertIn("Edit(./.coast/**)", settings["permissions"]["deny"])
        self.assertIn('.coast/hooks/claude-hook.py\\" governing-edit', json.dumps(settings["hooks"]))
        paths = json.load(open(os.path.join(CHECKS_DIR, "paths.json"), encoding="utf-8"))
        for platform, entry in paths["platforms"].items():
            self.assertIn("{state_dir}/**", entry["classes"]["governing"], platform)

    def test_a_projects_layout_override_comes_from_the_config_and_cannot_move_the_state_dir(self):
        project = Project()
        self.addCleanup(project.cleanup)
        project.write(".coast/config.json", json.dumps({"layout": {"checks_dir": "tools/checks", "state_dir": "elsewhere"}}))
        table = lay.load(project.path)
        self.assertEqual(table["checks_dir"], "tools/checks")
        self.assertEqual(table["state_dir"], ".coast")
        with self.assertRaises(cfg.ConfigError):
            cfg.load(project.path)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.project = Project()
        self.addCleanup(self.project.cleanup)
        code, out = self.project.adopt("--yes")
        self.assertEqual(code, 0, out)

    def write_config(self, **keys):
        table = json.loads(self.project.read(".coast/config.json"))
        for path, value in keys.items():
            group, key = path.split("__")
            table[group][key] = value
        self.project.write(".coast/config.json", json.dumps(table, indent=2))

    def scan(self, *args):
        done = subprocess.run([sys.executable, ".coast/checks/check_rules.py", *args, "--platform", "ios"],
                              cwd=self.project.path, capture_output=True, text=True, env=clean_env())
        return done.returncode, done.stdout + done.stderr

    def test_yes_writes_the_default_config_byte_for_byte(self):
        written = self.project.read(".coast/config.json")
        self.assertEqual(written, cfg.dump(cfg.defaults()))
        self.assertEqual(json.loads(written)["layout"], {})

    def test_an_off_signature_produces_no_hit_on_its_fail_plant(self):
        plant = read(os.path.join(CHECKS_DIR, "tests", "plants", "ios", "ui-string-literal.fail.swift"))
        self.project.write("Sources/App/Views/Planted.swift", plant)
        code, out = self.scan("--files", "Sources/App/Views/Planted.swift")
        self.assertEqual(code, 1, out)
        self.assertIn(":ui-string-literal:", out)
        self.write_config(rules__off=["ui-string-literal"])
        code, out = self.scan("--files", "Sources/App/Views/Planted.swift")
        self.assertNotIn(":ui-string-literal:", out)

    def test_a_severity_may_only_fall_and_a_raise_is_refused_with_a_sentence(self):
        self.write_config(rules__severity={"ui-string-literal": "advisory"})
        plant = read(os.path.join(CHECKS_DIR, "tests", "plants", "ios", "ui-string-literal.fail.swift"))
        self.project.write("Sources/App/Views/Planted.swift", plant)
        code, out = self.scan("--files", "Sources/App/Views/Planted.swift")
        self.assertEqual(code, 0, out)
        self.assertIn("ADVISORY rules Sources/App/Views/Planted.swift", out)
        self.write_config(rules__severity={"type-size": "block"})
        code, out = self.scan("--files", "Sources/App/Views/Planted.swift")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL config .coast/config.json:0:severity: rules.severity.type-size asks for 'block'", out)
        self.assertIn("may only lower a severity", out)

    def test_retired_words_join_the_retired_wording_signature(self):
        self.write_config(rules__retired_words=["synergy"])
        self.project.write("docs/notes.md", "We deliver synergy.\n")
        code, out = self.scan("--files", "docs/notes.md")
        self.assertEqual(code, 1, out)
        self.assertIn(":retired-wording:", out)

    def test_an_off_seat_prints_off_and_runs_nothing(self):
        self.write_config(seats__off=["jscpd", "lint"])
        code, out = self.project.hook("pre-push", "--seat", "jscpd,lint")
        self.assertEqual(code, 0, out)
        self.assertIn("gate: jscpd OFF (config)", out)
        self.assertIn("gate: lint OFF (config)", out)
        self.assertNotIn("gate: jscpd (no new clones)", out)
        self.assertNotIn("swiftlint", out)

    def test_an_off_linter_is_skipped_by_its_seat_and_not_seeded(self):
        self.write_config(linters__off=["swiftformat"])
        os.remove(os.path.join(self.project.path, ".swift-format"))
        code, out = self.project.adopt()
        self.assertEqual(code, 0, out)
        self.assertIn("swiftformat — OFF in the config", out)
        self.assertFalse(os.path.isfile(os.path.join(self.project.path, ".swift-format")))
        code, out = self.project.hook("pre-push", "--seat", "format")
        self.assertEqual(code, 0, out)
        self.assertIn("gate: swiftformat OFF (config)", out)

    def test_an_off_session_hook_exits_zero_with_a_note(self):
        self.write_config(session_hooks__off=["chained-cd", "attribution-trailer"])
        event = json.dumps({"session_id": "t", "cwd": self.project.path, "hook_event_name": "PreToolUse", "tool_name": "Bash",
                            "tool_input": {"command": "cd /tmp && ls"}, "tool_use_id": "x"})
        done = subprocess.run([sys.executable, ".coast/hooks/claude-hook.py", "chained-cd"], input=event,
                              cwd=self.project.path, capture_output=True, text=True, env=clean_env())
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stderr.strip(), "chained-cd: OFF in the project's config (session_hooks.off) — nothing was checked.")
        message = os.path.join(self.project.path, "MSG")
        with open(message, "w") as handle:
            handle.write("a commit from an agent with no trailer\n")
        code, out = self.project.hook("commit-msg", message, env=clean_env(CLAUDECODE="1"))
        self.assertEqual(code, 0, out)
        self.assertIn("gate: attribution-trailer OFF (config)", out)

    def test_the_verifier_counts_off_rules_and_the_number_falls_by_exactly_that(self):
        document = os.path.join(self.project.path, "docs", "domain-rules.md")
        before = vr.run(REPO_ROOT, os.path.join(CHECKS_DIR, "battery.json"), [document], ["ios"])["totals"]
        self.assertEqual(before["off"], 0)
        # every rule that names ui-string-literal alone, or with only ui-string-literal as its machine check, goes off
        report = vr.run(REPO_ROOT, os.path.join(CHECKS_DIR, "battery.json"), [document], ["ios"])
        held = [rule for doc in report["documents"] for rule in doc["rules"] if "scan:ui-string-literal" in rule["checks"]]
        self.assertTrue(held)
        self.write_config(rules__off=["ui-string-literal"])
        table = cfg.load(self.project.path)
        after = vr.run(REPO_ROOT, os.path.join(CHECKS_DIR, "battery.json"), [document], ["ios"], table)
        totals = after["totals"]
        gone = [rule for doc in after["documents"] for rule in doc["rules"] if rule["category"] == "off"]
        partly = [rule for doc in after["documents"] for rule in doc["rules"] if rule["off"] and rule["category"] == "partly"]
        self.assertEqual(len(gone) + len(partly), len(held))
        self.assertEqual(totals["off"], len(gone))
        self.assertEqual(totals["machine"], before["machine"] - len([r for r in held if r["category"] == "machine"]))
        self.assertEqual(totals["total"], before["total"])
        self.assertIn(f"({len(gone)} switched off)", vr.summary_line("x", totals))
        code, out = self.project.adopt()
        self.assertEqual(code, 0, out)
        self.assertIn("switched off in the config", self.project.read("CLAUDE.md"))
        self.assertIn(f"switched off {len(gone)}", self.project.read("CLAUDE.md"))

    def test_the_verifier_takes_a_config_file_on_the_command_line(self):
        self.write_config(rules__off=["ui-string-literal"])
        done = subprocess.run([sys.executable, os.path.join(CHECKS_DIR, "verify_rules.py"), "--document",
                               os.path.join(self.project.path, "docs", "domain-rules.md"), "--platform", "ios",
                               "--config", os.path.join(self.project.path, ".coast", "config.json"), "--summary"],
                              cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertRegex(done.stdout, r"enforced by a check \d+ of \d+ \(\d+ switched off\)")

    def test_the_names_come_from_the_config_and_no_shipped_file_carries_them(self):
        code, out = self.project.adopt("--owner", "Pat Lee", "--product", "Example App")
        self.assertEqual(code, 0, out)
        table = json.loads(self.project.read(".coast/config.json"))
        self.assertEqual(table["owner"], {"name": "Pat Lee", "product": "Example App", "org": ""})
        block = self.project.read("CLAUDE.md")
        self.assertIn("Example App follows the Coast Standards repo", block)
        self.assertIn('"who": "Pat Lee"', block)
        self.assertIn("## Coast Standards — the standing rules", block)
        event = json.dumps({"session_id": "t", "cwd": self.project.path, "hook_event_name": "PreToolUse", "tool_name": "Bash",
                            "tool_input": {"command": "fly deploy"}, "tool_use_id": "x"})
        done = subprocess.run([sys.executable, ".coast/hooks/claude-hook.py", "infra-command"], input=event,
                              cwd=self.project.path, capture_output=True, text=True, env=clean_env())
        self.assertEqual(done.returncode, 2)
        self.assertIn("ask Pat Lee in one line first", done.stderr)
        for path in SHIPPED:
            if os.path.isfile(path):
                text = read(path)
                for name in ("Pat Lee", "Example App"):
                    self.assertNotIn(name, text, f"{os.path.relpath(path, REPO_ROOT)} carries a name the config should supply")

    def test_without_names_the_sentences_use_general_words(self):
        block = self.project.read("CLAUDE.md")
        self.assertIn("this project follows the Coast Standards repo", block)
        self.assertIn("it is the owner's to open", block)
        event = json.dumps({"session_id": "t", "cwd": self.project.path, "hook_event_name": "PreToolUse", "tool_name": "Bash",
                            "tool_input": {"command": "fly deploy"}, "tool_use_id": "x"})
        done = subprocess.run([sys.executable, ".coast/hooks/claude-hook.py", "infra-command"], input=event,
                              cwd=self.project.path, capture_output=True, text=True, env=clean_env())
        self.assertIn("ask the owner in one line first", done.stderr)


class AskOnceTests(unittest.TestCase):
    def test_a_scripted_answer_file_drives_the_prompt(self):
        answers = iter(["ui-string-literal nonsense", "ui-string-literal spacing-literal", "jscpd", "chained-cd"])
        shown = []
        table = adopt.ask_once(cfg.defaults(), ask=lambda prompt: next(answers), out=shown.append)
        self.assertEqual(table["rules"]["off"], ["ui-string-literal", "spacing-literal"])
        self.assertEqual(table["seats"]["off"], ["jscpd"])
        self.assertEqual(table["session_hooks"]["off"], ["chained-cd"])
        text = "\n".join(shown)
        self.assertIn("not in the list: nonsense", text)
        self.assertIn("ui-string-literal", text)
        self.assertIn("gh-ruleset", text)
        self.assertIn("attribution-trailer", text)
        self.assertEqual(text.count("everything is ON unless"), 3, "one screen per group")

    def test_init_reads_the_answers_from_stdin_and_a_later_run_never_asks(self):
        project = Project()
        self.addCleanup(project.cleanup)
        done = subprocess.run([sys.executable, os.path.join(ENFORCEMENT_DIR, "adopt.py"), project.path, "--platform", "ios",
                               "--init", "--by", "Tester", "--today", "2026-09-04"],
                              input="\njscpd\n\n", capture_output=True, text=True, env=clean_env())
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        table = json.loads(project.read(".coast/config.json"))
        self.assertEqual(table["seats"]["off"], ["jscpd"])
        self.assertEqual(table["rules"]["off"], [])
        code, out = project.adopt()   # stdin is not a terminal here, and the config exists: no question
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(project.read(".coast/config.json"))["seats"]["off"], ["jscpd"], "a later run keeps the answers")
        self.assertIn("unchanged              .coast/config.json", out)


if __name__ == "__main__":
    unittest.main()
