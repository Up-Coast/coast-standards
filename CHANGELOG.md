# Changelog

What changes for a project that upgrades, one section per version. Every merge to `main` is a new version: the number is in `CHECKS-VERSION`, and each version is the git tag `v<version>` and a GitHub release with this section as its notes. How to write an entry: [Every merge raises the version](enforcement/DEVELOPER-GUIDE.md#121-every-merge-raises-the-version).

## Unreleased

## 1.16.0 — 2026-10-24

Three checks for Apple projects: catalog strings and view model ownership.

### Added

- Three checks for Apple projects: `format-on-catalog-string` refuses `String(format:)` filled from a catalog string, `view-model-in-presentation` refuses an observable view model built inside a `.sheet`, `.fullScreenCover`, `.popover` or navigation destination, and `view-model-in-let` refuses a view that builds its own view model into a `let` or plain `var` instead of `@State`; each would otherwise wait for a reviewer to find a sentence the catalog cannot translate or a model that loses its state.

## 1.15.0 — 2026-10-21

The pre-push hook runs the test seats last

### Changed

- The pre-push hook runs the test seats last. Every other check, the project's own earlier hook included, runs first, so a quick check never refuses a push after a long test run. The earlier hook sees `COAST_GATE=1` and can leave the tests to the gate.

## 1.14.0 — 2026-10-21

The duplicate-code check runs on every push; rule 1 spells out the DRY steps

### Changed

- The duplicate-code check (`jscpd`) now runs on every push, work branches included; only the build, the tests and the doc-comment count are held for the push to the default branch. A copied block now stops the push of the session that wrote it, instead of surfacing for the first time at the integration push.
- Priority rule 1 (DRY) now states the steps: search for existing code before writing, reuse it or extract the shared piece, never copy and edit, and run the duplicate-code check before calling work done.

## 1.13.0 — 2026-10-21

Rules for running background agents: two at a time, own worktrees, one integrator.

### Added

- Rules for running background agents (`rules/06-testing.md`, `rules/07-documentation-git-process.md`): at most two at once and one when free memory is low; a builder tests only what it changed; each agent works in its own worktree, commits locally and never pushes, deploys or migrates; one integrator runs one type check, one full suite, one deploy, one migration, one merge to main and one push; a worktree is removed as soon as its branch is merged.

## 1.12.4 — 2026-10-14

The duplicate-code check skips database migrations.

### Changed

- `jscpd` no longer reads any `migrations` folder (`**/migrations/**` in the layout's ignore list). An applied migration is frozen, and a migration that changes a database function restates the whole function, so a copy there is required and can never be extracted. Before, every such migration added clones that blocked the push to the default branch until the baseline was raised. Application code, tests and scripts are still checked. An upgraded project's clone count falls: lower the baseline with `adopt.py <project> --lower-baselines`.

## 1.12.3 — 2026-10-14

The unreached-view check knows web file-based routing, and the second-theme-file check needs styling content as well as a theme file name.

### Fixed

- `scan:unreached-view` on the web platform now knows file-based routing (issue #2). A file named `page`, `layout`, `template`, `error`, `not-found`, `loading`, `global-error` or `route` under `app/` or `src/app/`, a Pages Router file, a Remix or React Router route module and a Vite `main`/`index` entry are routes; the check follows their imports (relative, the `@/` alias, re-exports) and treats every view on that graph as reached. A view in a file no route reaches is still reported, and `not-mounted-yet:` still suppresses.
- `scan:second-theme-file` on the web and react-native platforms no longer refuses a file only for its name. A `tokens.ts`, `theme.ts` and the like is a theme file only when it holds styling: a hex colour, a `px` or `rem` value, a font family or a `--css-variable` declaration.

## 1.12.2 — 2026-10-13

The doc-comments check reads four Swift declaration shapes it used to miss.

### Fixed

- The `doc-comments` check now reads four Swift declaration shapes it used to miss, matching the compiler's own parser: a multi-name binding (`public var x, y: T` is two declarations), a backticked name (`default`), a type header wrapped onto a second line (the body is still opened), and a dotted extension name (`extension A.B` is `A.B`, not `A`). An upgraded project may see new missing-doc-comment findings.

## 1.12.1 — 2026-10-13

Every rule file is rewritten to be short: one sentence per rule, with every id, check and requirement kept.

### Changed

- **Every rule file is rewritten to be short enough for an agent to hold.** Each rule is now one imperative sentence and its check tag, with a reason only where it is not obvious. Origin stories, dates, quotes and examples that restate a rule are gone; every rule id, check tag and requirement is kept.
- **The rules say which files an agent holds and which it looks up.** `00-priority-rules.md` and the platform file (`docs/domain-rules.md` in a project) are always loaded. Every other numbered file, `PROJECT-TYPES.md` and `types/` opens with a "Read this when …" line, and the CLAUDE.md block the installer writes says the same.
- **Check tags no longer carry a source name.** A tag now reads `[check: review]`. The guides the rules are drawn from are listed once, under Sources in [rules/README.md](https://github.com/Up-Coast/coast-standards/blob/main/rules/README.md).
- **Each rule file's size, in bytes, before and after this release:**

| File | Before | After |
|---|---|---|
| `rules/00-priority-rules.md` | 10,109 | 3,645 |
| `rules/01-working-style.md` | 5,396 | 2,698 |
| `rules/02-architecture-and-code.md` | 8,936 | 4,234 |
| `rules/03-security-owasp.md` | 6,616 | 3,377 |
| `rules/04-localization.md` | 2,172 | 982 |
| `rules/05-design-and-ui.md` | 5,444 | 2,631 |
| `rules/06-testing.md` | 17,023 | 8,432 |
| `rules/07-documentation-git-process.md` | 12,970 | 6,530 |
| `rules/08-auditing-and-completeness.md` | 12,321 | 5,716 |
| `rules/09-models-and-agents.md` | 3,022 | 1,400 |
| `rules/10-development-environment.md` | 2,158 | 991 |
| `rules/PROJECT-TYPES.md` | 5,048 | 2,390 |
| `rules/types/backend-service.md` | 4,543 | 2,147 |
| `rules/types/data-and-ml.md` | 4,681 | 2,251 |
| `rules/platform/domain-rules-ios.md` | 24,338 | 12,200 |
| `rules/platform/domain-rules-macos.md` | 26,551 | 13,408 |
| `rules/platform/domain-rules-android.md` | 24,351 | 12,600 |
| `rules/platform/domain-rules-react-native.md` | 24,730 | 13,089 |
| `rules/platform/domain-rules-web.md` | 23,101 | 13,231 |
| `rules/platform/domain-rules-python.md` | 14,948 | 9,646 |
| `rules/platform/ai-features.md` | 12,532 | 6,190 |
| `rules/platform/shared/*.md` (12 files) | 17,474 | 8,894 |

### Removed

- **Five rules that repeated another rule in the same file are merged into it.** In `05-design-and-ui.md`, "Status and colour, concretely" is part of "Color is never the only signal". In `07-documentation-git-process.md`, "Secret-scan before a first push" is part of "Repos are private in the owner's organization", "Hosted CI is optional" is part of "CI confirms; it never discovers", "Every change updates the documents that describe it" is part of "Docs ship WITH the feature, not after", and "Documents are created only in defined types" is part of "One predictably-named document per subject". Each kept rule carries the merged rule's checks.

### Upgrading

Re-run `adopt.py <project>`. It replaces `docs/domain-rules.md` with the shorter file; an edited copy is kept as `docs/domain-rules.v<release>.md`, so copy your own rules across from it.

## 1.12.0 — 2026-10-13

A new priority rule, fix the class and not the instance, and DRY-5 now covers routing.

### Added

- **A new priority rule: fix the class, not the instance.** A defect report names one place, but the defect is rarely only there. The agent now searches for every other place with the same shape, fixes them through one shared piece of code, checks the error, cancel, keyboard and cold-load paths together with the success path, and adds a guard. A second rejection of the same area is an architecture task, not another patch.

### Changed

- **DRY-5 now names routing.** One module decides where a screen, overlay or action goes next, including Back, Close, Cancel and the error path, and a screen never names its own destinations. Error and after-save paths are listed as shared behaviour. The change is in the web, iOS, Android, macOS and React Native rules documents.

### Upgrading

Re-run `adopt.py <project>`. No other changes are needed.

## 1.11.0 — 2026-10-13

The commit-msg hook no longer asks for a model trailer.

### Removed

- **The commit-msg hook no longer asks for a model trailer.** A commit from an agent session used to be refused unless it ended with a `Co-Authored-By: Claude <model>` line; the rule and its check are gone, and no attribution line is asked of any commit. The hook still refuses a missing subject or one over 100 characters. An `attribution-trailer` entry left in `session_hooks.off` does nothing and can be deleted.

### Upgrading

Re-run `adopt.py <project>`. No other changes are needed.

## 1.10.1 — 2026-10-12

The shipped SwiftLint configuration no longer asks for the opposite of the formatter.

### Changed

- **The brace of a multi-line condition, signature or type header follows the formatter.** swift-format writes that opening brace on its own line; SwiftLint's default `opening_brace` rule refuses exactly that, so no edit satisfied both checks and an agent used all its tries. `enforcement/lint/swiftlint.yml` now sets `ignore_multiline_statement_conditions`, `ignore_multiline_function_signatures` and `ignore_multiline_type_headers`, so the formatter owns line layout.

### Upgrading

Copy the `opening_brace:` block from `enforcement/lint/swiftlint.yml` into your project's `.swiftlint.yml`; the file is yours to edit, so `adopt.py` does not overwrite it.

## 1.10.0 — 2026-10-02

A push of work branches runs only the fast checks; the full battery waits for the push to main.

### Changed

- **A push of work branches runs only the fast checks.** When a push names no default branch and no tag, the build, the tests, jscpd and the doc-comment count print `HELD for the push to main` and do not run. The rules scan, lint, format and gh-ruleset still run. A push that includes the default branch runs everything and checks every commit it brings in, so nothing reaches it untested. Work can now be pushed every time it is committed, and sessions sharing one checkout no longer queue behind each other's full test runs.

### Upgrading

Re-run `adopt.py <project>` to take the new pre-push hook and the updated project CLAUDE.md section.

## 1.9.9 — 2026-10-02

After a failure, re-run only what failed.

### Changed

- **Testing cadence: re-run only what failed.** When a run has passed everything except some tests, the next run is those tests plus the tests for code changed since, never the whole set again. A push or merge gate records which tests passed and failed on which commit and runs only the fast checks, last time's failures and the tests touched since the last passing run; it may never skip a test that failed last time. The full suite runs once per integration, not per feature or per push (`rules/06-testing.md`, Cadence).
- **Parallel sessions do not share one mutable test database without coordination.** A migration applied to a shared test database before its branch merges breaks other sessions' tests; give each stream its own test data or schema where practical, or sequence full runs and record which unmerged migrations are on it.

### Upgrading

Nothing to re-run. A project whose push gate re-runs whole test sets on every push should change the gate to match.

## 1.9.8 — 2026-09-20

README says who makes this and links the free course

### Changed

- **The README says who makes Coast Standards and links the free course.** A short "About Up Coast"
  section at the foot, next to the licence: what the free six-week app strategy course is and who it
  is for. Nothing about the rules or the checks changed, so a project on any version is unaffected.

## 1.9.7 — 2026-09-18

The guide-writing skill loads for guides only.

### Changed

- **`write-a-guide` no longer loads for every request that says "document".** Its description now says to judge by what the document is for. Requirements, specs and briefs written for another agent, plans, task lists, decision records, findings and audits are named as not guides, and "when in doubt, load it" is gone. A brief for an agent is written in the form that agent works from.

### Upgrading

Re-run `adopt.py <project>` to take the updated skill. Nothing else changes.

## 1.9.6 — 2026-09-17

The test time limit's kill reaches every helper on a shell without job control.

### Fixed

- **The test time limit's kill now reaches every helper on a shell without job control too.** On a `sh` that cannot give the run its own process group (dash, as on Debian and Ubuntu), the kill listed the processes under the runner wrongly and a helper could survive the push's refusal, holding its output open. The list is now taken once, correctly, and the same list gets TERM and then KILL.

### Upgrading

Re-run `adopt.py <project>`. No other changes are needed.

## 1.9.5 — 2026-09-17

The test time limit holds under load, and parallel work streams share their pieces first.

### Added

- **Parallel work streams that build the same kind of thing do not run at once.** One lands on main before the next is cut, or the shared pieces are committed first in a small serial commit both streams cut from and each stream's brief names them. The duplicate-code check measures one branch, so copies made on two branches only show at the merge: the merge of parallel streams is measured over the merged tree before it reaches main, and a plan that fans out carries a named "shared pieces first" step. Rule 06, Cadence.

### Fixed

- **The pre-push hook's test time limit now holds under load and kills every helper.** The limit is read from the clock, not counted in one-second sleeps, so a machine busy enough to starve the hook no longer stretches it. The test run is its own process group and is stopped children first, TERM then KILL, so a helper that ignores the first signal or outlives its runner cannot keep the push open. Ctrl-C on the hook stops the run too.

### Upgrading

Re-run `adopt.py <project>`. No other changes are needed.

## 1.9.4 — 2026-09-18

Hosted CI is optional, and its cost is part of the decision.

### Added

- **Hosted CI is optional, and never the only place a check runs.** The local pre-push hook is the gate; hosted CI repeats it for confirmation. A project that runs no hosted CI at all is compliant, as long as the hook runs the same checks.
- **Know what a hosted run costs before scheduling one.** Hosted minutes are usually one allowance shared across every private repository an owner has, and a macOS runner spends it about ten times faster than a Linux one. When the allowance runs out, every workflow in every private repository stops starting — so one project's untrimmed CI takes every other project's checks down with it. Run on the smallest runner that works, cancel superseded runs, skip runs for changes that cannot break the build, and prefer the local hook. A tool that ships workflows does not install them without being asked.

### Upgrading

Nothing to install. If a project runs hosted CI on a shared allowance, check its triggers: a full suite on every push, and any schedule measured in minutes, are the two that empty an allowance without anyone noticing.

## 1.9.3 — 2026-09-17

The writing guides name the model they are tuned for.

### Changed

- **The writing guides name the model they are tuned for.** `write-a-guide` and `write-developer-documentation` are tuned for Opus 5 at medium effort. An agent that loads either one now tells the person it works for which model and effort level it is running on, so they can switch models when it differs.

### Upgrading

Re-run the installer with `--release latest` to take the updated guides. Nothing else changes.

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
