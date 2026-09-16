#!/usr/bin/env python3
"""Fill the shared sections of the platform rule files from their one source.

A section that applies to more than one platform is written once, in
``rules/platform/shared/<name>.md``. Each platform file marks where it goes:

    <!-- shared-section: shared/<name>.md -->
    ...the section, filled in by this tool...
    <!-- end shared-section -->

The platform files stay complete documents, because each one is installed into a
project on its own as ``docs/domain-rules.md``. Only the text between the markers
is generated. To change a shared section, edit its file under ``shared/`` and run
this tool.

Usage (from anywhere):
    python3 tools/build_rules.py          # rewrite the platform files
    python3 tools/build_rules.py --check  # exit 1 if any platform file is out of date
"""

import argparse
import glob
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATFORM_DIR = os.path.join(REPO_ROOT, "rules", "platform")
SHARED_DIR = os.path.join(PLATFORM_DIR, "shared")
BLOCK = re.compile(r"(<!-- shared-section: (?P<source>\S+) -->\n)(?P<body>.*?)(<!-- end shared-section -->)", re.S)


def platform_files():
    return sorted(glob.glob(os.path.join(PLATFORM_DIR, "*.md")))


def shared_text(source):
    """The shared file's text, ending in exactly one newline."""
    with open(os.path.join(PLATFORM_DIR, source), encoding="utf-8") as handle:
        return handle.read().rstrip("\n") + "\n"


def render(text):
    """The platform file's text with every marked block filled from its source."""
    return BLOCK.sub(lambda m: m.group(1) + shared_text(m.group("source")) + m.group(4), text)


def uses():
    """{shared file (relative to rules/platform): [platform files that include it]}."""
    found = {}
    for path in platform_files():
        with open(path, encoding="utf-8") as handle:
            for match in BLOCK.finditer(handle.read()):
                found.setdefault(match.group("source"), []).append(os.path.basename(path))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="report out-of-date files and exit 1; write nothing")
    args = parser.parse_args(argv)
    stale = []
    for path in platform_files():
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        try:
            built = render(text)
        except FileNotFoundError as error:
            print(f"build_rules: {os.path.relpath(path, REPO_ROOT)} names a shared file that does not exist: {error.filename}")
            return 1
        if built == text:
            continue
        stale.append(os.path.relpath(path, REPO_ROOT))
        if not args.check:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(built)
    if args.check:
        for path in stale:
            print(f"build_rules: {path} does not match its shared sections. Edit the file under rules/platform/shared/, "
                  f"not the copy in the platform file, then run python3 tools/build_rules.py")
        return 1 if stale else 0
    for path in stale:
        print(f"build_rules: updated {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
