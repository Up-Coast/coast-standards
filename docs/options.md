# Options

*Last updated: 2026-09-07*

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

## What you cannot switch off today

Individual rules, checks, and agent guard-rails are all on for your platform. Per-rule
on/off switches and severity settings are planned and will appear here when they ship.
Until then, the two exception shapes above are the sanctioned ways to set something
aside, and both are dated and signed.
