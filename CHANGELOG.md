# Changelog

*Last updated: 2026-09-08*

What a project that upgrades will notice, one entry per release. The number lives in
`CHECKS-VERSION`; the release is the git tag `v<number>`.

## 1.1.1 — 2026-09-08

A project that runs Python can complete its first push.

- **The linter stops reporting on the layer itself.** The seeded `ruff.toml` and `mypy.ini`
  read the whole tree, so the checks and the session hook — which ship as they are and are
  not the project's code — came back as the project's own findings, and a first push could
  not go green. The seeds now exclude the layer's folder, and the push battery excludes it
  too, so a seat stays right whatever is later edited into a seed. A Swift or Node project
  was never affected: the layer holds no source of their kind.
  *Upgrading:* re-run the installer. A seed you have edited is left alone, as always — so
  add `extend-exclude = [".coast"]` to your `ruff.toml` and `exclude = ^\.coast/` to your
  `mypy.ini` yourself, or the battery will pass while your own `ruff check .` keeps
  reporting the layer.
- **Seeds are rendered, not copied.** A linter seed may name a layout key as `{state_dir}`
  the way the settings file and the governing classes already do, so a project that moves
  the layer's folder gets a seed that matches. The layout table gains `state_dir_regex`
  beside `state_dir`, for a tool whose exclude is a regular expression.
- **The module-layering check reads Python.** `import-matrix` (ARCH-2) knew only the Swift,
  Gradle and Node layouts, so on a Python project it stopped the push with "unknown
  platform" — while the Python rules document promised the check. It now reads a Python
  layout: one package (under `src/`, else the root) makes that package's subpackages the
  modules and its root files the app target; several packages side by side each count as a
  module. A `src.`-prefixed absolute import is tolerated, and module names are matched
  without regard to case, so a lowercase `domain` package is the shared centre the rule
  expects.

## 1.1.0 — 2026-09-08

The switches, the config file, and one folder for the layer.

- **One folder.** The checks and the Claude Code session hook now live under `.coast/`
  (`.coast/checks/`, `.coast/hooks/claude-hook.py`) instead of `Scripts/`. A project that
  already had a `scripts/` folder no longer collides with them on a Mac. Re-running the
  installer moves an existing project over and removes the old copies; the `CLAUDE.md`
  block, `.claude/settings.json` and the hooks are rewritten to the new paths.
- **A config file, asked once.** `.coast/config.json` holds the switches and the names.
  A first install at a terminal asks the on/off questions once — one screen each for the
  rules, the push-gate seats and the session hooks, every default on; `--yes` skips the
  questions, `--init` asks them again. A switched-off rule is not run, a switched-off seat
  prints `gate: <name> OFF (config)`, a switched-off session hook exits with a note, a
  switched-off linter is neither run nor seeded. A severity may be lowered in the config,
  never raised. `retired_words` add to the retired-wording check; `ratchet_days` sets the
  starting-line deadline.
- **The number stays honest.** A rule whose every check is switched off is counted as
  `off`, not enforced: "enforced by a check 24 of 74 (3 switched off)" in the verifier, the
  `CLAUDE.md` block and the session-start line.
- **Names from the config.** `--owner`, `--product` and `--org` fill `owner` in the config;
  every refusal sentence and the `CLAUDE.md` block read them ("ask Pat Lee in one line
  first"), with general words when they are blank. No shipped file carries a name.
- **The block title** now reads "Coast Standards — the standing rules, enforced by machines
  where a machine can hold them".
- **Docs.** The developer guide gains "Configuration" and the layout table; the options
  page gains the switches.

## 1.0.0 — 2026-09-07

The first public release, under the Coast Standards License (source-available: use
and share unchanged, no resale, no derived products; see LICENSE.md).

- **Rules.** Six platform rule documents (iOS, macOS, Android, React Native, Web, Python
  backend) at corpus version 8, plus the AI-features rules; every rule names the check
  that holds it. Rules enforced by a check: 170 of 643 across the corpus.
- **Checks.** The rules scanner with per-platform signature tables, the doc-comment
  check, the import matrix, the type-size advisory, the async-blocking check, the
  duplicate-code seat (jscpd 5.1.2), the secret scan, and the shipped linter configs.
- **Hooks.** `pre-commit`, `commit-msg` and `pre-push` for git; the Claude Code session
  hooks that refuse edits to governed files, infrastructure commands, `--no-verify` and
  force-pushes, and that scan every edited file.
- **Installer.** `adopt.py` installs all of it into a project in one command, records
  starting lines with a 90-day deadline, and upgrades in place. It records the release
  it installed in `.coast/standards-version` and can fetch a named release itself
  (`--release 1.0.0`, or `latest`), so no clone is needed.
- **The `CLAUDE.md` block** is written between `coast-standards: begin` / `end` markers.
  A block written by an earlier private build under the older `up-coast-standards`
  markers is recognised and replaced.
