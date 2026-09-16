# How it works

*Last updated: 2026-09-16*

## When the checks run

| When | What runs | How long |
|---|---|---|
| An AI coding agent saves a file | The scanner, on that file | Under a second |
| You commit | The scanner, on the lines you added, and a commit-message check | Seconds |
| You push | The pre-push hook's checks, on what the push changed (see below) | Seconds for documents; the affected build and tests for code |

The pre-push hook runs: build, tests, linter, formatter, the scanner, duplicate-code detection, and a check that your main branch is protected on GitHub.

Everything runs on your machine. A refusal never leaves it.

## A push only checks what it changed

Before running anything, the pre-push hook works out the scope of the push.

| Scope | When | What runs |
|---|---|---|
| **none** | Only documents or other prose changed | The scanner on added lines, and the protected-branch check. No build, tests, linter, formatter or duplicate-code check. |
| **files** | Code changed | The linter and formatter on the changed files. The build and tests for the affected modules (see below). |
| **all** | The checks themselves changed (a check, a linter config, a baseline, the package manifest), or `COAST_SCOPE=all` is set (CI sets it) | Everything. |

How "affected modules" is worked out:

| Platform | Unit | What runs |
|---|---|---|
| Swift package | Package targets | Changed targets, targets that depend on them, and their tests |
| Android | Gradle modules | Each affected module's build and tests |
| Web | npm workspaces | Affected workspaces; jest or vitest run only the tests that import the changed files |
| Python | Imports | Test files whose imports reach the changed code |
| Xcode project | None | Whole build and tests (linter and formatter still run per file) |

- A changed file that belongs to no module runs everything.
- Type checkers (`tsc`, `mypy`) always check the whole program.

## The scanner

Most rules catch a literal in the wrong place. Examples:

- User-facing text typed into a screen instead of a strings file.
- A colour or font size typed into a view instead of the theme.
- A password in code, or a plain `http://` address.
- A `sleep` on the main thread.

The scanner has a list of these patterns per platform. It checks the lines you added. It knows the file's kind (screen, test, theme, strings catalog) and applies only the patterns that fit. It does not analyse program structure.

## Your platform's linter

Where a good linter exists (SwiftLint, detekt, ESLint, ruff), the installer ships a config with the relevant rules on. The pre-push hook runs it. You may edit that config; the installer will not overwrite your edits.

## Duplicate code

`jscpd` finds copied blocks of code. Copies that existed at install are recorded. A push is refused only if it adds a new one.

## Baselines: existing problems in an older project

A baseline is a count of existing problems that may only go down. The installer records one for existing build warnings, linter and formatter findings, duplicated blocks, and some scanner checks.

- Each baseline has a deadline, 90 days after install by default (`ratchet_days`).
- Before the deadline, the count may stay the same or fall, never rise.
- After the deadline, the count must be zero.
- Only a person can move a deadline.

Baselines live in `.coast/ratchet-baseline.json` and `.coast/jscpd-baseline.json`.

Tool baselines (warnings, linter, formatter) can also store a count per file. With those, a scoped push is judged only on the files it rebuilt or linted. Without them, that check runs on the whole project, and the hook tells you which re-measure (`adopt.py --measure-tools`) enables the scoped run.

## How each rule is enforced

Every rule in your `docs/domain-rules.md` is labelled with what enforces it:

| Label | Meaning |
|---|---|
| Enforced by a check | A check refuses the change. |
| Advisory | The scanner reports it. Nothing fails. |
| Needs a reviewer | Only a person or a review agent can judge it (naming, premature abstraction, honest error messages). |
| Process | Held by the workflow or by a person. |
| Switched off | A person turned its check off in `.coast/config.json`. Nothing enforces it until they turn it back on. |

The installer counts the enforced rules (for example "rules enforced by a check: 24 of 74") and writes the number into your `CLAUDE.md`. A rule counts only if the check it names exists and runs.

## Guard-rails for AI agents

If you use Claude Code, session hooks stop an agent from editing the check files, changing cloud infrastructure, skipping hooks, force-pushing, or ending its turn with unpushed commits. See [Working with AI coding agents](ai-agents.md).

## Where the checks live

In your project. The installer copies the checks, hooks and rules into it. It records the installed release in `.coast/standards-version`. Nothing needs to be cloned or kept in sync elsewhere. To upgrade, run the installer with `--release`.

## What it never does

- It never sends your code anywhere.
- It never calls an AI model. The checks are scripts.
- It never edits your code. It only refuses.
