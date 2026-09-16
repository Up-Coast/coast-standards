#!/usr/bin/env python3
"""Every merge to main raises the version of this repository.

The version is in ``CHECKS-VERSION``. Each version has a dated section in ``CHANGELOG.md``,
and CI tags every version that reaches ``main`` as ``v<version>`` and publishes it as a
GitHub release.

Usage (from anywhere):
    python3 tools/version.py bump patch "One sentence summarising the change."
    python3 tools/version.py bump minor "..."     # a new check, switch, rule or refusal
    python3 tools/version.py bump major "..."     # an adopted project's setup stops working
    python3 tools/version.py check <old-commit> <new-commit>

``bump`` raises ``CHECKS-VERSION``, moves the entries under ``## Unreleased`` into a new
``## <version> — <date>`` section with the summary, and stamps the rule files that changed.
``check`` is what the pre-push hook runs for a push to main: the version must be higher than
the one on main, and the changelog must have a section for it.
"""

import datetime as _dt
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_rules  # noqa: E402
import release_notes  # noqa: E402

PARTS = ("major", "minor", "patch")
UNRELEASED = "## Unreleased\n"


def parse(version):
    if not build_rules.SEMVER.match(version or ""):
        raise ValueError(f"not a version: {version!r}")
    return tuple(int(part) for part in version.split("."))


def raised(version, part):
    major, minor, patch = parse(version)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def bump(part, summary, root=REPO_ROOT, today=None):
    """Raise the version, write its changelog section, stamp the rule files. Returns the new version."""
    if part not in PARTS:
        raise ValueError(f"the part to raise is one of {', '.join(PARTS)}, not {part!r}")
    summary = summary.strip()
    if not summary:
        raise ValueError("give a one-sentence summary of the change")
    version_file = os.path.join(root, "CHECKS-VERSION")
    changelog = os.path.join(root, "CHANGELOG.md")
    with open(version_file, encoding="utf-8") as handle:
        new = raised(handle.read().strip(), part)
    with open(changelog, encoding="utf-8") as handle:
        text = handle.read()
    if UNRELEASED not in text:
        raise ValueError("CHANGELOG.md has no '## Unreleased' section")
    head, rest = text.split(UNRELEASED, 1)
    match = re.search(r"(?m)^## ", rest)
    entries = (rest[:match.start()] if match else rest).strip()
    tail = rest[match.start():] if match else ""
    if not entries:
        raise ValueError("there are no entries under '## Unreleased'; write what changed first")
    date = (today or _dt.date.today()).isoformat()
    section = f"## {new} — {date}\n\n{summary}\n\n{entries}\n\n"
    with open(changelog, "w", encoding="utf-8") as handle:
        handle.write(head + UNRELEASED + "\n" + section + tail)
    with open(version_file, "w", encoding="utf-8") as handle:
        handle.write(new + "\n")
    build_rules.main(["--release", new], root=root)
    return new


def _show(root, commit, path):
    done = subprocess.run(["git", "-C", root, "show", f"{commit}:{path}"], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else None


def check(old, new, root=REPO_ROOT):
    """Sentences explaining why a push from ``old`` to ``new`` on main is refused; empty when it is fine."""
    after = (_show(root, new, "CHECKS-VERSION") or "").strip()
    before = (_show(root, old, "CHECKS-VERSION") or "").strip() if old else ""
    problems = []
    try:
        after_key = parse(after)
    except ValueError:
        return [f"CHECKS-VERSION at the pushed commit is not a version: {after!r}"]
    if before:
        try:
            if after_key <= parse(before):
                problems.append(f"CHECKS-VERSION is still {after} (main has {before}). Every merge to main raises it: "
                                f"run python3 tools/version.py bump patch|minor|major \"<summary>\"")
        except ValueError:
            pass
    changelog = _show(root, new, "CHANGELOG.md") or ""
    if release_notes.notes(after, changelog) is None:
        problems.append(f"CHANGELOG.md has no '## {after} — YYYY-MM-DD' section; tools/version.py bump writes it")
    return problems


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) == 3 and argv[0] == "bump":
        try:
            print(f"version: {bump(argv[1], argv[2])}")
        except ValueError as error:
            print(f"version.py: {error}")
            return 2
        return 0
    if len(argv) == 3 and argv[0] == "check":
        problems = check(argv[1], argv[2])
        for problem in problems:
            print(f"FAIL version: {problem}")
        return 1 if problems else 0
    print(__doc__.split("\n\n")[2])
    return 2


if __name__ == "__main__":
    sys.exit(main())
