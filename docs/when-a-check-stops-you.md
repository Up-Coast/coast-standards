# When a check stops you

*Last updated: 2026-09-08*

Every refusal prints a line like this:

```
FAIL rules Sources/Home/HomeView.swift:42:ui-string-literal: bare user-facing text in a view — add it to the strings catalog [L-1]
```

Read it left to right: which check, which file and line, the short name of the rule,
what was wrong and where it belongs, and the rule's id in your `docs/domain-rules.md`.

## Usually: fix the line

Most refusals are exactly what they say. Move the text to the strings file, take the
colour from the theme, remove the secret. Commit again.

## "It says a count went up"

You added a new instance of something your project already had (a spacing number in a
view, a comment on a code line, a log line with personal data). The count is allowed to
fall or stay flat, never rise. Remove the new one, or remove an old one somewhere else.

## "It says a count went down and refuses anyway"

When a scanner count falls, the recorded starting line has
to come down with it so it cannot creep back up. Run the installer again; it lowers the
count. Commit the updated `.coast/ratchet-baseline.json` with your change.

Build warnings are different: a count below the starting line just passes with a note.

## "The build failed on a warning"

The build runs with warnings treated as errors. Fix the warning. If your project came
with warnings, they were recorded at install and only a new one refuses.

## "The push says another push is running"

Two pushes from the same checkout are run one at a time so their builds do not cross.
Wait for the other to finish. If a push died and left its lock behind, the message names
the lock folder; it is broken automatically after an hour, or you can remove it.

## "No iOS simulator matched"

The tests look for an iPhone simulator on the newest installed iOS. If Xcode cannot see
one, they run on the Mac instead. To use the simulator, install a runtime that matches
your app's deployment target.

## "jscpd is not installed"

```bash
npm install -g jscpd@5.1.2
```

Then run the installer again so it can record your starting line for duplicate code.

## "This check is wrong"

The sanctioned path, in order:

1. **Set it aside with a date.** Add an entry to `.coast/rules-exceptions.json`, either for
   one rule on one file, or for one whole check until a date. See [Options](options.md).
   Both are signed and dated so the decision is visible.
2. **Report it** so it gets fixed for everyone: open an issue on the standards repository
   with the FAIL line and the code it refused.

What not to do: `git push --no-verify`. It turns every check off at once and leaves no
record. If you are using an AI agent, it is refused outright.

## "A file I need to edit is refused as governing"

The files that define the checks (`.coast/` — the checks, the session hook, the config
and the starting lines — `.githooks/`, the rules file, the linter configuration,
`.claude/settings.json`) are not an agent's to edit. A person can edit them. If an agent
needs a change there, it should say so and stop.
