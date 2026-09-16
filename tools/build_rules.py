#!/usr/bin/env python3
"""Build the platform rule files: fill their shared sections and keep their release stamps.

Shared sections. A section that applies to more than one platform is written once, in
``rules/platform/shared/<name>.md``. Each platform file marks where it goes:

    <!-- shared-section: shared/<name>.md -->
    ...the section, filled in by this tool...
    <!-- end shared-section -->

The platform files stay complete documents, because each one is installed into a project
on its own as ``docs/domain-rules.md``. To change a shared section, edit its file under
``shared/`` and run this tool.

Release stamps. The first line of each platform file names the release in which its text
last changed:

    <!-- coast-standards-release: 1.6.0 -->

The installer compares this stamp with a project's copy to decide whether to upgrade it.
This tool keeps it right: a file whose text differs from the release its stamp names is
marked ``unreleased``, and ``--release <version>`` replaces every ``unreleased`` mark when
a release is cut. There is no separate rules version.

Usage (from anywhere):
    python3 tools/build_rules.py                    # fill shared sections, mark changed files unreleased
    python3 tools/build_rules.py --release 1.6.2    # stamp every unreleased file with the new release
    python3 tools/build_rules.py --check            # exit 1 if any file is out of date; write nothing
"""

import argparse
import glob
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATFORM_DIR = os.path.join(REPO_ROOT, "rules", "platform")
SHARED_DIR = os.path.join(PLATFORM_DIR, "shared")
BLOCK = re.compile(r"(<!-- shared-section: (?P<source>\S+) -->\n)(?P<body>.*?)(<!-- end shared-section -->)", re.S)
STAMP = re.compile(r"\A<!-- coast-standards-release: (?P<release>\S+) -->\n")
LEGACY_STAMP = re.compile(r"\A<!-- coast-rules-version: (?P<number>\d+) -->\n")
UNRELEASED = "unreleased"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def platform_files(root=REPO_ROOT):
    return sorted(glob.glob(os.path.join(root, "rules", "platform", "*.md")))


def shared_text(source, root=REPO_ROOT):
    """The shared file's text, ending in exactly one newline."""
    with open(os.path.join(root, "rules", "platform", source), encoding="utf-8") as handle:
        return handle.read().rstrip("\n") + "\n"


def render(text, root=REPO_ROOT):
    """The platform file's text with every marked block filled from its source."""
    return BLOCK.sub(lambda m: m.group(1) + shared_text(m.group("source"), root) + m.group(4), text)


def uses(root=REPO_ROOT):
    """{shared file (relative to rules/platform): [platform files that include it]}."""
    found = {}
    for path in platform_files(root):
        with open(path, encoding="utf-8") as handle:
            for match in BLOCK.finditer(handle.read()):
                found.setdefault(match.group("source"), []).append(os.path.basename(path))
    return found


# -- release stamps

def stamp_of(text):
    """The release a file's stamp names, ``unreleased``, or None when it has no current stamp."""
    match = STAMP.match(text)
    return match.group("release") if match else None


def stamp_label(text):
    """What a file's first line says: a release, ``unreleased``, a legacy number, or None when it has no stamp."""
    match = STAMP.match(text)
    if match:
        return match.group("release")
    legacy = LEGACY_STAMP.match(text)
    return legacy.group("number") if legacy else None


def without_stamp(text):
    """The text with its first-line stamp (current or legacy) removed, for comparing contents."""
    return LEGACY_STAMP.sub("", STAMP.sub("", text, count=1), count=1)


def with_stamp(text, release):
    return f"<!-- coast-standards-release: {release} -->\n" + without_stamp(text)


def release_key(release):
    """A sortable key: a legacy number sorts below every release, ``unreleased`` above them all."""
    if release == UNRELEASED:
        return (2,)
    if release and SEMVER.match(release):
        return (1,) + tuple(int(part) for part in release.split("."))
    if release and release.isdigit():
        return (0, int(release))
    return (0, -1)


def checks_version(root=REPO_ROOT):
    with open(os.path.join(root, "CHECKS-VERSION"), encoding="utf-8") as handle:
        return handle.read().strip()


def _git(root, *args):
    if not os.path.exists(os.path.join(root, ".git")):
        return None
    done = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else None


def tag_exists(release, root=REPO_ROOT):
    return _git(root, "rev-parse", "--verify", "--quiet", f"refs/tags/v{release}") is not None


def released_text(path, release, root=REPO_ROOT):
    """The file's text at the tag ``v<release>``, or None when that cannot be read (no git, no tag)."""
    relative = os.path.relpath(path, root)
    return _git(root, "show", f"v{release}:{relative}")


def stamp_problem(path, text, root=REPO_ROOT):
    """A sentence when the file's stamp is wrong, else None."""
    release = stamp_of(text)
    name = os.path.relpath(path, root)
    current = checks_version(root)
    if release is None:
        return f"{name} has no release stamp on its first line; run python3 tools/build_rules.py"
    if release == UNRELEASED:
        if not tag_exists(current, root):
            return f"{name} is still marked unreleased while CHECKS-VERSION is {current}; run python3 tools/build_rules.py --release {current}"
        return None
    if not SEMVER.match(release):
        return f"{name} has a release stamp that is not a version: {release}"
    if release_key(release) > release_key(current):
        return f"{name} is stamped {release}, newer than CHECKS-VERSION {current}"
    old = released_text(path, release, root)
    if old is not None and without_stamp(old) != without_stamp(text):
        return f"{name} changed since release {release} but is still stamped {release}; run python3 tools/build_rules.py"
    return None


def build(text, path, root=REPO_ROOT, release=None):
    """The file as it should be: shared sections filled, and the stamp marked or released."""
    built = render(text, root)
    stamp = stamp_of(built)
    if stamp is None:
        built = with_stamp(built, UNRELEASED)
    elif stamp != UNRELEASED:
        old = released_text(path, stamp, root)
        if old is not None and without_stamp(old) != without_stamp(built):
            built = with_stamp(built, UNRELEASED)
    if release and stamp_of(built) == UNRELEASED:
        built = with_stamp(built, release)
    return built


def main(argv=None, root=REPO_ROOT):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="report out-of-date files and exit 1; write nothing")
    parser.add_argument("--release", metavar="VERSION", help="stamp every file marked unreleased with this release")
    args = parser.parse_args(argv)
    if args.release and not SEMVER.match(args.release):
        print(f"build_rules: --release takes a version like 1.6.2, not {args.release}")
        return 2
    problems = []
    for path in platform_files(root):
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        name = os.path.relpath(path, root)
        try:
            built = render(text, root)
        except FileNotFoundError as error:
            print(f"build_rules: {name} names a shared file that does not exist: {error.filename}")
            return 1
        if args.check:
            if built != text:
                problems.append(f"{name} does not match its shared sections. Edit the file under rules/platform/shared/, "
                                f"not the copy in the platform file, then run python3 tools/build_rules.py")
            problem = stamp_problem(path, text, root)
            if problem:
                problems.append(problem)
            continue
        built = build(text, path, root, args.release)
        if built != text:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(built)
            print(f"build_rules: updated {name} (stamp {stamp_of(built)})")
    for problem in problems:
        print(f"build_rules: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
