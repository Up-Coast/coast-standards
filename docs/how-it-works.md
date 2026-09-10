# How it works

*Last updated: 2026-09-07*

## Three moments

The checks run at three moments.

| Moment | What runs | How long |
|---|---|---|
| **Every time a file is saved** by an AI coding agent | the scanner on that one file | under a second |
| **Every commit** | the scanner on the lines you added, and a check that the commit message is sensible | seconds |
| **Every push** | the battery, on what the push changed: build, tests, linter, formatter, the scanner on everything since your last push, duplicate-code detection, and a check that your main branch is protected | seconds for a push of documents; as long as the affected modules' build and tests for a push of code |

A refusal at any moment stays on your machine.

## A push runs what it changed

The push hook reads what the push changed before it runs anything, and answers with one
of three words:

- **none** — only documents, plans or other prose changed. No build, no tests, no linter,
  no formatter, no duplicate-code run: none of them could have an opinion. The scanner
  still reads the added lines, and the protected-main check still runs.
- **files** — code changed. The linter and the formatter read the changed files. On a
  Swift package the build rebuilds the targets that changed and every target that depends
  on them, and the tests run for the test targets that depend on them — the package's
  own graph decides, so a change in a leaf module never runs the whole suite, and a
  change in the module everything imports runs everything. On Android the Gradle modules
  play the same part (each affected module builds and runs its own tests); on the web the
  npm workspaces do, and when the test script is jest or vitest the runner is handed the
  changed files and runs the tests that import them; in Python every file's imports are
  the graph, so a push runs exactly the test files whose imports reach what changed. A
  file no module owns runs the whole battery. An Xcode project has no graph the hook
  reads, so its build and tests run whole when code changed; its linter and formatter are
  still file-scoped. Type checkers (`tsc`, `mypy`) always read the whole program, because
  that is what a type check is.
- **all** — the checks themselves changed (a check, a linter configuration, a baseline,
  the package manifest), or the environment asked for everything (`COAST_SCOPE=all`,
  which CI sets). Everything runs.

The starting lines follow suit. A repository adopted with warnings or findings carries a
count per file beside its total (written by `adopt.py --measure-tools`), so a scoped push
is judged on the files it rebuilt or linted: their count may not rise, and the files it
did not touch keep their numbers. A starting line without the per-file counts runs that
check whole, and says which re-measure enables the scoped run.

## The scanner

Most of the rules are about a literal in the wrong place: a user-facing sentence typed
straight into a screen instead of a strings file, a colour or a font size typed into a
view instead of the theme, a password in code, a plain `http://` address, a `sleep` on
the main thread. The scanner has a list of these patterns for each platform and looks
for them in the lines you added. It knows what kind of file it is looking at (a screen, a
test, the theme, a strings catalog) and applies only the patterns that make sense there.

It does not read your program's structure.

## Your platform's linter

Where the platform already has a good tool (SwiftLint, detekt, ESLint, ruff), the
installer ships a configuration with the rules the standards cite switched on, and the
push runs it. You can edit that configuration; the installer will not overwrite your
edits.

## Duplicate code

`jscpd` finds copied blocks of code across your project. The rule is "no new
duplication": the copies you already had are recorded at install, and a push is refused
only when it adds a new one.

## Three kinds of rule

Every rule is labelled with what holds it, and the label puts it in a bin:

- **Enforced by a check.** A check refuses the change. This is the number you see.
- **Advisory.** The scanner mentions it. Nothing fails.
- **Needs a reviewer.** Only a person (or a review agent reading the code) can judge it:
  naming, whether an abstraction is premature, whether an error message is honest.
  These are listed in your rules file as review-only.

The number "rules enforced by a check: 24 of 74" is computed from your project's own copy
of the rules and written into your `CLAUDE.md`. A rule counts only if the check it names
exists and runs.

## Starting lines and deadlines

An existing project's warnings, style findings, duplicated blocks, and a few scanner
counts are recorded at install with a date 90 days out. Each count may fall or stay flat
and never rise. After the date, the check requires zero. Only a person can move a date,
and the move is written down with who and why.

## Guard-rails for AI agents

If you use Claude Code on the project, a small set of hooks stops an agent from doing
things it should never do on its own: editing the files that define the checks, running
commands that change your cloud infrastructure, skipping the hooks, force-pushing, and
ending its turn with work it has not pushed. See
[Working with AI coding agents](ai-agents.md).

## Where the checks live

In your project. The installer copies the checks, the hooks, and the rules into it, and
records the release in `.coast/standards-version`. Nothing outside the project carries
the rules, and nothing needs to be cloned or kept in step on your machine. A newer release
is taken by running the installer with `--release`.

## What it never does

- It never sends your code anywhere. Everything runs locally.
- It never calls a model. The checks are scripts.
- It never edits your code. It only refuses.
