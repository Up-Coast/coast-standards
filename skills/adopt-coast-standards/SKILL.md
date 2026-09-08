---
name: adopt-coast-standards
description: Install or upgrade Coast Standards (engineering rules for AI-built software, with the checks that enforce them) in the current project. Use when asked to adopt, install, set up, or upgrade Coast Standards, or to add coding-standard checks and git hooks to a repository. Fetches a published release; the rules and checks then live in the project's own copy.
---

# Adopt Coast Standards

This skill only says where the releases are and how to run the installer. Nothing
else lives here: the rules, the checks and the hooks are copied into the project by
the installer and belong to the project from then on, like any other dependency.

Releases: https://github.com/Up-Coast/coast-standards/releases
Installer: `enforcement/adopt.py` inside any release.

## Steps

1. **Get the newest release into the cache.** One command; it reads the newest tag
   from the releases page, fetches that release, and leaves it at
   `~/.cache/coast-standards/<version>/`:

   ```bash
   v=$(curl -fsSL https://api.github.com/repos/Up-Coast/coast-standards/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))') && mkdir -p ~/.cache/coast-standards && curl -fsSL "https://github.com/Up-Coast/coast-standards/archive/refs/tags/v$v.tar.gz" | tar xz -C ~/.cache/coast-standards && rm -rf ~/.cache/coast-standards/"$v" && mv ~/.cache/coast-standards/coast-standards-"$v" ~/.cache/coast-standards/"$v" && echo "Coast Standards $v is at ~/.cache/coast-standards/$v"
   ```

   Use the printed version in the paths below. A copy that is already in the cache
   can fetch any other release itself: `adopt.py <project> --release <version>`.

2. **Dry run first, and show the user the list.** Nothing is written:

   ```bash
   python3 ~/.cache/coast-standards/$v/enforcement/adopt.py <project> --dry-run
   ```

3. **Ask the few real questions before writing**, each as a recommended default the
   user can veto. Do not ask what the dry run already answered.
   - The platform, only if the installer could not tell (`--platform ios|macos|android|react-native|web|python`).
   - Where the theme file (colours, fonts, spacing) lives, if the dry run did not find one.
   - The name to record on the starting lines (`--by`), if the git user name is not the right one.
   - Any check the project cannot run on this machine yet (a build that needs secrets, for
     example). That becomes a dated skip in `.coast/rules-exceptions.json`, never a
     permanent switch.

4. **Install**, then commit what it wrote and push. The first push runs every check.

   ```bash
   python3 ~/.cache/coast-standards/$v/enforcement/adopt.py <project>
   ```

5. **Tell the user what changed** in plain words: the files added, the rules-enforced
   number the installer printed, the starting lines and their 90-day date, and the
   version now recorded in `.coast/standards-version`.

## Upgrading

Run the same installer with a newer release. It replaces its own files, keeps anything
the project edited, and lowers a starting-line count that has fallen:

```bash
python3 ~/.cache/coast-standards/<any version>/enforcement/adopt.py <project> --release <new version>
```

## Rules for the agent

- Never edit `Scripts/checks/`, `.githooks/`, `.claude/settings.json` or the rules
  document by hand; they are the project's governed files. Change them by upgrading.
- Never pass `--no-verify`. When a check stops you, read `docs/when-a-check-stops-you.md`
  in the release, or the refusal line itself: it names the rule and the door.
