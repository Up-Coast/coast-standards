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
| `rules/04-localization.md` | String externalization and localization — **apps and frontends only** |
| `rules/05-design-and-ui.md` | Design tokens, component reuse, reading design mocks, copy rules, accessibility — **apps and frontends only** |
| `rules/06-testing.md` | Test types, TDD, false-passing patterns, what "coverage" means |
| `rules/07-documentation-git-process.md` | Docs, diagrams, decision logs, git and PR discipline |
| `rules/08-auditing-and-completeness.md` | How to audit: rebuild the list from the code, never review the list. Read before any audit or "what's left" pass. |
| `rules/09-models-and-agents.md` | Model effort defaults (frugal, per role, never inherited), verifying which model is running, commit attribution, not dictating diffs into code you don't own |
| `rules/10-development-environment.md` | Atomic commands and permission prompts, disk hygiene, the cost of branch switching |
| `rules/types/backend-service.md` | The reasoning layer for services with no screen: layering without a UI, API contracts, async/workers, operability, data safety |
| `rules/types/data-and-ml.md` | Pipelines, scoring engines, and models: reproducibility, data-quality gates, model versioning, drift, presenting numbers honestly |
| `rules/platform/domain-rules-<platform>.md` | The per-platform checkable rule corpus (iOS, macOS, Android, React Native, Web, Python backend). Copy the one matching your target into the project. |
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

## Provenance

- Category A sources (rules governing agents working for Abbey): Coast's `CLAUDE.md`, the
  App-Engineering-Framework capture log and domain docs, the design-conformance standing
  rulings, and Abbey's global `~/.claude/CLAUDE.md`. Load-bearing rules keep Abbey's verbatim
  words, marked as quotes.
- Category B sources (rules Coast enforces on the apps it builds): Coast's
  `Templates/rules/` corpus, the specialist agent system prompts, the reviewer gates, and the
  deterministic CI checks. The five app-platform files in `rules/platform/` (iOS, macOS,
  Android, React Native, Web) are byte-for-byte copies of the shipped corpus.
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
- `skills/` is vendored from [BuildGreatProducts/builder-os](https://github.com/BuildGreatProducts/builder-os)
  (MIT — license retained at `skills/BUILDEROS-LICENSE.txt`), pinned in `skills-lock.json`.
  Per Coast's rule, vendored skills are flag-don't-edit; local fixes go upstream or into a
  separately named skill.

Newer decisions win: when a rule here conflicts with something Abbey says in a session, her
newer instruction wins — and the fix is to update this repo in the same session, not to leave
the stale rule standing.
