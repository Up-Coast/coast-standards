#!/usr/bin/env python3
"""Print one version's section of CHANGELOG.md, the text published as that version's release notes.

Both release paths use this: CI, which publishes every version on main, and the manual release
workflow, which republishes a version that is missing from the releases page.

Usage (from anywhere):
    python3 tools/release_notes.py 1.9.1        # prints the section; exit 1 if there is none
"""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def notes(version, changelog_text):
    """The ``## <version> — <date>`` section, heading included, up to the next ``## `` heading; None if absent."""
    heading = re.compile(r"(?m)^## " + re.escape(version) + r" — \d{4}-\d{2}-\d{2}\n")
    match = heading.search(changelog_text)
    if not match:
        return None
    rest = changelog_text[match.start():]
    following = re.search(r"(?m)^## ", rest[3:])
    section = rest[: following.start() + 3] if following else rest
    return section.rstrip("\n") + "\n"


def main(argv=None, root=REPO_ROOT):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print(__doc__.split("\n\n")[2], file=sys.stderr)
        return 2
    with open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8") as handle:
        section = notes(argv[0], handle.read())
    if section is None:
        print(f"release_notes: CHANGELOG.md has no '## {argv[0]} — YYYY-MM-DD' section", file=sys.stderr)
        return 1
    sys.stdout.write(section)
    return 0


if __name__ == "__main__":
    sys.exit(main())
