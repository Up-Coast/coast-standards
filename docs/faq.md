# FAQ

*Last updated: 2026-09-07*

**Will this slow down my commits?**
No. A commit runs the scanner on the lines you added, which takes seconds. The full
battery runs only at push, on what the push changed: a push of documents alone runs no
build and no tests at all, and a push of code takes as long as the affected modules' build
and tests, on every platform.

**Does my code leave my machine?**
No. Every check runs locally. Nothing is uploaded and no model is called.

**Will it rewrite my code?**
No. It only refuses. Formatting is checked, not applied.

**I already have a linter config. Will it be replaced?**
No. A linter config you already have, or one you edit after install, is left alone.

**I already have git hooks. Will they stop working?**
No. Your existing hooks are recorded and run after the standards' hooks, with the same
arguments.

**My project has hundreds of warnings. Do I have to fix them first?**
No. They are counted at install and become a starting line with a 90-day date. Only a new
warning refuses. After 90 days the count has to be zero.

**Can I turn off a rule I disagree with?**
Not with a switch yet. You can set aside one rule on one file, or one whole check until a
date, and both are signed. Per-rule switches are planned. See [Options](options.md).

**What is "rules enforced by a check 24 of 74"?**
Of the 74 rules in your project's rules file, 24 are enforced by a check that runs. The
rest need a reviewer, are advisory, or are process rules. A rule counts only when the
check it names exists and runs.

**Why does the first push after install pass when my code breaks rules?**
Lines written before the checks existed are legacy, and legacy is recorded as a starting
line rather than refused. Only lines you add from now on are judged.

**Why can't I use `--no-verify` when I am in a hurry?**
Because it turns every check off at once and leaves no record of who did it or why. The
dated exception is the same escape with a name and an expiry on it.

**Does it work on Windows?**
Not today. macOS and Linux.

**Which languages are supported?**
Swift, Kotlin and Java, TypeScript and JavaScript, Python. Platforms: iOS, macOS, Android,
React Native, web, Python services.

**How do I know which version I have, and how do I upgrade?**
`.coast/standards-version` in your project holds the release you installed (for example
`1.0.0`). To upgrade, run the installer you already have with `--release latest`, or name
a version. It fetches that release, installs it, keeps anything you edited, and updates
the file. Nothing needs to be cloned. See [Quickstart](quickstart.md#updating-later).

**Where do I report a wrong check?**
Open an issue on the standards repository with the FAIL line and the code it refused.
