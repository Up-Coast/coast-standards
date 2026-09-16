# What gets checked

*Last updated: 2026-09-16*

A summary of what the checks look for. The exact rules for your platform are in your project's `docs/domain-rules.md`. Each rule there names the check that enforces it.

## Text and translation

- User-facing text typed into a screen instead of a strings file.
- Sentences glued together from pieces (`"You have " + n + " items"`). These cannot be translated.
- Plurals handled by hand (`count == 1 ? "item" : "items"`).
- Text upper-cased in code instead of in the design.
- More than one strings file per language.
- Strings-file keys that are English sentences instead of names.

## Design consistency

- Colours, font sizes and spacing typed into views instead of taken from the theme file. Spacing has a baseline: existing cases are counted, new ones refused.
- A second theme file.
- Fixed text sizes that ignore the user's accessibility settings.
- Layouts sized for one screen (advisory).

## Security

- Secrets in code: API keys, tokens, private keys, passwords.
- Secret-shaped files (`.env`, `.p12`, `.pem`, keystores) and data files added to the repo.
- Plain `http://` addresses.
- Raw HTML injected into a page.
- `eval` and similar.
- Shell commands or database queries built from strings.
- Scripts loaded from a CDN.
- Android components exported without a permission.
- Personal data in logs (email, phone, address, card numbers).

## Code quality

- A missing doc comment on a public function or type.
- New compiler warnings. The build treats warnings as errors, or compares against your baseline.
- New duplicated code.
- Force-unwraps and unsafe casts (Swift), unsafe null calls (Kotlin), unhandled promises (TypeScript), loose typing (TypeScript, Python).
- Blocking calls on the main thread.
- Views that import the database, and view models that import UI frameworks.
- Types and files that are too large (advisory).
- Money stored as floating point (advisory).
- Hand-built versions of things the platform provides: tab bar, picker, router, search field, progress bar, password hashing.

## Tests

- A test that does not name the acceptance criterion it proves.
- Tests that reach the real network.
- Tests weakened in a change: skipped, disabled, or assertions removed.
- A test run that does not finish within the time limit (see [When a check stops you](when-a-check-stops-you.md)).

## Environment

- Hardcoded branch names, absolute paths, `localhost` ports and hostnames outside the config file.
- Retired words in copy and docs (for example, "guarantee").

## Process

- A commit message must have a subject line under 100 characters.
- A commit made by an AI agent must name the model that did the work.
- Your main branch must be protected on GitHub: pull requests required, no deletion, no force-push, no bypass.

## What a machine does not check

About half the rules need a human or AI reviewer. Examples: is a name accurate, is an abstraction premature, does an error message tell the truth, was the design followed. These are marked "review" in your rules file, so nobody mistakes them for enforced rules.
