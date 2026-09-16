# Contributing

*Last updated: 2026-09-16*

Coast Standards is a set of rules plus the checks that enforce them. You can change either. The bar is the same for both:

- A rule is not done until a check holds it.
- A check is not done until a test proves what it refuses and what it lets through.

## License

Coast Standards is source-available under [LICENSE.md](LICENSE.md). When you submit a change, you license it to the project's owner for inclusion (section 5 of the license). You keep the copyright in what you wrote.

## Before you start

1. Read `rules/00-priority-rules.md`. It is short, and it applies to this repository too.
2. Turn on the repository's git hooks (once per clone). The pre-commit hook runs the verifier and the tests. The pre-push hook refuses a push to `main` that does not raise the version.

   ```bash
   git config core.hooksPath .githooks
   ```

3. Run the tests once to see the starting state. This takes about two minutes.

   ```bash
   python3 -m unittest discover -s enforcement/checks/tests -p 'test_*.py'
   ```

Everything is standard-library Python 3. There is nothing to install.

## Changing or adding a rule

- **Every rule ends with a `[…; check: …]` tag** naming the check that holds it. The verifier (`enforcement/checks/verify_rules.py`) refuses a rule that names no check, or names a check that nothing runs. The committed baseline of gaps may only go down.
- **A rule a machine can check** gets a scanner signature in `enforcement/checks/rules_signatures.json`. Add two test files under `enforcement/checks/tests/plants/<platform>/`: a `.fail` file the check must refuse and a `.pass` file it must accept.
- **A rule only a person can judge** is tagged `check: review`.
- **Rule ids are stable** (`DRY-3`, `L-7`, `SEC-12`). Never renumber. To replace a rule, retire its id and add a new one.
- **Platform files carry a release stamp.** The first line of each file under `rules/platform/` names the release in which its text last changed. After editing a platform file, run `python3 tools/build_rules.py`: it marks the file `unreleased`, and the release step replaces that with the release number. A project only receives a new copy of its rules document when the stamp is newer than its copy's. A test refuses a stale stamp.
- **Shared sections are edited in one place.** A section used by more than one platform lives in `rules/platform/shared/`. Edit it there, then run `python3 tools/build_rules.py` to update the platform files. Never paste the same section into two platform files; a test refuses it.
- **Write plainly.** State the rule, then the reason. No marketing, and no summary at the end of a section.

## Changing a check

- Read the relevant section first. `enforcement/DEVELOPER-GUIDE.md` describes every mode, flag, file and output format. `enforcement/README.md` explains the design and the reasons behind it.
- Keep the output format exactly: `FAIL <check> <path>:<id>: <words>`. Hooks, CI and the reference implementation parse it.
- Every behaviour change ships with a test in `enforcement/checks/tests/`.
- Every change updates the pages that describe it, in the same commit. Check at least `README.md`, `docs/options.md`, the other pages in `docs/`, `enforcement/DEVELOPER-GUIDE.md`, `enforcement/TEMPLATE-PROJECT-CLAUDE.md` and `CHANGELOG.md`. A test fails when an installer flag, a setting or a layout key is missing from `docs/options.md`.
- Write documentation by [`skills/write-developer-documentation/SKILL.md`](skills/write-developer-documentation/SKILL.md).

## Pull requests

- One change per pull request.
- The commit subject line is under 100 characters and says what changed.
- CI runs the verifier and the tests on Linux and macOS. Both must pass.
- Every documentation page has a `*Last updated: YYYY-MM-DD*` line under its title. Update the date when you change the page.
- Every merge to `main` raises the version. Run `python3 tools/version.py bump patch|minor|major "<summary>"` before you merge; the pre-push hook refuses a push to `main` without it.
- Add a changelog entry under **Unreleased** in `CHANGELOG.md`, grouped under Added, Changed, Fixed or Removed. Write each entry as one line: what changed and the problem it solves. No dates, incident stories, rule numbers or task ids. Full instructions: [Every merge raises the version](enforcement/DEVELOPER-GUIDE.md#121-every-merge-raises-the-version).
- The BuilderOS skills that the rules name are not copied here. Send fixes to them to [BuildGreatProducts/builder-os](https://github.com/BuildGreatProducts/builder-os).

## Reporting a false positive

1. Open an issue with the "A check stopped me wrongly" template.
2. Paste the refusal line and the code it refused.

A false positive is a bug in the scanner signature. The fix adds a `.pass` test file so the same mistake cannot come back.

## The documentation site

The site at [up-coast.github.io/coast-standards/](https://up-coast.github.io/coast-standards/) is built from the Markdown files in this repository. No page is copied and none has front matter, so each file reads the same on GitHub, on the site, and inside a project that adopted it. `mkdocs.yml` holds the navigation.

To build it locally:

```bash
pip install mkdocs==1.6.1 mkdocs-material==9.7.7
tools/build-docs.sh serve      # http://localhost:8000
tools/build-docs.sh            # build into site/
```

- The build runs with `--strict`, so a broken link fails it.
- The `docs` workflow runs the same build on every pull request and publishes on a push to `main`.
- When you add a page, add it to the nav in `mkdocs.yml` and to the staging list in `tools/build-docs.sh`.
