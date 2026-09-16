# Changelog

What changes for a project that upgrades, one section per release. The version number is in `CHECKS-VERSION`, and each release is the git tag `v<version>`. How to write an entry: [Cutting a release](enforcement/DEVELOPER-GUIDE.md#121-cutting-a-release).

## Unreleased

### Added

- **Writing guides for AI agents.** The installer adds two Claude Code skills to `.claude/skills/`: `write-developer-documentation` and `write-a-guide`. Agents follow them when they write documentation, and the `CLAUDE.md` block points to them. They are guidance, not checks. Switch either off with `writing_guides.off` in `.coast/config.json` if your project already has documentation instructions.
- **Sections shared by several platforms are written once.** They live in `rules/platform/shared/`, and `tools/build_rules.py` fills them into each platform file. A test refuses a platform file that no longer matches, and a section copied by hand into two files.

### Changed

- **The documentation is shorter and easier to follow.** The README, the guides and the rule documents were rewritten in plain words, with steps, tables and one line per paragraph. No rule changed what it requires.
- **The rule documents are at rules version 9.** Re-running `adopt.py` replaces a project's `docs/domain-rules.md` with the new wording and saves the old copy as `docs/domain-rules.v8.md`, so any edits you made are still there to copy across.

### Fixed

- **The installer reports the right standards version from a git worktree.** It used to treat a worktree as a downloaded release.
- **`adopt.py --release` works from a git worktree of the standards repo.** It used to install from the worktree's own files instead of downloading the requested release, because it only recognised a checkout whose `.git` is a folder.

### Upgrading

Re-run `adopt.py <project>`. It replaces your `docs/domain-rules.md` with the rules version 9 wording and saves the old copy as `docs/domain-rules.v8.md`. To keep your own documentation instructions, add both writing guide names to `writing_guides.off` in `.coast/config.json` before you re-run it.

## 1.5.0 — 2026-09-16

The pre-push hook stops a hanging test run, and a new installer option updates the baseline files after a count goes down.

### Added

- **`adopt.py <project> --lower-baselines` updates the baseline files after a count goes down.** When a count of existing problems goes down, the push is refused until the baseline file matches, and agents are not allowed to edit that file. This option updates only the two baseline files, only ever lowers a number, and installs nothing else, so an agent can run it. The refusal message now names this command.

### Changed

- **The pre-push hook now stops test runs that take longer than 15 minutes.** A hanging test used to block the push forever with no message. The hook now stops the run, refuses the push, and says a test is hanging. Set `tests_deadline_seconds` in `.coast/config.json` to allow longer runs.
- **Log files are no longer checked for duplicate code.** Saved build logs were reported as copied code and blocked pushes. Files ending in `.log` are now skipped.

### Upgrading

Re-run `adopt.py <project>`. No other changes are needed.

## 1.4.0 — 2026-09-15

The scanner refuses a screen or component that no part of the app displays.

### Added

- **New check: every public view or component must be used somewhere in the app.** A view that is only shown in a debug gallery, a preview, a storybook or a test is refused at push. This catches screens that were built and tested but never connected. A view behind a feature flag counts as used. To defer one on purpose, add `not-mounted-yet: <the task that will add it>` in the comment above its declaration. Applies to SwiftUI views, Jetpack Compose screens and exported React components.
- **New path class `gallery`** for component catalogues, previews and storybooks. The user-facing text check no longer flags labels in those files. A project can change which paths it covers in `.coast/paths.json`.
- **Rule: every failure path has a test.** Each outcome a model, network call or file read can return needs a test of what the person sees and can do next.
- **Rule: a screen task is done only when it works in the built app.** The builder uses the screen in the running product, including the window, title, settings, navigation and relaunch, and saves screenshots.

### Upgrading

Re-run `adopt.py <project>`. The new check may refuse views that nothing displays. Connect each one, or mark it `not-mounted-yet`.

## 1.3.0 — 2026-09-09

The pre-push hook checks only what a push changed on every platform, not just Swift.

### Changed

- **Android pushes build and test only the affected Gradle modules.** The hook reads the modules from `settings.gradle` or `settings.gradle.kts` and their `project(':x')` dependencies.
- **Web pushes test only the affected npm workspaces.** The hook reads the workspaces from the root `package.json` and runs `npm test -w` for each affected one.
- **Web pushes with Jest or Vitest run only the related tests.** The hook passes the changed files to `jest --findRelatedTests` or `vitest related`, with or without workspaces.
- **Python pushes run only the test files that import the changed code.** The hook follows imports through the project, including the `src` layout and relative imports, and says so when no test is affected.
- **ktlint checks only the changed files**, like the other formatters.

`tsc`, `mypy`, `npm run build` and `detekt` still run on the whole project when code changed.

### Upgrading

Re-run `adopt.py <project>`. No other changes are needed.

## 1.2.0 — 2026-09-09

The pre-push hook checks only what a push changed.

### Changed

- **A push that changes only documents skips the code checks.** Documentation, plans and other text files skip the build, tests, linter, formatter, whole-project scan and duplicate-code check, so the push takes seconds. The scanner still reads the added lines, and the protected-branch check still runs.
- **A push that changes code checks only that code.** The linter and formatter check the changed files. On a Swift package, the build and tests cover the changed targets and every target that depends on them. A change to the checks, a linter config, a baseline or `Package.swift` runs everything. Set `COAST_SCOPE=all` to always run everything, for example in CI. Xcode projects still build and test the whole project.
- **Baselines for warnings, lint and formatting findings now count per file.** A push that checks only some files is compared against those files' counts, and a new finding names its file.

### Upgrading

Run `adopt.py <project> --measure-tools` once to record the per-file counts. Until you do, those checks run on the whole project. Re-measuring never raises a count.

## 1.1.1 — 2026-09-08

Python projects can complete their first push.

### Fixed

- **The Python linters no longer report the standards' own files.** The seeded `ruff.toml` and `mypy.ini` checked the `.coast/` folder, so a first push could not pass. The seeds and the pre-push hook now skip that folder.
- **The layering check works on Python projects.** It used to stop the push with "unknown platform". It now treats a package's subpackages as modules, and matches module names without regard to case.

### Changed

- **Linter seeds can use layout values**, such as `{state_dir}`, so they match a project that moves the `.coast/` folder.

### Upgrading

Re-run `adopt.py <project>`. If you edited `ruff.toml` or `mypy.ini`, the installer leaves them alone. Add `extend-exclude = [".coast"]` to `ruff.toml` and `exclude = ^\.coast/` to `mypy.ini` yourself.

## 1.1.0 — 2026-09-08

A settings file for turning checks off, and one folder for everything the standards install.

### Added

- **A settings file, `.coast/config.json`.** The first install at a terminal asks once which rules, pre-push checks and session hooks to switch off. Everything is on by default. `--yes` skips the questions and `--init` asks them again. A setting can lower a check's severity but never raise it. See the [settings reference](https://github.com/Up-Coast/coast-standards/blob/main/docs/options.md).
- **`--owner`, `--product` and `--org`** put names into every refusal message and the `CLAUDE.md` block.
- **The rule count reports switched-off rules.** A rule whose checks are all switched off is no longer counted as enforced, for example "enforced by a check 24 of 74 (3 switched off)".

### Changed

- **Everything installs under `.coast/`.** The checks moved from `Scripts/` to `.coast/checks/`, and the Claude Code session hook to `.coast/hooks/claude-hook.py`. This avoids a clash with an existing `scripts/` folder on a Mac.

### Upgrading

Re-run `adopt.py <project>`. It moves the files, removes the old copies, and updates `CLAUDE.md`, `.claude/settings.json` and the git hooks.

## 1.0.0 — 2026-09-07

The first public release, under the Coast Standards License. The code is source-available: you may use and share it unchanged, but not resell it or build products from it. See [LICENSE.md](https://github.com/Up-Coast/coast-standards/blob/main/LICENSE.md).

### Added

- **Rules** for iOS, macOS, Android, React Native, Web and Python backends, plus rules for AI features. Each rule names the check that enforces it.
- **Checks:** the rules scanner, doc-comment check, module-layering check, type-size warning, blocking-call check, duplicate-code check (jscpd 5.1.2), secret scan, and linter configs.
- **Git hooks:** `pre-commit`, `commit-msg` and `pre-push`.
- **Claude Code session hooks** that refuse edits to the check files, infrastructure commands, `--no-verify` and force pushes, and that scan every edited file.
- **The installer, `adopt.py`,** which installs everything with one command and updates in place. It records existing problems as baselines with a 90-day deadline, and can download a release itself with `--release <version>` or `--release latest`.
