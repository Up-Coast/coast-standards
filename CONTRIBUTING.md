# Contributing

*Last updated: 2026-09-07*

Coast Standards is a rule corpus and the checks that enforce it. Changes are welcome to
both, and the bar is the same for each: a rule is not done until a check holds it, and a
check is not done until a test proves what it refuses and what it lets through.

## The license, in one sentence

Coast Standards is source-available under [LICENSE.md](LICENSE.md). By submitting a
change you license it to the project's owner for inclusion, as section 5 of the license
says, and you keep the copyright in what you wrote.

## Before you start

1. Read `rules/00-priority-rules.md`. It is short and it governs this repository too.
2. Install the pre-commit hook once per clone. It runs the verifier and the tests:

```bash
git config core.hooksPath .githooks
```

3. Run the tests once so you know the starting state (about two minutes):

```bash
python3 -m unittest discover -s enforcement/checks/tests -p 'test_*.py'
```

Everything here is standard-library Python 3. There is nothing to install.

## Changing or adding a rule

- Every rule ends with a `[…; check: …]` tag naming what holds it. The verifier
  (`enforcement/checks/verify_rules.py`) refuses a rule that names no check, or names a
  check that nothing runs. The committed baseline of gaps may only fall.
- A rule that a machine can hold gets a scanner signature in
  `enforcement/checks/rules_signatures.json`, with a `.fail` and a `.pass` plant under
  `enforcement/checks/tests/plants/<platform>/`. A rule only a person can judge is tagged
  `check: review`.
- Rule ids (`DRY-3`, `L-7`, `SEC-12`) are stable. Never renumber; retire an id and add a
  new one.
- The per-platform files under `rules/platform/` carry a version stamp on their first
  line. Bump it when a rule changes meaning, not for wording.
- Write in plain words. State the rule, then the reason. No marketing, no summaries at
  the end of a section.

## Changing a check

- `enforcement/DEVELOPER-GUIDE.md` describes every mode, flag, file and output format.
  `enforcement/README.md` is the design and the reasons behind it. Read the relevant
  section before changing behaviour.
- Output format is load-bearing: `FAIL <check> <path>:<id>: <words>`. Hooks, CI and the
  reference implementation parse it.
- Every behaviour change ships with a test in `enforcement/checks/tests/`.

## Pull requests

- One change per pull request. A subject line under 100 characters that says what
  changed, in words.
- CI runs the verifier and the tests on Linux and macOS. Both must be green.
- Every documentation page carries a `*Last updated: YYYY-MM-DD*` line under its title.
  Move the date when you change the page.
- The BuilderOS skills the rules name are not copied here. A fix to one of them goes to
  [BuildGreatProducts/builder-os](https://github.com/BuildGreatProducts/builder-os).

## Reporting a false positive

Open an issue with the "A check stopped me wrongly" template. Paste the refusal line and
the code it refused. A false positive is a defect in the signature, and it gets a `.pass`
plant so it cannot come back.

## The documentation site

The site at [up-coast.github.io/coast-standards/](https://up-coast.github.io/coast-standards/) is built from the markdown already in
the repository — no page is copied and none carries front matter, so the same file reads
correctly on GitHub, on the site, and inside a project that adopted it. `mkdocs.yml` holds
the nav.

```bash
pip install mkdocs==1.6.1 mkdocs-material==9.7.7
tools/build-docs.sh serve      # http://localhost:8000
tools/build-docs.sh            # build into site/
```

The build runs `--strict`, so a link that does not resolve fails it. The `docs` workflow
runs the same build on every pull request, and publishes on a push to `main`. When you add
a page, add it to the nav in `mkdocs.yml` and to the staging list in `tools/build-docs.sh`.
