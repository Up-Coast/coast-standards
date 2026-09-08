"""The headline number has one name, kept in vocabulary.json; a rename must reach every page.

AC: when the label changes, this test lists every documentation line still using a retired
label, and the verifier and hook print the current one."""
import glob
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CHECKS = os.path.dirname(HERE)
SKIP_DIRS = ("/.git/", "/node_modules/", "/skills/")


def vocabulary():
    with open(os.path.join(CHECKS, "vocabulary.json"), encoding="utf-8") as handle:
        return json.load(handle)["number"]


def pages():
    """Every markdown page in the repository plus the shipped hook and installer (they print the label)."""
    found = [p for p in glob.glob(os.path.join(REPO, "**", "*.md"), recursive=True) if not any(s in p for s in SKIP_DIRS)]
    found += [os.path.join(REPO, "enforcement", "adopt.py"), os.path.join(REPO, "enforcement", "hooks", "claude-hook.py"),
              os.path.join(CHECKS, "verify_rules.py")]
    return found


class RetiredLabelsAreGone(unittest.TestCase):
    """AC: no documentation page, template, installer or hook uses a retired name for the number."""

    def test_no_page_uses_a_retired_label(self):
        entry = vocabulary()
        self.assertTrue(entry["label"].strip())
        offenders = []
        for path in pages():
            with open(path, encoding="utf-8") as handle:
                for number, line in enumerate(handle, 1):
                    for old in entry["retired"]:
                        # the vocabulary file itself and the hook's fallback list are the only places the old name may live
                        if old.lower() in line.lower() and "number_labels" not in line and '"held by a machine"]' not in line:
                            offenders.append(f"{os.path.relpath(path, REPO)}:{number}: {line.strip()[:100]}")
        self.assertEqual(offenders, [], "retired label(s) still in use:\n" + "\n".join(offenders))

    def test_current_label_is_where_the_number_is_explained(self):
        """AC: the pages that explain the number use the current name."""
        label = vocabulary()["label"]
        for relative in ("docs/how-it-works.md", "docs/faq.md", "enforcement/TEMPLATE-PROJECT-CLAUDE.md"):
            with open(os.path.join(REPO, relative), encoding="utf-8") as handle:
                self.assertIn(label, handle.read().lower(), relative)

    def test_verifier_prints_the_current_label(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("verify_rules", os.path.join(CHECKS, "verify_rules.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.number_label(), vocabulary()["label"])
        self.assertIn(vocabulary()["label"], module.summary_line("x", {b: 0 for b in list(module.BINS) + ["total"]}))


if __name__ == "__main__":
    unittest.main()
