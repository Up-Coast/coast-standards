# Options

*Last updated: 2026-09-16*

Every setting you can change, and where it lives. The installer creates all of these files in a `.coast/` folder in your project.

| File | What it holds | Section |
|---|---|---|
| `.coast/config.json` | Switches and settings | [Settings file](#settings-file) |
| `.coast/rules-exceptions.json` | Temporary excuses for a check | [Exceptions file](#exceptions-file) |
| `.coast/paths.json` | Which of your files are which | [Paths file](#paths-file) |
| `.coast/xcode-scheme` | The Xcode scheme to build | [Other project files](#other-project-files) |
| `.coast/module-kinds.json` | Swift module layering | [Other project files](#other-project-files) |
| `.coast/ratchet-baseline.json`, `.coast/jscpd-baseline.json` | Baseline counts | [Baselines](#baselines) |
| `.coast/standards-version` | The release your project carries | [Versions and releases](#versions-and-releases) |

`.coast/config.json` and `.coast/rules-exceptions.json` define what is enforced. AI agents are refused when they try to edit them, so only a person changes them.

## Installer flags

Run the installer as `python3 <release>/enforcement/adopt.py <project> [flags]`. `<project>` is the project's root folder, which must be a git repository. The installer is safe to run again: it changes nothing when nothing changed.

| Flag | What it does |
|---|---|
| `--platform NAME` | Sets the platform: `ios`, `macos`, `android`, `react-native`, `web` or `python`. Default: the platform recorded in `.coast/platform`, or detected from your project files. |
| `--dry-run` | Prints what would change. Writes nothing. |
| `--init` | Asks the on/off questions again (scanner rules, pre-push steps, session hooks, writing guides) and writes the answers to `.coast/config.json`. A first install at a terminal asks them anyway, once. |
| `--yes` | Takes every default without asking. Everything is on. |
| `--owner NAME` | The owner's name, used in refusal messages ("ask NAME first"). Saved as `owner.name`. |
| `--product NAME` | The product's name. Saved as `owner.product`. |
| `--org NAME` | The organisation's name. Saved as `owner.org`. |
| `--release VERSION` | Downloads that version (for example `1.6.3`, or `latest` for the newest published release) and installs from it instead of from the copy you ran. Use it to update. |
| `--measure-tools [STEPS]` | Measures the tool baselines again: build warnings, formatter findings, linter findings and a missing test target. A first install does this anyway. Add a list to skip work, for example `--measure-tools format,lint` to measure without building. |
| `--lower-baselines` | Writes only the two baseline files, measured from the code as it is now. A count that fell is lowered. A count that rose is left and reported. Nothing is installed. Use it when a push is refused because a count went down. An AI agent may run it, because it can only lower counts. It cannot be combined with `--init`, `--measure-tools` or `--secret-scan`, and the project must already be installed. |
| `--secret-scan` | Scans every tracked file for secrets again. A first install always does this. |
| `--by NAME` | The name recorded on new baselines. Default: your git `user.name`. |
| `--checks-dir PATH` | Installs the checks somewhere other than `.coast/checks/`. Use it when that path clashes with an existing folder, for example `--checks-dir scripts/checks` in a project that has `Scripts/`. Saved under `layout` in the config and used on every later run. |
| `--jscpd-bin PATH` | The `jscpd` program to use. Default: the `JSCPD_BIN` environment variable, then your `PATH`, then `npx --no-install`. |
| `-h`, `--help` | Prints the list of flags. |

## Settings file

`.coast/config.json` holds the switches and settings. The installer writes it on the first install, from your answers or from the defaults. It never rewrites your answers.

Edit the file by hand. The next commit, push or agent action reads it. You do not need to re-run the installer. Any key you leave out keeps its default. A list you write replaces the default list.

Everything is on by default. The defaults look like this:

```json
{
  "version": 1,
  "owner": {"name": "", "product": "", "org": ""},
  "rules": {"off": [], "severity": {}, "retired_words": []},
  "seats": {"off": []},
  "session_hooks": {"off": []},
  "linters": {"off": []},
  "writing_guides": {"off": []},
  "ratchet_days": 90,
  "tests_deadline_seconds": 900,
  "layout": {}
}
```

An example with some changes:

```json
{
  "version": 1,
  "owner": {"name": "Pat Lee", "product": "Example App", "org": ""},
  "rules": {
    "off": ["scrim-modal"],
    "severity": {"inline-comment": "advisory"},
    "retired_words": ["synergy"]
  },
  "seats": {"off": ["gh-ruleset"]},
  "tests_deadline_seconds": 1200
}
```

### All keys

| Key | Type | Default | What it does |
|---|---|---|---|
| `version` | number | `1` | The format of the file. Leave it as it is. |
| `owner.name` | text | `""` | The owner's name in refusal messages and the `CLAUDE.md` block. Blank reads as "the owner". |
| `owner.product` | text | `""` | The product's name. Blank reads as "this project". |
| `owner.org` | text | `""` | The organisation's name. |
| `rules.off` | list of ids | `[]` | Scanner rules that do not run. Use the id from a `FAIL` line (`:scrim-modal:`). |
| `rules.severity` | object of id → level | `{}` | Lowers a scanner rule's level. Levels, highest first: `block` (refuses), `ratchet` (a baseline count that may only go down), `advisory` (reported, never refuses). You can only lower a level. A setting that raises one is refused with an error. |
| `rules.retired_words` | list of words | `[]` | Extra words the retired-wording check refuses, on top of the shipped list. |
| `seats.off` | list of names | `[]` | Steps of the pre-push hook that do not run. The push prints `gate: <name> OFF (config)`. Names are in the table below. |
| `session_hooks.off` | list of names | `[]` | AI agent guard-rails that do not run. Names are in the table below. |
| `linters.off` | list of names | `[]` | Linters and formatters the pre-push hook skips. The installer adds no config file for them. Names are in the table below. |
| `writing_guides.off` | list of names | `[]` | Writing guides the installer does not add to `.claude/skills/`. Names are in the table below. Switch them off if your project already has its own documentation instructions. |
| `ratchet_days` | whole number, 1 or more | `90` | Days from today to the deadline the installer writes on a new baseline. |
| `tests_deadline_seconds` | whole number, 1 or more | `900` | The time limit on the pre-push test run. If the tests have not finished in that time, the hook stops the run and refuses the push. A run that long usually means a test hangs. Raise the limit only for a suite that really takes that long. |
| `layout` | object | `{}` | Moves the installed files (see [Layout keys](#layout-keys)). |

A rule whose every check is switched off is counted as **switched off**, never as enforced. The count in the `CLAUDE.md` block reads, for example, "24 of 74 (3 switched off)". Use a switch for something that does not apply to your project. Use the [exceptions file](#exceptions-file) to set something aside for a while.

### Pre-push steps (`seats.off`)

| Name | What the step does |
|---|---|
| `build` | Builds the project with warnings treated as errors. |
| `tests` | Runs the platform's test runner. |
| `lint` | Runs the platform's linter with the shipped config. |
| `format` | Runs the formatter in check mode. |
| `rules-scan` | Runs the rules scanner on what the push adds, and on the whole project. |
| `doc-comments` | Counts missing doc comments across the project. Reports only. |
| `jscpd` | Refuses new duplicated code. |
| `gh-ruleset` | Checks that the default branch is protected on GitHub. |

### Session hooks (`session_hooks.off`)

| Name | What it does |
|---|---|
| `governing-edit` | Refuses an agent's edit to a file that defines the checks. |
| `chained-cd` | Refuses a `cd X && …` chain. Use one command with absolute paths instead. |
| `infra-command` | Refuses infrastructure commands, except their read-only forms. |
| `no-verify` | Refuses `--no-verify` and every other way around the git hooks. |
| `force-push` | Refuses a force push. |
| `scan-at-commit` | Scans the staged changes before an agent commits. |
| `scan-on-edit` | Scans a file after an agent edits it. |
| `unpushed-at-stop` | Refuses to end an agent's turn with unpushed commits. |
| `rules-at-start` | Prints the rules and the enforced count when a session starts. |
| `attribution-trailer` | Requires a commit from an agent session to name the model that did the work. This one runs in the `commit-msg` git hook. |

### Linters (`linters.off`)

| Platform | Names |
|---|---|
| iOS, macOS | `swiftlint`, `swiftformat` |
| Android | `detekt`, `ktlint`, `androidlint` |
| React Native, web | `eslint`, `tsc`, `prettier` |
| Python | `ruff`, `mypy` |

### Writing guides (`writing_guides.off`)

Writing guides are Claude Code skills that an AI agent follows when it writes documentation. The installer adds each one that is on to `.claude/skills/<name>/SKILL.md`, and the `CLAUDE.md` block tells agents to use them. They are guidance, not checks: nothing refuses a commit because of them.

| Name | What it covers |
|---|---|
| `write-developer-documentation` | READMEs, quickstarts, settings and CLI references, troubleshooting pages, design documents, rule documents, changelogs and release notes. |
| `write-a-guide` | Short guides to a tool, dashboard or process, for the people who use or look after it. |

A guide is yours to edit once installed. The installer updates it only while it still matches the shipped version. When you switch a guide off, the installer removes it on its next run, unless you have edited it.

### Layout keys

Set these under `layout` only when your project must move the installed files.

| Key | Default |
|---|---|
| `checks_dir` | `.coast/checks` |
| `hooks_dir` | `.githooks` |
| `session_hook` | `.coast/hooks/claude-hook.py` |
| `settings_file` | `.claude/settings.json` |
| `rules_document` | `docs/domain-rules.md` |
| `ai_rules_document` | `docs/ai-features-rules.md` |
| `context_file` | `CLAUDE.md` |
| `skills_dir` | `.claude/skills` |
| `lock_name` | `coast-push.lock` |
| `temp_prefix` | `coast-` |
| `env_prefix` | `COAST_` |

The `.coast` folder itself cannot move. The hooks find the settings file through it, so `layout.state_dir` is refused.

## Exceptions file

`.coast/rules-exceptions.json` sets something aside for a while. It has two kinds of entry, and both can sit in the same list.

### Skip a pre-push step until a date

Use it when a step is wrong for your situation and you are waiting on a fix.

```json
{
  "exceptions": [
    {"seat": "build", "reason": "the build needs env vars this checkout has not got",
     "who": "Pat Lee", "when": "2026-09-16", "until": "2026-09-30"}
  ]
}
```

| Field | Meaning |
|---|---|
| `seat` | The step to skip: `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd` or `gh-ruleset`. |
| `reason` | Why. Printed on every push. |
| `who` | Who excused it. Printed on every push. |
| `when` | The date you wrote the entry. |
| `until` | Required. The last day the step is skipped, as `YYYY-MM-DD`. After it, the step runs again. An entry with no `until` is ignored, so a skip cannot become permanent. |

### Excuse one scanner rule on one file

Use it for a test fixture that looks like a secret, a scaffold file that looks like a second theme file, or a false positive you have reported.

```json
{
  "exceptions": [
    {"id": "secret-literal", "path": "Tests/Auth/FixtureKeys.swift",
     "reason": "a fake key read by the code under test",
     "who": "Pat Lee", "when": "2026-09-16"}
  ]
}
```

| Field | Meaning |
|---|---|
| `id` | The scanner rule id from the `FAIL` line. |
| `path` | An exact file, or a folder ending in `/**`. |
| `reason`, `who`, `when` | Why, who, and the date written. |

## Paths file

`.coast/paths.json` tells the scanner which of your files are which. The installer writes a first version when it finds your theme file. Edit it if your project is laid out differently from your platform's default.

```json
{
  "platforms": {
    "ios": {
      "classes": {
        "theme": ["MyApp/DesignSystem/Theme.swift"],
        "ui_lib": ["MyApp/DesignSystem/**"],
        "plans": ["plans/**", "docs/handoff/**"]
      }
    }
  }
}
```

The classes you will set most often:

| Class | Meaning |
|---|---|
| `theme` | The one file where colours, fonts and spacing live. |
| `ui_lib` | Your shared components. |
| `ui` | Screens and views. The scanner looks for bare user-facing text here. |
| `strings` | Your translation files. |
| `tests` | Test code. |
| `plans` | Planning documents, transcripts, and anything else that is not product code. |
| `config_home` | Where hostnames and environment settings are allowed. |

## Other project files

| File | What it does |
|---|---|
| `.coast/xcode-scheme` | For an Xcode project: the scheme name to build and test. Without it, the first scheme Xcode lists is used. |
| `.coast/module-kinds.json` | For Swift packages: which targets are apps, feature modules and shared layers. The import check uses it to refuse one feature importing another. Example: `{"app": ["MyApp"], "feature": ["Onboarding", "Journal"], "shared": ["Core", "DesignKit"]}` |
| Linter and formatter configs | `.swiftlint.yml`, `eslint.config.mjs`, `detekt.yml`, `ruff.toml` and so on. The installer adds one only if you have none. They are yours to edit. The installer does not touch a file you changed. |
| `.claude/skills/write-developer-documentation/`, `.claude/skills/write-a-guide/` | The writing guides. Yours to edit. See [Writing guides](#writing-guides-writing_guidesoff). |
| `docs/domain-rules.md` | Your project's copy of the rules. It is yours to edit. Its first line names the release its text comes from. The installer never replaces a copy from the same release. When a newer release changes the rules, the installer replaces your copy, and keeps it as `docs/domain-rules.v<release>.md` if you had edited it. |

## Baselines

A baseline is a count of problems the project already had when it installed the standards. The count may only go down. Each count has a deadline, after which the check blocks.

| File | What it holds |
|---|---|
| `.coast/ratchet-baseline.json` | Scanner counts and tool counts (build warnings, linter and formatter findings, a missing test target). Each has a date, a deadline and, for tools, a per-file map. |
| `.coast/jscpd-baseline.json` | The duplicated-code count. |

- Do not edit the counts by hand.
- To lower a count that fell, run the installer with `--lower-baselines` (or run a normal install again).
- To move a deadline, a person edits the file and records who and why under `moves`. Raising a count or moving a deadline is always a person's decision.

## Versions and releases

`.coast/standards-version` records the release installed in your project. It takes one of two forms:

- `1.2.0`: installed from a published release.
- `1.2.0+<commit>`: installed from a checkout that was not at a release tag.

The installer's last line prints the same value. To change release, run the installer with `--release`.

| Environment variable | What it does |
|---|---|
| `COAST_STANDARDS_CACHE` | The folder releases are downloaded into. Default: `$XDG_CACHE_HOME/coast-standards` when that variable is set, else `~/.cache/coast-standards`. |
| `COAST_STANDARDS_RELEASES` | The address release tarballs are downloaded from, for a mirror. |
| `JSCPD_BIN` | The `jscpd` program to use. |

## Run every check on one push

A push normally runs only the checks for what it changed ([how it works](how-it-works.md)). To run every check once, for example before a release or in CI:

```bash
COAST_SCOPE=all git push
```

A scoped push judges tool counts by the per-file map in `.coast/ratchet-baseline.json`. The installer writes that map with `--measure-tools`. Until it exists, the build, linter and formatter steps run on the whole project and say so.
