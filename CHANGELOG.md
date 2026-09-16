# Changelog

What changes for a project that upgrades, one section per version. Every merge to `main` is a new version: the number is in `CHECKS-VERSION`, and each version is the git tag `v<version>` and a GitHub release with this section as its notes. How to write an entry: [Every merge raises the version](enforcement/DEVELOPER-GUIDE.md#121-every-merge-raises-the-version).

## Unreleased

## 1.9.2 — 2026-09-16

Every version is published as a GitHub release.

### Changed

- **Every version is published as a GitHub release.** CI now publishes a release for each merge to main, with the version's changelog section as its notes, so `adopt.py --release latest` always installs the newest version. The release workflow stays for publishing a version that is missing from the releases page.

### Upgrading

Nothing to do. `--release latest` now follows every version.

## 1.9.1 — 2026-09-16

A rewritten introduction in the README.

### Changed

- **The README's introduction is rewritten.** It explains why this project exists and how it is meant to be used.

### Upgrading

Nothing to do.

## 1.9.0 — 2026-09-16

A rule that testing leaves no mess in anyone's inbox.

### Added

- **Rule: testing leaves no mess in anyone's inbox.** Work that sends email or notifications uses test-only addresses that a filter removes on arrival, and trashes anything that got past the filter when it ends. A scheduled job that fails on every run is a defect to fix or switch off, not noise to filter. The rule is in `rules/06-testing.md`.

### Upgrading

Nothing to do. The numbered rules are read in place from the standards repo, so reviews apply the new rule from this version on.

## 1.8.0 — 2026-09-16

Rules for keeping documentation current, and a test that holds the settings reference to the code.

### Added

- **Rule: every change updates the documents that describe it.** A change to a behaviour, command, flag, setting, file location or message updates the README, guides, settings references, troubleshooting pages, diagrams and changelog in the same change. The rule is in `rules/07-documentation-git-process.md`.
- **Rule: documents follow the project's writing instructions.** Agents write and update documents by the installed writing guides, or by the project's own instructions when the guides are switched off.
- **The settings reference is checked against the code.** A test fails when an installer flag, a setting, a layout key or a switchable name is missing from `docs/options.md`.

### Fixed

- **The settings reference lists every layout key and the writing-guides question.** `lock_name`, `temp_prefix` and `env_prefix` were missing, and the `--init` description left out the writing guides.

### Upgrading

Nothing to do. The numbered rules are read in place from the standards repo, so reviews apply the new rules from this version on.

## 1.7.0 — 2026-09-16

A rule for versions and build numbers.

### Added

- **Rule: versions and build numbers.** A version names a release and changes only when a release is cut: patch for fixes, minor for new features, major for breaking changes. Every build gets a new, never-reused build number that records its commit. A repository installed straight from git, like this one, raises its version on every merge instead. The rule is in `rules/07-documentation-git-process.md`.

### Upgrading

Nothing to do. The numbered rules are read in place from the standards repo, so reviews apply the new rule from this version on.

## 1.6.3 — 2026-09-16

Every merge to main is a new version, and publishing a release is a separate step.

### Changed

- **Every merge to main is a new version.** `python3 tools/version.py bump patch|minor|major "<summary>"` raises `CHECKS-VERSION`, writes the version's changelog section and stamps the rule files. The pre-push hook refuses a push to main that does not raise the version, and CI tags every version `v<version>` once the checks pass.
- **Publishing a GitHub release is a separate, manual step.** A tag no longer publishes a release. Run the release workflow by hand and name the version. `adopt.py --release <version>` installs any tagged version, and `--release latest` installs the newest published release.

### Upgrading

Nothing to do. Adopted projects are not affected.

## 1.6.2 — 2026-09-16

One version number for everything: the rules files carry the release number.

### Changed

- **The rules files carry the release number instead of a separate rules version.** The first line of each platform rules file now names the release in which its text last changed, for example `<!-- coast-standards-release: 1.6.0 -->`. The installer compares these as release numbers and treats the old `coast-rules-version: 9` stamps as older, so an unchanged project copy is updated without a backup.

### Fixed

- **Python projects now receive rule updates.** The Python rules file had no version stamp, so the installer never upgraded a Python project's copy. An unstamped copy is upgraded while it is still the one the installer wrote.

### Upgrading

Re-run `adopt.py <project>`. Your `docs/domain-rules.md` gets the new first line. If you had edited it, your copy is kept as `docs/domain-rules.v<old stamp>.md`.

## 1.6.1 — 2026-09-16

A wording fix in the `CLAUDE.md` block.

### Fixed

- **The `CLAUDE.md` block starts with a capital letter when no product name is set.** It used to open with "this project follows".

### Upgrading

Re-run `adopt.py <project>`. No other changes are needed.

## 1.6.0 — 2026-09-16

Writing guides for AI agents, clearer documentation, and platform rule sections written once.

### Added

- **Writing guides for AI agents.** The installer adds two Claude Code skills to `.claude/skills/`: `write-developer-documentation` and `write-a-guide`. Agents follow them when they write documentation, and the `CLAUDE.md` block points to them. They are guidance, not checks. Switch either off with `writing_guides.off` in `.coast/config.json` if your project already has documentation instructions.
- **Sections shared by several platforms are written once.** They live in `rules/platform/shared/`, and `tools/build_rules.py` fills them into each platform file. A test refuses a platform file that no longer matches, and a section copied by hand into two files.

### Changed

- **The documentation is shorter and easier to follow.** The README, the guides and the rule documents were rewritten in plain words, with steps, tables and one line per paragraph. No rule changed what it requires.
- **The rule documents are at rules version 9.** Re-running `adopt.py` replaces a project's `docs/domain-rules.md` with the new wording and saves the old copy as `docs/domain-rules.v8.md`, so any edits you made are still there to copy across.

### Fixed

- **The installer works from a git worktree of the standards repo.** It used to treat a worktree as a downloaded release, so `--release` installed the worktree's own files and the recorded version was wrong.

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
