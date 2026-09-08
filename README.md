# Coast Standards

*Last updated: 2026-09-08*

Engineering rules for software built with AI coding agents, and the checks that enforce
them. Point an agent at this repository, or install it into a project, and the agent
knows how to work: what must stay DRY, where user-facing text lives, which imports are
forbidden, what a review must return, and what a commit or push is refused for.

The rules were extracted from building Coast, a macOS app that runs an
AI software team, and from the projects it builds. Coast is the reference implementation:
it installs this repository into every project it creates, and its own repository is held
by the same checks.

Three parts:

- **`rules/`** — the corpus. Numbered files that apply to every project, type files for
  services and pipelines, and one checkable rule document per platform (iOS, macOS,
  Android, React Native, Web, Python). Every rule names the check that holds it.
- **`enforcement/`** — the checks. A standard-library Python scanner with per-platform
  signature tables, a doc-comment check, a verifier that counts how many rules a check
  holds, shipped linter configs, three git hooks, hooks for Claude Code sessions, and
  `adopt.py`, which installs all of it into any project in one command.
- **`docs/`** — the public documentation for someone installing this into their product,
  in plain words.

Source-available, not open source: see [License](#license) below, and
[CONTRIBUTING.md](CONTRIBUTING.md) to change a rule or a check.

## Layout

| Path | What it is |
|---|---|
| `rules/PROJECT-TYPES.md` | **Which rules apply to your kind of project** — app, backend service, data/ML pipeline, library/CLI. Read this second, before applying anything to a project without a screen. |
| `rules/00-priority-rules.md` | The non-negotiables, in priority order. **DRY is the rule above all other rules.** Read this first, always. |
| `rules/01-working-style.md` | How agents work with the owner of a project: communication, verification, reporting, decisions |
| `rules/02-architecture-and-code.md` | Layering, SRP, naming, the DRY mechanics (all types); MVVM, reactive state and responsive layout (apps only) |
| `rules/03-security-owasp.md` | OWASP-derived security rules + sensitive-code handling |
| `rules/04-localization.md` | Why every app is built localizable from day one, and the Canadian defaults — **apps and frontends only**. The twelve checkable rules (L-1..L-12) live in each platform file since corpus version 8. |
| `rules/05-design-and-ui.md` | Reading design mocks, interaction rulings, copy rules, accessibility — **apps and frontends only**. The checkable token and component rules (DES-1..4, DRY-1..2) live in each platform file since corpus version 8. |
| `rules/06-testing.md` | Test types, TDD, false-passing patterns, what "coverage" means |
| `rules/07-documentation-git-process.md` | Docs, diagrams, decision logs, git and PR discipline |
| `rules/08-auditing-and-completeness.md` | How to audit: rebuild the list from the code, never review the list; audit the product's claims, not just its specs; **the case log of real audit misses and the mechanical check each one produces**. Read before any audit or "what's left" pass, and add to it whenever an audit misses something. |
| `rules/09-models-and-agents.md` | Model effort defaults (frugal, per role, never inherited), verifying which model is running, commit attribution, not dictating diffs into code you don't own |
| `rules/10-development-environment.md` | Atomic commands and permission prompts, disk hygiene, the cost of branch switching |
| `rules/types/backend-service.md` | The reasoning layer for services with no screen: layering without a UI, API contracts, async/workers, operability, data safety |
| `rules/types/data-and-ml.md` | Pipelines, scoring engines, and models: reproducibility, data-quality gates, model versioning, drift, presenting numbers honestly |
| `rules/platform/domain-rules-<platform>.md` | The per-platform checkable rule corpus (iOS, macOS, Android, React Native, Web, Python backend). Copy the one matching your target into the project. Since corpus version 8 (2026-09-04) every rule names the check that holds it (`[…; check: …]`), and the app files carry the DRY (DRY-1..7), strings (L-1..12) and design-token (DES-1..4) rules. |
| `rules/platform/ai-features.md` | The checkable rules for AI features (disclosure, consent and data flow, prompt injection, output handling, agency, cost, evaluation, logging, retrieval, supply chain, the store and EU gates) — own words citing OWASP AISVS chapters and the GenAI LLM Top 10 2026 ids. Copy it to `docs/ai-features-rules.md` when the app has AI features; Coast does this on the founder's say-so. |
| `docs/` | **The public documentation** — for a founder or developer installing this into their own product: what it is, the quickstart, how it works, what gets checked, the options, what to do when a check stops you, working with AI agents, FAQ. Plain words; nothing a maintainer-only reader needs. |
| `enforcement/` | **How these rules are enforced by checks** — the rules scanner (`checks/check_rules.py`, per-platform signature tables, path classes), the doc-comment check, the verifier that prints the honest number ("enforced by a check N of M"), the shipped linter configs (`lint/`), the three git hooks and the Claude Code session hooks (`hooks/`), and `adopt.py`, which installs all of it into any project. `docs/` is the public documentation for anyone installing this into their product (plain words: what it is, how to set it up, the options, what to do when a check stops you); `enforcement/DEVELOPER-GUIDE.md` is the internal guide for people working on the layer itself — every mode, flag, file and format; `enforcement/README.md` is the design and the build plan; read it before touching any rule's check. Built and proven on Coast's own repository and three shipped iOS apps (September 2026). |
| `.githooks/` | This repo's own pre-commit hook (CI runs the same two commands on every pull request): the enforcement checks' tests, then `verify_rules.py` against the committed gap baseline (the count may only fall). Install once per clone: `git config core.hooksPath .githooks`. |
| `CHECKS-VERSION` | The release number, one line. Every release is this number, the git tag `v<number>`, and an entry in `CHANGELOG.md`; projects record it in `.coast/standards-version`. |
| `CHANGELOG.md` | One entry per release, in plain words: what a project that upgrades will notice. The release workflow publishes the entry as the release notes. |
| `skills/adopt-coast-standards/` | This repo's own skill for AI coding agents: where the releases are and how to run the installer, nothing more. Copy the folder into `~/.claude/skills/` or a project's `.claude/skills/`. |
| `TEMPLATE-CLAUDE.md` | Paste-in starter block for a new project's CLAUDE.md |

## How to adopt in a new project

1. Decide the project's type from `rules/PROJECT-TYPES.md` (app · backend · data/ML ·
   library/CLI) — a project with a frontend and an API is two types, one per part — and
   name it in the project's `CLAUDE.md` so no session has to guess which rules apply.
2. Copy `TEMPLATE-CLAUDE.md` content into the project's `CLAUDE.md` and fill in the blanks.
3. Copy the matching `rules/platform/domain-rules-<platform>.md` to `docs/domain-rules.md`
   in the project and edit it to fit (delete inapplicable sections, add product-specific
   rules — keep every rule checkable: a reviewer must be able to answer "does this change
   break the rule — yes or no?").
4. Install the BuilderOS skills (see "Built on BuilderOS" below):
   `npx skills add BuildGreatProducts/builder-os`. The rules assume the Claude Code build
   loop, `design-better` and `design-system` are present.
5. The numbered files in `rules/` are read in place — reference this repo's path from the
   project CLAUDE.md rather than copying them, so improvements land everywhere at once.
6. Run `python3 enforcement/adopt.py <project-dir> --measure-tools` (`--dry-run` first if
   you like). The installer can be run from a fetched release rather than a clone: the
   [quickstart](docs/quickstart.md) has the one command that fetches the newest release
   into `~/.cache/coast-standards/<version>/`. It installs the checks under `.coast/checks/`, the
   three git hooks under `.githooks/` with `core.hooksPath` set, the Claude Code session
   hooks (`.coast/hooks/claude-hook.py` and `.claude/settings.json`), the platform's
   linter seeds, `docs/domain-rules.md` when the project has none, the baselines and the
   config under `.coast/`, and the standards block in the project's `CLAUDE.md` with the
   "enforced by a check" number. A first install at a terminal asks the on/off questions
   once — one screen each for the rules, the push-gate seats and the session hooks, every
   default on, Enter takes them all — and writes the answers to `.coast/config.json`; `--yes`
   skips the questions, `--init` asks them again, `--owner "Pat Lee" --product "Example App"`
   fills the names every refusal sentence uses. `--measure-tools` builds the project once so an existing repository's
   warnings, formatter and linter findings — and a missing test target — start as
   baselines instead of refusing the first push. Re-run it to take a newer version — it
   replaces governed files, keeps anything you edited, lowers a baseline that fell, and
   changes nothing when nothing changed, and `--release <version>` (or `latest`) fetches
   another release and installs from it. The programs the hooks expect are listed in
   `enforcement/TOOLCHAIN.md`.

## How enforcement works, in one screen

Every rule in `rules/` ends with a `[check: …]` tag naming what holds it, and the tag
puts the rule in one of five bins — **machine** (a check refuses the change: the scanner,
the linter with the shipped config, a tool the push gate runs, a hook), **partly** (a
machine check and a reviewer share it), **advisory** (the scanner reports it, nothing
fails), **reviewer** (only a mind can judge it; every review returns a row per rule with
evidence), **process** (held by the pipeline or by a person). `verify_rules.py` counts the
bins and fails the commit when a rule names no check or names one nothing runs; the
corpus stands at **enforced by a check 170 of 643** (4 September 2026), and each project's
own number comes from its `docs/domain-rules.md`.

A rule whose check a person switched off in `.coast/config.json` is counted as **switched
off**, never as enforced: the number reads "24 of 74 (3 switched off)", because the number
is honest or it is nothing.

What refuses, and where: `.githooks/pre-commit` (the scanner on the staged diff — added
lines only, in seconds), `.githooks/commit-msg` (a subject under 100 characters; an agent
session's commit names its model), `.githooks/pre-push` (build, tests, lint, format, the
scanner on everything added since the remote and on the whole tree, the doc-comment count,
jscpd, the protected-main ruleset), and the Claude Code hooks in `.claude/settings.json`
(no edits to the files that define the checks, no `cd X && …` chains, no infrastructure
commands, no `--no-verify` or force-push, the staged scan before a commit, the scanner on
every edited file, no ending a turn with unpushed work).

An existing repository adopts without a rewrite day: the counts of what it already
violates — the scanner's ratchets, the build's warnings, the formatter's and linter's
findings, a missing test target — are written once to `.coast/ratchet-baseline.json` with
a 90-day deadline. A change may lower a count, never raise it; past the deadline the check
blocks. Never `--no-verify`; the governed files are not an agent's to edit.

## Built on BuilderOS

The product-side skills these rules assume come from
[BuilderOS](https://github.com/BuildGreatProducts/builder-os) by Build Great Products (MIT).
Planning a product, running the build loop, designing well and generating a design
system are solved problems there, and the skills work. There is no reason to redo that
work here, so this repository does not copy them. Install them once, and keep them
current from the source:

```bash
npx skills add BuildGreatProducts/builder-os
```

Three of them are named by the rules: `build-loop-claude-code` (the build → review → test
→ fix loop in the git-process rules), `design-better` (the craft layer under the design
rules) and `design-system` (token generation). The rest are worth having too.

## Releases

Every release is a semantic version in `CHECKS-VERSION`, a git tag `v<number>`, and an
entry in `CHANGELOG.md`; the release workflow refuses a tag that does not match the file
or has no changelog entry, then publishes a GitHub release with that entry. Each project
holds its own copy of the rules and the checks, like a dependency, and records the
release it carries in `.coast/standards-version`. Nobody needs a clone to adopt: the
installer is fetched from the newest release tarball, and any installed copy can fetch
another release with `--release`. Contributors clone the repository; adopters do not.

## License

Coast Standards is source-available under its own license, [LICENSE.md](LICENSE.md),
not an open-source license. In plain words: you may use it, including in a business,
to build and ship your own software, and you may share it unchanged with the notice
kept. You may change the copies the installer puts in your project, because that is
how it works. You may not sell it, publish a changed version as the standards, or
build a product or service whose main value comes from it, such as an assistant or a
checking service wrapped around the rules and checks. Contributions are welcome and
become part of the standards under the same license. The reason for the choice: the
rules are meant to be adopted as written, and the checks are the product.

## Provenance

- The numbered `rules/` files were extracted from the rules Coast's own development
  followed: its agent context, its capture log of decisions, and its design-conformance
  rulings. Each rule keeps its origin story where one exists, so the reason travels with
  the rule.
- The five app-platform files in `rules/platform/` (iOS, macOS, Android, React Native,
  Web) are the corpus Coast ships into the projects it builds. Each carries a version
  stamp on its first line (`<!-- coast-rules-version: N -->`): a project's copy is never
  auto-updated. Coast offers a newer version with the changes in plain words, and the
  founder takes it with an explicit click.
- **The numbered `rules/` files are NOT all universal.** They were extracted from an app
  project, and several assume a screen. `PROJECT-TYPES.md` says exactly which apply to
  which kind of project; the app-only files carry an applicability header.
- `rules/platform/domain-rules-python.md` (Python backends and services) was written for
  backend work and is not part of the corpus Coast ships, which covers mobile and web
  targets only. If Coast ever ships a Python target, the two must be reconciled.
- `rules/08-auditing-and-completeness.md` was written from a real completeness-sweep
  failure it describes.

Newer decisions win: when a rule here conflicts with a newer instruction from the owner of
the project, the newer instruction wins, and the fix is to update this repository in the
same session rather than leave the stale rule standing.
