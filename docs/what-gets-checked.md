# What gets checked

*Last updated: 2026-09-07*

This is the plain-words version. The exact rule text for your platform is in your
project at `docs/domain-rules.md`, and every rule there ends with the name of the check
that holds it.

## Text and translation

- User-facing text typed straight into a screen instead of a strings file.
- Sentences built by gluing pieces together (`"You have " + n + " items"`), which cannot
  be translated.
- Handling singular and plural by hand (`count == 1 ? "item" : "items"`).
- Upper-casing text in code instead of in the design.
- More than one strings file per language.
- Strings-file keys that are English sentences instead of names.

## Design consistency

- Colours, font sizes, and (over time) spacing typed into views instead of coming from
  the one theme file.
- A second theme file appearing somewhere else.
- Fixed text sizes that ignore the user's accessibility settings.
- Layouts sized to one screen (advisory).

## Security

- Secrets in code: API keys, tokens, private keys, passwords. Also secret-shaped files
  (`.env`, `.p12`, `.pem`, keystores) and data files added to the repository.
- Plain `http://` addresses.
- Raw HTML injected into a page.
- `eval` and friends.
- Building shell commands or database queries from strings.
- Scripts loaded from a CDN.
- Android components exported without a permission.
- Logging personal data (email, phone, address, card numbers).

## Code quality

- Every public function and type has a doc comment.
- No new compiler warnings. The build runs with warnings treated as errors, or against
  your recorded starting line.
- No new duplicated code.
- Force-unwraps and unsafe casts (Swift), unsafe null calls (Kotlin), unhandled promises
  (TypeScript), strict typing (TypeScript, Python).
- Blocking calls on the main thread.
- Views importing the database directly, and view models importing UI frameworks.
- Types and files that have grown too large (advisory).
- Money stored in floating point (advisory).
- A hand-rolled version of something the platform already provides: your own tab bar,
  picker, router, search field, progress bar, password hashing.

## Tests

- Every test names the acceptance criterion it proves.
- Tests that reach the real network.
- Tests weakened in a change: skipped, disabled, assertions removed.

## Environment

- Hardcoded branch names, absolute paths, `localhost` ports, and hostnames outside the
  configuration file.
- Retired wording in copy and docs (for example, "guarantee").

## Process

- A commit message with a subject line, under 100 characters.
- A commit made by an AI agent names the model that did the work.
- Your main branch is protected on GitHub: pull requests required, no deletion, no
  force-push, no exceptions.

## What is not checked by a machine

Roughly half the rules need a reader: whether a name is honest, whether an abstraction
is premature, whether an error message tells the user the truth, whether the design was
followed. These are listed in your rules file as "review" so that no one mistakes them
for enforced.
