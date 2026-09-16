# When a check stops you

*Last updated: 2026-09-16*

## Reading a refusal

Every refusal prints one line:

```
FAIL rules Sources/Home/HomeView.swift:42:ui-string-literal: bare user-facing text in a view — add it to the strings catalog [L-1]
```

From left to right:

| Part | Example |
|---|---|
| The check | `rules` |
| File and line | `Sources/Home/HomeView.swift:42` |
| Short name of the problem | `ui-string-literal` |
| What is wrong and how to fix it | `bare user-facing text in a view — add it to the strings catalog` |
| Rule id in your `docs/domain-rules.md` | `[L-1]` |

Below, `.coast/` is your project's checks folder and `<standards>` is your copy of the standards.

## A line of code was refused

**Means:** the check found exactly what the message says.

1. Fix the line as the message says (move the text to the strings file, use the theme colour, remove the secret).
2. Commit or push again.

## "A count went up"

**Means:** you added a new case of an existing problem that has a baseline (a count that may only go down). Examples: a spacing number in a view, a log line with personal data.

1. Remove the new case, or fix an old one elsewhere so the total does not rise.
2. Push again.

## "A count went down" and the push is still refused

**Means:** you fixed some existing problems. The recorded baseline must come down too, so the count cannot creep back up.

1. Lower the baseline:

   ```bash
   python3 <standards>/enforcement/adopt.py <project> --lower-baselines
   ```

   This only rewrites `.coast/ratchet-baseline.json` and `.coast/jscpd-baseline.json`. It only lowers counts and never moves a deadline. An AI agent may run it itself.
2. Commit the updated baseline file together with your change.
3. Push again.

Build warnings, linter findings, formatter findings and duplicate code do not refuse when they fall. The hook prints a note suggesting the same command.

## "The test run passed … s with no verdict" (`tests-deadline`)

**Means:** the tests did not finish within `tests_deadline_seconds` (default 900 seconds). The pre-push hook stopped the run and refused the push. This is usually a hanging test, not a slow suite.

1. Find the test that hangs. Run the test suites one at a time under the same time limit.
2. Fix it so it finishes or fails.
3. Push again.

If the suite genuinely takes longer, a person can raise `tests_deadline_seconds` in `.coast/config.json`. An agent cannot. See [Options](options.md).

## "The build failed on a warning"

**Means:** the build treats warnings as errors.

1. Fix the warning.
2. Push again.

If the project had warnings at install, they are in the baseline. Only new ones refuse.

## "Another push is running"

**Means:** pushes from the same checkout run one at a time so their builds do not collide.

1. Wait. The hook waits for the other push, then continues.
2. If it gives up after 45 minutes, check that the other push is still running, then push again.

A lock left by a push that died is removed automatically once it is an hour old. The message names the lock folder if you want to remove it yourself.

## "No iOS simulator matched"

**Means:** Xcode has no iPhone simulator on the newest installed iOS. The tests run on the Mac instead.

1. To test on a simulator, install an iOS runtime that matches your app's deployment target.

## "jscpd is not installed"

1. Install it:

   ```bash
   npm install -g jscpd@5.1.2
   ```

2. Run the installer again so it records your duplicate-code baseline.

## "A file I need to edit is refused"

**Means:** the file defines the checks, and AI agents are not allowed to edit it. These files are: `.coast/` (checks, session hook, config, baselines), `.githooks/`, the rules file, the linter config, and `.claude/settings.json`.

1. If you are a person, edit it yourself.
2. If you are an agent, say what change is needed and why, then stop.

## The check is wrong

1. **Set it aside with an end date.** A person adds an entry to `.coast/rules-exceptions.json`. It can excuse one rule on one file, or one whole pre-push check until a date. Each entry records who and why. See [Options](options.md).
2. **Report it.** Open an issue on the standards repository with the FAIL line and the refused code.

Do not use `git push --no-verify`. It turns off every check at once and leaves no record. AI agents are blocked from using it.
