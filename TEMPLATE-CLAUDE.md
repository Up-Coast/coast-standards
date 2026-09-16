# <Project name> — Agent Context

<!-- Starter CLAUDE.md for a new project that follows Coast Standards. Copy it into the project's CLAUDE.md, fill in the blanks, and delete these comments. -->

## Standing rules (read before any work)

This project follows the Coast Standards repo, cloned at `<path to your clone>` (GitHub: Up-Coast/coast-standards).

Read `rules/00-priority-rules.md` first. Its most important rules:

- **Keep the project DRY.** This rule comes before all others.
- **Put every user-facing string in the localization files.**
- **Create each design component once and reuse it.**
- **Follow the OWASP rules.**

Always read `01-working-style.md`. Read the others when the work touches their area: `02-architecture-and-code.md`, `03-security-owasp.md`, `04-localization.md`, `05-design-and-ui.md`, `06-testing.md`, `07-documentation-git-process.md`.

This project's checkable rules are in `docs/domain-rules.md`, copied from `rules/platform/domain-rules-<PLATFORM>.md`. Reviews check every change against exactly that file.

`enforcement/adopt.py` writes and updates a block in this file between the `coast-standards: begin` and `end` markers. That block lists what the git and Claude Code hooks refuse, the "rules enforced by a check: N of M" number, and the files agents may not edit. Do not write it by hand. Only edit this file outside those markers.

## This project

- **What it is:** <one paragraph>
- **Platform / stack:** <e.g. web: React + TypeScript + Vite; see domain-rules-web.md>
- **Design source of truth:** <path to design package / design.md>
- **Locales:** <e.g. en, fr from day one; keys semantic; glossary at docs/glossary.md>
- **Repo:** <org/name, branch model>
- **Run / test:** <commands>

## Project-specific rules

<!-- Only rules the standards repo does not already cover. Note who decided each one and when. -->

## Current state / entry point

<!-- Where a fresh session should start: plan doc, next task, known gaps. -->
