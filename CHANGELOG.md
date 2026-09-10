# Changelog

*Last updated: 2026-09-09*

What a project that upgrades will notice, one entry per release. The number lives in
`CHECKS-VERSION`; the release is the git tag `v<number>`.

## 1.3.0 — 2026-09-09

Every platform's push runs on what it changed, not only Swift's.

- **Module graphs for Android, the web and Python.** The hook reads the platform's own
  graph: Gradle modules from `settings.gradle[.kts]` and each module's `project(':x')`
  dependencies (a push builds and tests the affected modules, `./gradlew :m:build` /
  `:m:test`); npm workspaces from the root `package.json` (a push tests the affected
  workspaces, `npm test -w`); and for Python every tracked `.py` file with its imports
  resolved to files in the tree, the `src` layout and relative imports included, so a push
  runs exactly the test files whose imports reach what changed, and says so when none do.
- **The runner's own related-tests mode.** When the web test script is `jest` or `vitest`,
  a push hands the changed files to `jest --findRelatedTests` or `vitest related`: the
  tests that import the changed files, transitively, whether or not the project has
  workspaces.
- **ktlint reads the changed files** like the other formatters already did.
- `tsc`, `mypy`, `npm run build` and `detekt` still run whole when code changed: the first
  two are whole-program by nature, the others are not scoped by their tools.



The push battery runs on what the push changed.

- **A push of documents alone runs no code check.** The hook reads what the push changed
  before it runs anything. Documents, plans and other prose (`docs/`, `plans/`, `.md`,
  `.txt` and the like) are not code: the build, the tests, the linter, the formatter, the
  whole-tree scan, the doc-comment count and jscpd all print `SKIPPED — no code changed`
  and the push takes seconds. The scanner still reads the added lines, and the
  protected-main check still runs. Origin: a push that changed one internal note ran the
  whole battery, for a change no check could have an opinion on.
- **A push of code runs the checks on that code.** The linter and the formatter read the
  changed files. On a Swift package, the build rebuilds the targets that changed and every
  target that depends on them, and the tests run for the test targets that depend on them
  (`swift test --filter`), by the package's own graph: a change in a leaf module runs its
  tests alone, and the hook says so when no test target depends on what changed. A file
  no target owns, a change to the checks, a linter configuration, a baseline or the package
  manifest runs everything, as does `COAST_SCOPE=all` in the environment (CI's word).
  An Xcode project has no graph the hook reads yet: its build and tests run whole when
  code changed; its linter and formatter are file-scoped. On the web and Python platforms
  eslint, prettier and ruff read the changed files; the other tools run whole when code
  changed. Module graphs for Gradle, npm workspaces and Python packages are filed (E8.6).
- **The starting lines judge a scoped run by file.** A tool's baseline entry
  (`build-warnings`, `lint-findings`, `format-findings`) now carries a count per file
  beside its total, so a scoped push is held on the files it rebuilt or linted: their
  count may not rise against those same files' baseline, and a rise names the file. Files
  the push did not touch keep their numbers. The seats' counters live in one place now
  (`check_rules.py --ratchet <id> --log <log>`); `--measure` prints the per-file lines the
  installer writes.
  *Upgrading:* re-run the installer with `--measure-tools` once, so the baseline gains
  the per-file counts; until then a scoped push runs those seats whole and prints the
  line that says so. The re-measure never raises a count.
- `rules/07`: "the full gate battery runs before every push" now says what the battery
  runs on. The rule's check is unchanged.

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
