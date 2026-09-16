# Coast Standards

Engineering rules for software built with AI coding agents, and the checks that enforce them.

Install it into a project and every commit and push is checked against the rules. An AI agent working in the project also knows the rules: what must stay DRY, where user-facing text lives, which imports are forbidden, and what a review must return.

Supported platforms: iOS, macOS, Android, React Native, web (TypeScript) and Python services. Full documentation with search: [up-coast.github.io/coast-standards](https://up-coast.github.io/coast-standards/).

## How this repo came to be

Scroll down if you don't care.... :)

Hi there, I'm Abbey. I am an iOS engineer (Intel/Mastercard) turned psuedo-short-lived system architect (Rivian) turned product manager (Rivian). I'm now teaching product strategy to both technical and non-technical folks, for FREE through my social venture [Up Coast Leaders](https://www.upcoastleaders.ca).

This project started in July 2026 when I first started using AI to code. I was a late bloomer because for the previous 18 months I had been building the free product strategy course and the companion workbook and doing it right took time! Because I was late, I didn't START until Fable. On the coding side I had played around a little bit with Replit, and I had plenty of experience using it as a non-technical user for research, projections, and drafting reports, so I knew going into it that it was going to piss me off big time when it broke what to me seem like simple rules. 

Y'know...like having one source of truth or not hard-coding things.

Before I even started coding, because I didn't want to be influenced by my experience with the AI, I documented everything that I felt makes a code base a good code base. I spent hours upon hours having a meeting with my Granola transcriber listing out everything I thought was important and how I would design a system of controls. It was kind of a dream come true, FINALLY all coding rules were up to me and no negotiating anything with my team! Muwahahahah!!!

I then had Claude add all OWASP recommendations and after that I had it search the developer communities for the platforms these standards cover in order to surface up platform specific community recommended coding rules and guidelines.

Everything in this repo is written by Claude, so yes the language is sometimes flowery or without purpose but it's AI talking to AI. This repo isn't for you, it's for your AI, so I decided to do an experiment and see if I could be completely hands off the actual code. 

So far that experiment has paid off!

Using these coding standards, since Fable was released (2 months ago), I have built:
- 3 iOS apps,
- a learning and course platform,
- a webapp,
- a mac app,
- a feedback system that takes reports from beta testers and fixes them in Claude automatically, and
- this development tool

I do believe that completing a feature most likely takes more tokens now. Often at the end of work the push will be blocked because a rule was not followed so there is rework done. But it is automatic, I don't manage it, and I suspect that in the long run less credits are used because there are less regressions, less bugs, less skipped work. In either case, even if it is still more credits, I am happier with the experience and the speed than I am when I try to use Claude without it.

I assume this can be used with other AI coding systems however I have only used Claude so it hasn't been tested.

## Install it into a project

You need macOS or Linux, `git`, and Python 3.10 or newer. The [quickstart](docs/quickstart.md) is the short version of these steps.

1. Install the programs the checks run: your platform's linter, formatter and test runner, plus `jscpd`. The list per platform is in the [quickstart](docs/quickstart.md).

   ```bash
   npm install -g jscpd@5.1.2
   ```

2. Fetch the newest release into `~/.cache/coast-standards/<version>/`. No clone is needed. The one-line command is in the [quickstart](docs/quickstart.md); it sets `$v` to the version.

3. Preview what the installer would change. Nothing is written.

   ```bash
   python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project --dry-run
   ```

4. Run the installer. At a terminal it asks the on/off questions once (see [Customize](#customize)). Press Enter to keep everything on.

   ```bash
   python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project
   ```

5. Commit and push what it wrote.

   ```bash
   git add -A
   git commit -m "Adopt Coast Standards"
   git push
   ```

6. Name your project's type in its `CLAUDE.md`: app, backend service, data/ML pipeline, or library/CLI. [`rules/PROJECT-TYPES.md`](rules/PROJECT-TYPES.md) says which rules apply to each. A project with a frontend and an API is two types, one per part.

7. Optional: edit `docs/domain-rules.md` to fit your product. Delete sections that do not apply and add your own rules. Keep every rule checkable: a reviewer must be able to answer "does this change break the rule?" with yes or no.

8. Optional: paste [`TEMPLATE-CLAUDE.md`](TEMPLATE-CLAUDE.md) around the block the installer wrote into `CLAUDE.md`, and fill in the blanks.

9. Optional: install the [BuilderOS](https://github.com/BuildGreatProducts/builder-os) skills (MIT, by Build Great Products). Some rules name three of them: `build-loop-claude-code`, `design-better` and `design-system`. No check depends on them.

   ```bash
   npx skills add BuildGreatProducts/builder-os
   ```

To have an AI agent do the install, give it the skill in [`skills/adopt-coast-standards/`](skills/adopt-coast-standards/SKILL.md). Copy that folder into `~/.claude/skills/` or the project's `.claude/skills/`.

The numbered files in [`rules/`](rules/README.md) are meant to be read in place. Reference them from the project's `CLAUDE.md` instead of copying them.

### What the installer adds

| Where | What |
|---|---|
| `.coast/checks/` | The rules scanner and the other checks. |
| `.githooks/` | Three git hooks: `pre-commit`, `commit-msg` and `pre-push`. The installer sets `core.hooksPath` to this folder. |
| `.coast/hooks/claude-hook.py` and `.claude/settings.json` | The Claude Code session hooks (guard-rails for AI agents). |
| `.coast/config.json` | Your settings. See [Customize](#customize). |
| `.coast/ratchet-baseline.json` and `.coast/jscpd-baseline.json` | The baselines: counts of problems the project already had. |
| `.coast/standards-version` | The release your project carries. |
| `docs/domain-rules.md` | Your project's copy of the rules for its platform. Only added when the file does not exist. |
| Linter and formatter configs | For example `.swiftlint.yml` or `eslint.config.mjs`. Only added when you do not have one. |
| `.claude/skills/` | Two writing guides that AI agents follow when they write documentation. You can switch them off. |
| `CLAUDE.md` | A block that tells AI agents the rules and how many are enforced by a check. |

On a first install the installer also builds the project once and scans every tracked file for secrets. It stops if it finds a secret.

An existing project does not have to fix everything first. The installer counts the problems the project already has: build warnings, linter and formatter findings, scanner findings, and a missing test target. It writes those counts as a baseline with a deadline 90 days out. After that, a count may go down but never up. At the deadline, the check starts blocking.

## Update to a newer release

1. Run the installer from any installed release, naming the release you want (`latest`, or a version such as `1.2.0`).

   ```bash
   python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project --release latest
   ```

2. Commit and push the changes.

What an update does:

- It replaces its own files and keeps files you edited.
- It keeps your settings in `.coast/config.json`.
- It lowers any baseline count that fell.
- When the platform rules have a newer version, it keeps your old copy as `docs/domain-rules.v<N>.md`.
- It changes nothing when nothing changed.

Each project holds its own copy of the rules and checks, like a dependency. Every release is listed in [CHANGELOG.md](CHANGELOG.md).

## Customize

All settings live in one file in your project: **`.coast/config.json`**. The full list of settings is in [Options](docs/options.md).

### Create the settings file

The installer writes `.coast/config.json` on the first install.

| You run | What happens |
|---|---|
| `adopt.py <project>` at a terminal, first install | It asks three screens of on/off questions: the scanner rules, the steps of the pre-push hook, and the session hooks. Every answer defaults to on. Press Enter to take them all. |
| `adopt.py <project> --yes` | No questions. Everything is on. |
| `adopt.py <project> --init` | Asks the questions again on a project that is already installed, and writes the new answers. |
| `adopt.py <project> --owner "Pat Lee" --product "Example App" --org "Example Co"` | Records the names that refusal messages and the `CLAUDE.md` block use ("ask Pat Lee first"). Blank names read as "the owner" and "this project". |

After that, edit the file by hand. The next commit, push or agent action reads it. You do not need to re-run the installer.

### Switch something off

Add its name to the matching `off` list in `.coast/config.json`:

```json
{
  "rules": {"off": ["scrim-modal"]},
  "seats": {"off": ["gh-ruleset"]},
  "session_hooks": {"off": ["chained-cd"]},
  "linters": {"off": ["mypy"]},
  "writing_guides": {"off": ["write-a-guide"]}
}
```

| List | What it switches off | The names |
|---|---|---|
| `rules.off` | A scanner rule. | The id in a `FAIL` line, for example `:scrim-modal:`. |
| `seats.off` | A step of the pre-push hook. | `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd`, `gh-ruleset` |
| `session_hooks.off` | A guard-rail for AI agents. | Listed in [Options](docs/options.md#settings-file). |
| `linters.off` | One linter or formatter. | Listed in [Options](docs/options.md#settings-file). |
| `writing_guides.off` | A writing guide for AI agents. Switch these off if you already have documentation instructions. | `write-developer-documentation`, `write-a-guide` |

A rule you switch off is counted as "switched off", never as enforced. Use a switch for something that does not apply to your project at all.

The same file also sets:

- `rules.severity`: lower a scanner rule to a baseline count or a warning.
- `rules.retired_words`: extra words the scanner refuses.
- `ratchet_days`: how far out a new baseline's deadline is (default 90).
- `tests_deadline_seconds`: the time limit on the push's test run (default 900).

Details for each are in [Options](docs/options.md#settings-file).

### Excuse a check for a while

To skip one step of the pre-push hook until a date, add an entry to **`.coast/rules-exceptions.json`**:

```json
{
  "exceptions": [
    {"seat": "build", "reason": "the build needs env vars this checkout has not got",
     "who": "Pat Lee", "when": "2026-09-16", "until": "2026-09-30"}
  ]
}
```

- Every push prints who excused the step and why.
- After the `until` date, the step runs again.
- An entry with no `until` date is ignored.

The same file can also excuse one scanner rule on one file. See [Options](docs/options.md#exceptions-file).

### Who may change these files

`.coast/config.json`, `.coast/rules-exceptions.json` and the installed checks define what is enforced. AI agents are refused when they try to edit them. A switch or an exception is always a person's decision.

When a newer instruction from a project's owner conflicts with a rule here, the newer instruction wins. Update the rules in the same session so they do not stay out of date.

## When a check stops you

A refusal prints one line: the check, the file and line, the rule, and what to do.

1. Fix what it names and commit again. This is the answer almost every time.
2. If a baseline count went down and the push still refuses, record the lower count. Then commit the two baseline files with your change. An AI agent may run this itself, because it can only lower counts.

   ```bash
   python3 ~/.cache/coast-standards/$v/enforcement/adopt.py /path/to/your/project --lower-baselines
   ```

3. If the check is wrong, stop. Tell the project's owner which step is wrong and why. Only a person can switch it off or excuse it (see [Customize](#customize)).

Never skip the hooks with `--no-verify`. More cases are in [When a check stops you](docs/when-a-check-stops-you.md).

## Read more

| Page | Read it when |
|---|---|
| [Quickstart](docs/quickstart.md) | You want it installed now. |
| [Options](docs/options.md) | You want the full list of settings, installer flags and files. |
| [How it works](docs/how-it-works.md) | You want to know what runs, and when. |
| [What gets checked](docs/what-gets-checked.md) | You want to know which mistakes it catches. |
| [When a check stops you](docs/when-a-check-stops-you.md) | Something was refused. |
| [Working with AI coding agents](docs/ai-agents.md) | You use Claude Code or a similar tool. |
| [FAQ](docs/faq.md) | You want short answers to common questions. |
| [The rules](rules/README.md) | You want to read the rules. Start with [`00-priority-rules.md`](rules/00-priority-rules.md): DRY is the rule above all others. |
| [Enforcement](enforcement/README.md) | You want the design of the checks. |
| [Developer guide](enforcement/DEVELOPER-GUIDE.md) | You work on the checks themselves: every mode, flag, file and format. |
| [Toolchain](enforcement/TOOLCHAIN.md) | You want the pinned tool versions. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | You want to change a rule or a check. |

### What is in this repo

| Path | What it is |
|---|---|
| [`rules/`](rules/README.md) | The rules. The numbered files apply to every project. `rules/types/` covers backend services and data/ML pipelines. `rules/platform/` holds one checkable rules file per platform, plus [`ai-features.md`](rules/platform/ai-features.md) for apps with AI features. Every rule names the check that enforces it. |
| [`enforcement/`](enforcement/README.md) | The checks: the rules scanner, the doc-comment check, the rule verifier, linter configs, git hooks, Claude Code hooks, and the installer `adopt.py`. |
| [`docs/`](docs/README.md) | The user documentation. |
| [`skills/adopt-coast-standards/`](skills/adopt-coast-standards/SKILL.md) | A skill that lets an AI agent run the install. |
| [`skills/write-developer-documentation/`](skills/write-developer-documentation/SKILL.md), [`skills/write-a-guide/`](skills/write-a-guide/SKILL.md) | The writing guides the installer adds to a project, unless switched off. You can also install them as personal Claude Code skills. |
| [`TEMPLATE-CLAUDE.md`](TEMPLATE-CLAUDE.md) | A starter block for a project's `CLAUDE.md`. |
| `CHECKS-VERSION` | The release number. Each release is also the git tag `v<number>` and an entry in [CHANGELOG.md](CHANGELOG.md). |
| `.githooks/` | This repo's own pre-commit hook. Install it once per clone with `git config core.hooksPath .githooks`. |

## License

Coast Standards is source-available under its own license, [LICENSE.md](LICENSE.md). It is not open source.

- You may use it, including in a business, to build and ship your own software.
- You may share it unchanged, with the notice kept.
- You may change the copies the installer puts in your project.
- You may not sell it, publish a changed version as the standards, or build a product or service whose main value comes from it.

Contributions are welcome and are covered by the same license.
