# Options

*Last updated: 2026-09-08*

Everything you can change today, and where. All of it lives in a `.coast/` folder in
your project, which the installer creates.

## Install options

| Option | What it does |
|---|---|
| `--platform <name>` | `ios`, `macos`, `android`, `react-native`, `web`, or `python`. Only needed when the installer cannot tell from your files. |
| `--dry-run` | Print what would change; write nothing. |
| `--measure-tools` | Re-measure your starting lines for build warnings, linter and formatter findings. A first install does this anyway. Add `format,lint` to skip the build. |
| `--by <name>` | The name recorded on the starting lines. Defaults to your git name. |
| `--secret-scan` | Run the whole-project secret scan again. |
| `--release VERSION` | Fetch that published release (`1.1.0`, or `latest`) into the cache and install from it, instead of from the copy you ran. See below. |
| `--init` | Ask the on/off questions again (rules, push-gate seats, session hooks) and write the answers to `.coast/config.json`. A first install at a terminal asks them once anyway. |
| `--yes` | Take every default without asking: everything on. |
| `--owner NAME`, `--product NAME`, `--org NAME` | The names every refusal sentence and the `CLAUDE.md` block use ("ask Pat Lee in one line first"). Recorded in `.coast/config.json`. |
| `--checks-dir PATH` | Put the checks somewhere other than `.coast/checks/`. Recorded under `layout` in the config. |

## The version your project carries

`.coast/standards-version` records the release the installer put into your project. It
has two forms: `1.0.0` when the install came from a published release, and
`1.0.0+<commit>` when it came from a checkout of the repository that was not at a release
tag. The installer's last line prints the same value. To move to another release, run
the installer with `--release`; your project keeps its own copy, so nothing outside it
changes.

Releases are downloaded into `~/.cache/coast-standards/<version>/`. Two environment
variables change where that happens: `COAST_STANDARDS_CACHE` sets the cache folder, and
`COAST_STANDARDS_RELEASES` sets the address the tarballs are fetched from, for a mirror.

## Tell it where things are

`.coast/paths.json` tells the scanner which files are which. The installer writes a
first version when it finds your theme file. Edit it if your project is laid out
differently from the default for your platform.

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

The classes you will most often set:

| Class | Meaning |
|---|---|
| `theme` | the one file where colours, fonts, and spacing live |
| `ui_lib` | your shared components |
| `ui` | screens and views (the scanner looks for bare text here) |
| `strings` | your translation files |
| `tests` | test code |
| `plans` | planning documents, transcripts, and anything else that is not product code |
| `config_home` | where hostnames and environment settings are allowed to live |

## Set aside one rule on one file

`.coast/rules-exceptions.json` excuses a named check on a named path. Use it for a test
fixture that looks like a secret, a scaffold file that looks like a second theme, or a
false positive you have reported.

```json
{
  "exceptions": [
    {"id": "secret-literal", "path": "Tests/Auth/FixtureKeys.swift",
     "reason": "a fake key read by the code under test",
     "who": "Jordan Lee", "when": "2026-09-04"}
  ]
}
```

`path` is an exact file or a folder with `/**`.

## Set aside one whole check for a while

The same file can skip one push-time check until a date. Use it when a check is wrong
for your situation and you are waiting on a fix, for example a build that needs
environment variables this machine does not have.

```json
{
  "exceptions": [
    {"seat": "build", "reason": "the build needs env vars this checkout has not got",
     "who": "Jordan Lee", "when": "2026-09-05", "until": "2026-09-19"}
  ]
}
```

Checks you can name: `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`,
`jscpd`, `gh-ruleset`. The date is required. An entry without one is ignored, so a skip cannot
become permanent.

## Which Xcode scheme to build

For an Xcode project, write the scheme name into `.coast/xcode-scheme`. Otherwise the
first scheme Xcode lists is used.

## Module layering (Swift packages)

`.coast/module-kinds.json` tells the import check which of your targets are app targets,
feature modules, and shared layers, so it can refuse a feature importing another feature.

```json
{"app": ["MyApp"], "feature": ["Onboarding", "Journal"], "shared": ["Core", "DesignKit"]}
```

## The linter configuration

The installer writes your platform's linter and formatter configuration
(`.swiftlint.yml`, `eslint.config.mjs`, `detekt.yml`, `ruff.toml`, and so on) only if you
did not have one. These files are yours: edit them freely, and the installer will not
touch a file you have changed.

## The rules file

`docs/domain-rules.md` is your project's copy of the rules. It is yours too. The installer
never replaces it at the same version. When a newer version of the rules is published, the
installer upgrades it and keeps your old copy beside it as `docs/domain-rules.v<N>.md`.

## Starting lines

`.coast/ratchet-baseline.json` and `.coast/jscpd-baseline.json` hold the counts recorded
at install with their dates. You do not edit these by hand. To lower a count that has
fallen, run the installer again. To move a date, a person edits the file and records who
and why under `moves`.

## Switch a rule, a check or a guard-rail off

`.coast/config.json` holds the switches. The installer writes it on the first install —
after asking you, one screen per group, at a terminal — and never rewrites your answers.
Everything is on until you say otherwise. Edit the file and the next commit, push or
agent action reads it; no re-install is needed.

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
  "session_hooks": {"off": []},
  "linters": {"off": []},
  "ratchet_days": 90,
  "layout": {}
}
```

| Key | What it does |
|---|---|
| `owner` | the names every refusal sentence uses; blank means "the owner" and "this project" |
| `rules.off` | scanner signatures that do not run at all. The ids are the ones in a FAIL line (`:scrim-modal:`) |
| `rules.severity` | lower a signature: `block` → `ratchet` → `advisory`. Raising one is refused with a sentence; the table decides what blocks |
| `rules.retired_words` | words the retired-wording check refuses, on top of the shipped one |
| `seats.off` | push-gate seats that print `gate: <name> OFF (config)` and run nothing: `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd`, `gh-ruleset` |
| `session_hooks.off` | agent guard-rails that exit without checking: `governing-edit`, `chained-cd`, `infra-command`, `no-verify`, `force-push`, `scan-at-commit`, `scan-on-edit`, `unpushed-at-stop`, `rules-at-start`, `attribution-trailer` |
| `linters.off` | linters the seats skip and the installer does not seed: `swiftlint`, `swiftformat`, `detekt`, `ktlint`, `androidlint`, `eslint`, `tsc`, `prettier`, `ruff`, `mypy` |
| `ratchet_days` | how far out a new starting line's deadline is written |
| `layout` | where the layer's files live, for a project that must move them (`checks_dir`, `hooks_dir`, `session_hook`, `settings_file`, `rules_document`, `context_file`) |

A switch is counted. A rule whose every check is off shows as **switched off** in the
"enforced by a check" number and the `CLAUDE.md` block ("24 of 74 (3 switched off)"), so
nobody reads a rule as held when nothing holds it. The file is governed: an AI agent is
refused when it tries to write it, which is the point — a switch is a person's decision.
The two dated exception shapes above are still the right tool for setting one thing
aside for a while; a switch is for a rule that does not apply to your project at all.
