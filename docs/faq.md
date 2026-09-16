# FAQ

*Last updated: 2026-09-16*

**Will this slow down my commits?**

No. A commit only scans the lines you added, which takes seconds. The build and tests run at push, and only for what the push changed. A push of documents runs no build or tests.

**Does my code leave my machine?**

No. Every check runs locally. Nothing is uploaded and no AI model is called.

**Will it rewrite my code?**

No. It only refuses. Formatting is checked, not applied.

**Will it replace my linter config?**

No. An existing linter config, or one you edit after install, is left alone.

**Will my existing git hooks stop working?**

No. They run after the standards' hooks, with the same arguments.

**My project has hundreds of warnings. Must I fix them first?**

No. They are recorded as a baseline with a deadline 90 days out. Until then, only new warnings refuse. After the deadline the count must be zero. See [How it works](how-it-works.md).

**Why does my first push pass when existing code breaks rules?**

Existing problems are recorded in the baseline instead of refused. Only lines you add from now on are judged.

**Can I turn off a rule I disagree with?**

Yes, a person can, in `.coast/config.json`. You can also set aside one rule on one file, or one pre-push check until a date, in `.coast/rules-exceptions.json`. AI agents cannot edit either file. See [Options](options.md).

**What does "rules enforced by a check: 24 of 74" mean?**

24 of the 74 rules in your rules file are enforced by a check that exists and runs. The rest need a reviewer, are advisory, or are process rules.

**Why can't I use `--no-verify` when I'm in a hurry?**

It turns off every check at once and records nothing. A dated exception does the same job for one check, with a name, a reason and an end date.

**Does it work on Windows?**

Not yet. macOS and Linux only.

**Which languages and platforms are supported?**

Languages: Swift, Kotlin, Java, TypeScript, JavaScript, Python. Platforms: iOS, macOS, Android, React Native, web, Python services.

**Which version do I have, and how do I upgrade?**

Your installed release is in `.coast/standards-version`. To upgrade, run the installer with `--release latest`, or with a version number. It keeps your edits and updates the file. See [Quickstart](quickstart.md#updating-later).

**Where do I report a wrong check?**

Open an issue on the standards repository. Include the FAIL line and the code it refused.
