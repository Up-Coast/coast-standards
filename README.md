# Up Coast Standards

The standing engineering rules for every project Abbey Jackson (Up Coast) builds with AI
agents. This repo exists so no session ever has to be told these rules again: point an agent
here (or copy the files in) and it knows how to work.

Extracted 20 August 2026 from the Coast project — both the rules Abbey has demanded while
building Coast itself and the rules Coast enforces on the apps it builds — plus the
open-source BuilderOS skill set that Coast's build loop wraps.

## Layout

| Path | What it is |
|---|---|
| `rules/PROJECT-TYPES.md` | **Which rules apply to your kind of project** — app, backend service, data/ML pipeline, library/CLI. Read this second, before applying anything to a project without a screen. |
| `rules/00-priority-rules.md` | The non-negotiables, in priority order. **DRY is the rule above all other rules.** Read this first, always. |
| `rules/01-working-style.md` | How agents work with Abbey: communication, verification, reporting, decisions |
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
| `enforcement/` | **How these rules are held by machines** — the rules scanner (`checks/check_rules.py`, per-platform signature tables, path classes), the doc-comment check, the verifier that prints the honest number ("held by a machine N of M"), the shipped linter configs (`lint/`), the three git hooks and the Claude Code session hooks (`hooks/`), and `adopt.py`, which installs all of it into any project. `enforcement/DEVELOPER-GUIDE.md` is the manual — every mode, flag, file and format, how to adopt, excuse, extend and troubleshoot; `enforcement/README.md` is the design and the build plan; read it before touching any rule's check. Built and proven on Coast's own repository and Abbey's three app repositories (September 2026). |
| `.githooks/` | This repo's own pre-commit hook: the enforcement checks' tests, then `verify_rules.py` against the committed gap baseline (the count may only fall). Install once per clone: `git config core.hooksPath .githooks`. |
| `examples/` | Reference snapshots of real engagements — not rules, just what a project actually delivered, kept for scoping future client work by rule of thumb |
| `skills/` | The BuilderOS skills (BuildGreatProducts/builder-os, MIT), vendored verbatim |
| `skills-lock.json` | Pins each vendored skill to its source commit + SHA-256, matching Coast's pattern |
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
4. Copy the skills you want from `skills/` into the project's `.claude/skills/` (or run
   `npx skills add BuildGreatProducts/builder-os` for fresh upstream copies). The build loop
   for Claude Code sessions is `skills/build-loop-claude-code/`.
5. The numbered files in `rules/` are read in place — reference this repo's path from the
   project CLAUDE.md rather than copying them, so improvements land everywhere at once.
6. Run `python3 enforcement/adopt.py <project-dir> --measure-tools` (from this repo;
   `--dry-run` first if you like). It installs the checks under `Scripts/checks/`, the
   three git hooks under `.githooks/` with `core.hooksPath` set, the Claude Code session
   hooks (`Scripts/hooks/claude-hook.py` and `.claude/settings.json`), the platform's
   linter seeds, `docs/domain-rules.md` when the project has none, the baselines under
   `.coast/`, and the standards block in the project's `CLAUDE.md` with the "held by a
   machine" number. `--measure-tools` builds the project once so an existing repository's
   warnings, formatter and linter findings — and a missing test target — start as
   baselines instead of refusing the first push. Re-run it to take a newer version — it
   replaces governed files, keeps anything you edited, lowers a baseline that fell, and
   changes nothing when nothing changed. The programs the hooks expect are listed in
   `enforcement/TOOLCHAIN.md`.

## How enforcement works, in one screen

Every rule in `rules/` ends with a `[check: …]` tag naming what holds it, and the tag
puts the rule in one of five bins — **machine** (a check refuses the change: the scanner,
the linter with the shipped config, a tool the push gate runs, a hook), **partly** (a
machine check and a reviewer share it), **advisory** (the scanner reports it, nothing
fails), **reviewer** (only a mind can judge it; every review returns a row per rule with
evidence), **process** (held by the pipeline or by a person). `verify_rules.py` counts the
bins and fails the commit when a rule names no check or names one nothing runs; the
corpus stands at **held by a machine 170 of 643** (4 September 2026), and each project's
own number comes from its `docs/domain-rules.md`.

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

## Provenance

- Category A sources (rules governing agents working for Abbey): Coast's `CLAUDE.md`, the
  App-Engineering-Framework capture log and domain docs, the design-conformance standing
  rulings, and Abbey's global `~/.claude/CLAUDE.md`. Load-bearing rules keep Abbey's verbatim
  words, marked as quotes.
- Category B sources (rules Coast enforces on the apps it builds): Coast's
  `Templates/rules/` corpus, the specialist agent system prompts, the reviewer gates, and the
  deterministic CI checks. The five app-platform files in `rules/platform/` (iOS, macOS,
  Android, React Native, Web) are byte-for-byte copies of the shipped corpus. Each carries
  Coast's version stamp on its first line (`<!-- coast-rules-version: N -->`, since
  2026-08-21): a project's copy is never auto-updated — Coast offers a newer version with
  the changes in plain words, and the founder takes it with an explicit click.
- **The numbered `rules/` files are NOT all universal.** They were extracted from an app
  project, and several assume a screen. `PROJECT-TYPES.md` says exactly which apply to
  which kind of project; the app-only files carry an applicability header. (Corrected
  20 August 2026 — an earlier version of this README claimed they were language-agnostic,
  which was wrong.)
- `rules/platform/domain-rules-python.md` (Python backends and services) is Up Coast
  standards, **not** part of Coast's shipped corpus — Coast builds mobile and web app
  targets, so it has no Python rules doc to copy. Added 20 August 2026 for client backend
  work. If Coast ever ships a Python target, that corpus and this file must be reconciled.
- `rules/08-auditing-and-completeness.md` is Up Coast standards, written 20 August 2026 from
  the Coast completeness-sweep failure it describes.
- `examples/fleetsignal-full-scope.md` is Up Coast standards, added 21 August 2026: a
  reference list of everything delivered on the FleetSignal client engagement outside its
  frontend build (backend hardening, standards docs, security, deploy infra, analytics,
  localization, ops tooling, handoff docs), kept for scoping future client projects.
- `skills/` is vendored from [BuildGreatProducts/builder-os](https://github.com/BuildGreatProducts/builder-os)
  (MIT — license retained at `skills/BUILDEROS-LICENSE.txt`), pinned in `skills-lock.json`.
  Per Coast's rule, vendored skills are flag-don't-edit; local fixes go upstream or into a
  separately named skill.

Newer decisions win: when a rule here conflicts with something Abbey says in a session, her
newer instruction wins — and the fix is to update this repo in the same session, not to leave
the stale rule standing.
