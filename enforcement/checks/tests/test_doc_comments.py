"""Tests for the TypeScript and Python sides of check_doc_comments.py (enforcement task E2.9).

The fail plants hold one undocumented declaration per shape the scanners once missed;
the pass plants hold the same shapes documented. Each test names the exact lines.

Run from the repo root:  python3 -m unittest -q enforcement.checks.tests.test_doc_comments
"""

import os
import sys
import unittest

CHECKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANTS = os.path.join(CHECKS_DIR, "tests", "plants")
sys.path.insert(0, CHECKS_DIR)

import check_doc_comments as dc  # noqa: E402


def reported(platform, name):
    path = os.path.join(PLANTS, platform, name)
    return [(line, entry) for _, line, entry in dc.undocumented([path], platform)]


class TypeScriptTests(unittest.TestCase):
    def test_the_fail_plant_reports_every_shape_once(self):
        self.assertEqual(reported("web", "doc-comments.fail.tsx"), [
            (9, "StatusPanel.title (var)"),      # after a multi-line @Component({ … }) decorator
            (10, "StatusPanel.save (func)"),
            (13, "greet (function)"),            # after the decorated class: the file is not silenced
            (19, "orphaned (function)"),         # a blank line between the /** */ and the declaration
            (21, "quote (const)"),               # a " inside a single-quoted string
            (23, "banner (const)"),              # a " and a ${ } inside a template string
            (25, "Note (function)"),             # an apostrophe in JSX text
            (29, "afterStrings (function)"),     # still seen after every string above
        ])

    def test_the_pass_plant_reports_nothing(self):
        self.assertEqual(reported("web", "doc-comments.pass.tsx"), [])

    def test_a_decorator_counts_its_braces(self):
        source = "@Component({\n  selector: 'x',\n})\nexport class A {\n  run() {}\n}\nexport function later() {}\n"
        names = [(d.name, [m.name for m in d.members]) for d in dc.ts_declarations(source)]
        self.assertEqual(names, [("A", ["run"]), ("later", [])])

    def test_the_js_sanitizer_empties_strings_and_reads_interpolations(self):
        self.assertEqual(dc.sanitize_js("const a = 'it\"s';"), "const a = '';")
        self.assertEqual(dc.sanitize_js("const t = `x ${ f({a: `y`}) } {`;"), "const t = `${ f({a: ``}) }`;")
        self.assertEqual(dc.sanitize_js("<p>Don't {x}</p>"), "<p>Don't {x}</p>")
        self.assertEqual(dc.sanitize_js("a; // note\n/* gone\n*/ b"), "a; //\n \n b")
        self.assertEqual(dc.sanitize_js("/** kept */ c"), "/** kept */ c")

    def test_a_blank_line_breaks_the_doc_and_a_comment_line_does_not(self):
        broken = dc.ts_declarations("/** doc */\n\nexport function a() {}\n")
        kept = dc.ts_declarations("/** doc */\n// eslint-disable-next-line\nexport function a() {}\n")
        self.assertEqual([d.doc for d in broken], [""])
        self.assertEqual([d.doc for d in kept], ["doc"])


class PythonTests(unittest.TestCase):
    def test_the_fail_plant_reports_every_shape_once(self):
        self.assertEqual(reported("python", "doc-comments.fail.py"), [
            (4, "Draft (class)"),         # a trailing comment on the class line
            (5, "Draft.save (func)"),     # a trailing comment on the def line
            (8, "Draft.render (func)"),   # the def whose body holds a nested function; the nested one is not listed
            (14, "Draft.title (func)"),   # a decorated method
            (21, "publish (func)"),       # a trailing comment on a module-level def
            (29, "parse (func)"),         # the @overload implementation; the signatures are not listed
        ])

    def test_the_pass_plant_reports_nothing(self):
        self.assertEqual(reported("python", "doc-comments.pass.py"), [])

    def test_nesting_is_exact(self):
        source = "class A:\n    '''d'''\n    def m(self):\n        def inner():\n            pass\n    class B:\n        def k(self):\n            pass\n    class _C:\n        def k(self):\n            pass\n"
        found = []
        for declaration in dc.python_declarations(source):
            dc.collect_undocumented(declaration, "", found, "python")
        self.assertEqual([entry for _, _, entry in found], ["A.m (func)", "A.B (class)", "A.B.k (func)"])

    def test_overloads_setters_and_empty_docstrings(self):
        source = ("from typing import overload\n@overload\ndef f(x: int): ...\n@overload\ndef f(x: str): ...\n"
                  "def f(x):\n    ''\n    return x\nclass P:\n    '''d'''\n    @property\n    def v(self):\n        '''d'''\n"
                  "    @v.setter\n    def v(self, x):\n        pass\n")
        found = []
        for declaration in dc.python_declarations(source):
            dc.collect_undocumented(declaration, "", found, "python")
        self.assertEqual([(line, entry) for line, _, entry in found], [(6, "f (func)")])

    def test_a_file_that_does_not_parse_reports_nothing(self):
        self.assertEqual(dc.python_declarations("def broken(:\n    pass\n"), [])


if __name__ == "__main__":
    unittest.main()
