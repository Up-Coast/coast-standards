# Coast Standards

*Last updated: 2026-09-07*

Coast Standards is a set of engineering rules for apps, and a small tool that installs
those rules into your project so they are checked automatically every time code is
saved, committed, or pushed.

You do not need to read the rules to benefit from them. Once installed, the checks run
on their own and stop bad changes before they reach your repository. When something is
stopped, you get a plain sentence saying what was wrong and where.

## Who this is for

- **Founders using Coast.** Coast installs this into every project it builds. You will
  mostly meet it as the "rules enforced by a check" number in your Rules tab and as the
  occasional refusal with a reason. This documentation explains what those mean.
- **Developers adding it to an existing project.** You run one command, commit what it
  writes, and the checks are live. The [Quickstart](quickstart.md) takes about ten minutes.

## What it does, in one paragraph

Every rule is sorted into one of two kinds: rules a machine can check, and rules only a
person can judge. The machine-checked ones are enforced by scripts that run on your own
computer before anything is pushed: a scanner that looks for known mistakes in the lines
you added, your platform's standard linter, a duplicate-code detector, and a set of
guard-rails for AI coding agents. The rest are listed as "needs a reviewer". The
number of rules a machine holds is shown to you and only ever goes up.

## Pages

| Page | Read it when |
|---|---|
| [Quickstart](quickstart.md) | you want it installed in your project now |
| [How it works](how-it-works.md) | you want to understand what runs, and when |
| [What gets checked](what-gets-checked.md) | you want to know which mistakes it catches |
| [Options](options.md) | you want to change how it behaves in your project |
| [When a check stops you](when-a-check-stops-you.md) | something was refused and you want to know what to do |
| [Working with AI coding agents](ai-agents.md) | you use Claude Code or a similar tool on this project |
| [FAQ](faq.md) | short answers to common questions |

## Supported platforms

iOS, macOS, Android, React Native, web (TypeScript), and Python services.

## Requirements

- macOS or Linux, with `git` and Python 3.10 or newer
- your platform's normal toolchain (Xcode, Android Studio and Gradle, Node, or Python)
- `jscpd`, the duplicate-code detector: `npm install -g jscpd@5.1.2`

## Getting help

The [FAQ](faq.md) covers the common cases. If a check refused something you believe is
correct, [When a check stops you](when-a-check-stops-you.md) explains the sanctioned way
to set it aside, and how to report a wrong check so it gets fixed for everyone.
