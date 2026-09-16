# Coast Standards documentation

*Last updated: 2026-09-16*

Coast Standards is a set of engineering rules, and a tool that installs checks for them into your project. The checks run on every commit and push, and stop changes that break a rule. Each refusal says what was wrong and where.

## Pages

- [Quickstart](quickstart.md): install it into your project in about ten minutes.
- [How it works](how-it-works.md): what runs, and when.
- [What gets checked](what-gets-checked.md): the mistakes it catches.
- [Options](options.md): every setting, installer flag and file you can change.
- [When a check stops you](when-a-check-stops-you.md): what to do after a refusal.
- [Working with AI coding agents](ai-agents.md): using Claude Code or a similar tool on the project.
- [FAQ](faq.md): short answers to common questions.
- [The rules](../rules/README.md): the rules themselves, including the one a refusal named.

## Supported platforms

iOS, macOS, Android, React Native, web (TypeScript), and Python services.

## Requirements

- macOS or Linux, with `git` and Python 3.10 or newer.
- Your platform's normal toolchain: Xcode, Android Studio and Gradle, Node, or Python.
- `jscpd`, the duplicate-code detector: `npm install -g jscpd@5.1.2`.
