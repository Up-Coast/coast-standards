# Quickstart

*Last updated: 2026-09-07*

Ten minutes from an existing project to live checks.

## 1. Get the newest release

One command. It reads the newest version from the releases page, fetches that release,
and leaves it at `~/.cache/coast-standards/<version>/`. No clone is needed.

```bash
v=$(curl -fsSL https://api.github.com/repos/Up-Coast/coast-standards/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))') && mkdir -p ~/.cache/coast-standards && curl -fsSL "https://github.com/Up-Coast/coast-standards/archive/refs/tags/v$v.tar.gz" | tar xz -C ~/.cache/coast-standards && rm -rf ~/.cache/coast-standards/"$v" && mv ~/.cache/coast-standards/coast-standards-"$v" ~/.cache/coast-standards/"$v" && echo "Coast Standards $v is at ~/.cache/coast-standards/$v"
```

The last line prints the version. The commands below use `$v` from the same shell.
(Contributors who want to change the rules or the checks clone the repository instead;
see [CONTRIBUTING.md](../CONTRIBUTING.md).)

## 2. See what would change

Nothing is written yet. This prints a list of every file the installer would add or
replace in your project.

```bash
python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project --dry-run
```

The installer works out your platform from your project files. If it cannot, add
`--platform ios` (or `macos`, `android`, `react-native`, `web`, `python`).

## 3. Install

```bash
python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project
```

This takes a few minutes on a first run because it builds your project once to measure
where it stands today. It:

- adds the checks and the git hooks to your project
- adds a linter configuration for your platform, if you did not have one
- adds a copy of the rules for your platform at `docs/domain-rules.md`
- records the current state of your code as a starting line (more on this below)
- writes a short block into your `CLAUDE.md` so AI coding agents know the rules
- records the version it installed in `.coast/standards-version`
- scans every file for secrets and stops if it finds any

Its last line says which version your project now carries.

## 4. Commit and push

```bash
git add -A
git commit -m "Adopt Coast Standards"
git push
```

The first push runs every check. It should pass, because anything your project was
already doing wrong has been recorded as a starting line rather than treated as new.

## What "starting line" means

An existing project usually has warnings, style findings, and a few duplicated blocks
already. Rather than demand you fix all of them before the first push, the installer
counts them and writes the counts down with a date 90 days out. From then on the counts
may go down but never up. After the 90 days, the counts must be zero.

## Updating later

Your project holds its own copy of the checks, like a dependency, and the copy you
installed from can fetch any other release itself:

```bash
python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project --release latest
```

Name a version instead of `latest` to take that one (`--release 1.1.0`). The installer
downloads the release into the cache and runs it. It replaces its own files, leaves
anything you edited alone, and lowers any starting-line count that has fallen. Then
commit and push.

## For AI coding agents

If you would rather have an agent do the install, copy the folder
`skills/adopt-coast-standards/` from any release into `~/.claude/skills/` (for every
project) or into your project's `.claude/skills/`. The skill holds only where the
releases are and the commands above, and tells the agent to dry-run and ask you the few
real questions first. The rules themselves never live in the skill; they live in your
project's copy. See [Working with AI coding agents](ai-agents.md).

## Next

- [How it works](how-it-works.md) for what runs and when
- [Options](options.md) if the defaults do not fit your project
