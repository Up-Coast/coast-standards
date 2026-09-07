# Quickstart

Ten minutes from an existing project to live checks.

## 1. Get the standards

```bash
git clone https://github.com/Up-Coast/up-coast-standards.git ~/coast-standards
```

## 2. See what would change

Nothing is written yet. This prints a list of every file the installer would add or
replace in your project.

```bash
python3 ~/coast-standards/enforcement/adopt.py /path/to/your/project --dry-run
```

The installer works out your platform from your project files. If it cannot, add
`--platform ios` (or `macos`, `android`, `react-native`, `web`, `python`).

## 3. Install

```bash
python3 ~/coast-standards/enforcement/adopt.py /path/to/your/project
```

This takes a few minutes on a first run because it builds your project once to measure
where it stands today. It:

- adds the checks and the git hooks to your project
- adds a linter configuration for your platform, if you did not have one
- adds a copy of the rules for your platform at `docs/domain-rules.md`
- records the current state of your code as a starting line (more on this below)
- writes a short block into your `CLAUDE.md` so AI coding agents know the rules
- scans every file for secrets and stops if it finds any

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

So you never have a "rewrite day" forced on you at install, and you cannot quietly sit
on the debt forever either.

## Updating later

Run the same install command again. It replaces its own files, leaves anything you
edited alone, and lowers any starting-line count that has fallen.

## Next

- [How it works](how-it-works.md) for what runs and when
- [Options](options.md) if the defaults do not fit your project
