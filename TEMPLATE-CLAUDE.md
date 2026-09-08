# <Project name> — Agent Context

<!-- Starter CLAUDE.md block for a new project that follows Coast Standards. Copy into the project's CLAUDE.md,
     fill the blanks, delete these comments. -->

## Standing rules (read before any work)

This project follows the Coast Standards repo, cloned at `<path to your clone>`
(GitHub: Up-Coast/coast-standards).

Read `rules/00-priority-rules.md` first — the non-negotiables, headed by: **the project
must stay DRY (rule above all other rules), all user-facing strings externalized for
localization, all design components created once and reused, OWASP rules followed.**

Then, as the work demands: `01-working-style.md` (always), `02-architecture-and-code.md`,
`03-security-owasp.md`, `04-localization.md`, `05-design-and-ui.md`, `06-testing.md`,
`07-documentation-git-process.md`.

This project's checkable rule corpus lives at `docs/domain-rules.md` (seeded from
`rules/platform/domain-rules-<PLATFORM>.md`). Reviews check every change against exactly
that file.

The enforcement block — what the git and Claude Code hooks refuse, the "rules enforced by a
check N of M" number, the governing files — is written and kept current by
`enforcement/adopt.py` between `coast-standards: begin` / `end` markers; do not write
it by hand, and edit this file outside those markers only.

## This project

- **What it is:** <one paragraph>
- **Platform / stack:** <e.g. web: React + TypeScript + Vite; see domain-rules-web.md>
- **Design source of truth:** <path to design package / design.md>
- **Locales:** <e.g. en, fr from day one; keys semantic; glossary at docs/glossary.md>
- **Repo:** <org/name, branch model>
- **Run / test:** <commands>

## Project-specific rules

<!-- Only rules NOT already covered by the standards repo. Cite who decided and when. -->

## Current state / entry point

<!-- Where a fresh session should start: plan doc, next task, known gaps. -->
