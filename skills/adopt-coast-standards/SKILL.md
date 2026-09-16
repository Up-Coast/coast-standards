---
name: adopt-coast-standards
description: Install or upgrade Coast Standards (engineering rules for AI-built software, plus the checks that enforce them) in the current project. Use when asked to adopt, install, set up or upgrade Coast Standards, or to add coding-standard checks and git hooks to a repository. Fetches a published release; the installer copies the rules and checks into the project.
---

# Adopt Coast Standards

This skill says where the releases are and how to run the installer. The installer copies the rules, checks and hooks into the project. From then on they belong to the project, like any other dependency.

- Releases: https://github.com/Up-Coast/coast-standards/releases
- Installer: `enforcement/adopt.py` inside any release.

## Steps

1. **Download the newest release.** This command finds the newest tag, downloads it, and unpacks it to `~/.cache/coast-standards/<version>/`:

   ```bash
   v=$(curl -fsSL https://api.github.com/repos/Up-Coast/coast-standards/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))') && mkdir -p ~/.cache/coast-standards && curl -fsSL "https://github.com/Up-Coast/coast-standards/archive/refs/tags/v$v.tar.gz" | tar xz -C ~/.cache/coast-standards && rm -rf ~/.cache/coast-standards/"$v" && mv ~/.cache/coast-standards/coast-standards-"$v" ~/.cache/coast-standards/"$v" && echo "Coast Standards $v is at ~/.cache/coast-standards/$v"
   ```

   Use the printed version in the paths below. To get a different release, use a copy already in the cache: `adopt.py <project> --release <version>`.

2. **Do a dry run and show the user the list of files.** Nothing is written.

   ```bash
   python3 ~/.cache/coast-standards/$v/enforcement/adopt.py <project> --dry-run
   ```

3. **Ask the user only what the dry run did not answer.** Phrase each question as a recommended default they can turn down.

   | Question | When to ask | Where the answer goes |
   |---|---|---|
   | Which platform? | The installer could not tell | `--platform ios\|macos\|android\|react-native\|web\|python` |
   | Where is the theme file (colours, fonts, spacing)? | The dry run did not find one | The `theme` entry in `.coast/paths.json` (the user's file to edit) |
   | Whose name goes on the baselines? | The git user name is wrong | `--by <name>` |
   | The owner's name and the product's name | Always | `--owner <name>`, `--product <name>` (used in every refusal message and the `CLAUDE.md` block) |
   | Should any rule, pre-push check or session hook be off? | Always | See below |
   | Is there a check this machine cannot run yet (for example, a build that needs secrets)? | Always | A dated skip in `.coast/rules-exceptions.json`, never a permanent switch-off |

   The installer asks the on/off questions itself when run in a terminal. From an agent session, either:
   - pass `--yes` (everything on), then have the user put their answers in `.coast/config.json`, or
   - have the user run `adopt.py <project> --init` in a terminal themselves.

4. **Install.** Then commit the files it wrote and push. The first push runs every check.

   ```bash
   python3 ~/.cache/coast-standards/$v/enforcement/adopt.py <project>
   ```

5. **Tell the user what changed:**
   - the files added,
   - the "rules enforced by a check" number the installer printed,
   - the baselines (counts of existing problems that may only go down) and their deadline, 90 days out,
   - the version now recorded in `.coast/standards-version`.

## Upgrading

Run the installer again with a newer release:

```bash
python3 ~/.cache/coast-standards/<any version>/enforcement/adopt.py <project> --release <new version>
```

It replaces its own files, keeps anything the project edited, and lowers any baseline count that has gone down.

## Rules for the agent

- **Never edit these by hand:** `.coast/` (the checks, the session hook, the config, the baselines), `.githooks/`, `.claude/settings.json`, or the rules document. They define the project's checks. Change the checks by upgrading.
- **The config and the exceptions file belong to the user.** Tell them what to write; do not write it yourself.
- **Never pass `--no-verify`.** When a check stops you, read the refusal line: it names the rule and what to do. For more, read `docs/when-a-check-stops-you.md` in the release.
