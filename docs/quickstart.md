# Quickstart

*Last updated: 2026-09-16*

About ten minutes from an existing project to live checks. You need macOS or Linux, `git`, and Python 3.10 or newer.

## 1. Install the programs the checks run

The checks use your platform's own linter, formatter and test runner. Install them first, so your first push is not refused for a missing program.

| Your project | Install |
|---|---|
| iOS, macOS | Xcode, then `brew install swiftlint swift-format` |
| Android | `brew install ktlint` (detekt comes through the Gradle plugin) |
| React Native, web | `npm install` in the project (`tsc`, `eslint` and `prettier` run from its `node_modules`) |
| Python | `pip install ruff mypy pytest` (without `pytest`, the tests fall back to `unittest`) |
| Every project | `npm install -g jscpd@5.1.2` (the duplicate-code check) |

`gh` (`brew install gh`) is optional. Without it, the branch-protection check is skipped, not failed. Pinned versions are in [enforcement/TOOLCHAIN.md](../enforcement/TOOLCHAIN.md).

## 2. Get the newest release

This command downloads the newest release to `~/.cache/coast-standards/<version>/` and sets `$v` to the version. No clone is needed.

```bash
v=$(curl -fsSL https://api.github.com/repos/Up-Coast/coast-standards/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))') && mkdir -p ~/.cache/coast-standards && curl -fsSL "https://github.com/Up-Coast/coast-standards/archive/refs/tags/v$v.tar.gz" | tar xz -C ~/.cache/coast-standards && rm -rf ~/.cache/coast-standards/"$v" && mv ~/.cache/coast-standards/coast-standards-"$v" ~/.cache/coast-standards/"$v" && echo "Coast Standards $v is at ~/.cache/coast-standards/$v"
```

Run the next steps in the same shell, so `$v` is still set. To change the rules or checks themselves, clone the repository instead; see [CONTRIBUTING.md](../CONTRIBUTING.md).

## 3. Preview the changes

This lists every file the installer would add or replace. It writes nothing.

```bash
python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project --dry-run
```

If the installer cannot tell your platform, add `--platform` with `ios`, `macos`, `android`, `react-native`, `web` or `python`.

## 4. Install

```bash
python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project
```

1. Answer the on/off questions, or press Enter to keep everything on. They appear once, at a terminal. Add `--yes` to skip them.
2. Wait a few minutes. A first install builds your project once to measure where it stands.
3. Check the last line. It prints the version your project now carries.

The installer stops if it finds a secret in any tracked file.

What it adds:

| Where | What |
|---|---|
| `.coast/checks/` | The checks |
| `.githooks/` | The git hooks (`pre-commit`, `commit-msg`, `pre-push`) |
| `.coast/hooks/`, `.claude/settings.json` | Guard-rails for AI coding agents |
| `.coast/config.json` | Your settings (see [Options](options.md)) |
| `.coast/ratchet-baseline.json`, `.coast/jscpd-baseline.json` | Baselines (see below) |
| `.coast/standards-version` | The installed version |
| `docs/domain-rules.md` | The rules for your platform, if you had no copy |
| Linter config | For your platform, if you had none |
| `CLAUDE.md` | A short block so AI agents know the rules |

## 5. Commit and push

```bash
git add -A
git commit -m "Adopt Coast Standards"
git push
```

The first push runs every check. It should pass, because existing problems were recorded as baselines.

## What a baseline is

Most existing projects already have warnings, style findings and some duplicated code. The installer counts them and records each count with a deadline 90 days out.

- A count may go down, never up.
- After the deadline, the count must be zero.

## Updating later

```bash
python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project --release latest
```

Use a version number instead of `latest` to take a specific release, for example `--release 1.2.0`. The installer replaces its own files, keeps files you edited, and lowers any baseline count that fell. Then commit and push.

## For AI coding agents

To have an agent do the install, copy `skills/adopt-coast-standards/` from any release into `~/.claude/skills/` (all projects) or your project's `.claude/skills/`. The skill tells the agent where the releases are and to dry-run and ask you first. See [Working with AI coding agents](ai-agents.md).

## Next

- [Options](options.md): every setting, installer flag and file.
- [How it works](how-it-works.md): what runs, and when.
- [When a check stops you](when-a-check-stops-you.md): what to do after a refusal.
