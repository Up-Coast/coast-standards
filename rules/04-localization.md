# Localization

> **Applies to:** project type A — apps and frontends with user-facing text. A backend,
> pipeline, or CLI satisfies priority rule 2 through the one-home-for-messages rule in
> `types/backend-service.md` instead. See `PROJECT-TYPES.md`.

Every project with a user interface is built localizable from day one, whether or not a second language is
scheduled. Retrofitting string externalization is expensive; doing it from the first commit
is free. (This section closes a known gap: Coast's shipped per-platform corpus has no L-*
section even though Coast enforces these rules internally via its strings specialist.)

## The rules (L)

The twelve checkable rules — **L-1 to L-12** — live in every app platform rules document
(`rules/platform/domain-rules-<platform>.md`, a project's `docs/domain-rules.md`), each with
the check that holds it named: no hardcoded user-facing text (L-1), one catalog per locale
(L-2), semantic keys (L-3), no concatenated sentences (L-4), the platform's plural system
(L-5), locale-aware formatters (L-6), room for text expansion (L-7), tooling-managed plumbing
(L-8), approved domain vocabulary (L-9), a translation path for data-sourced text (L-10), a
visible and persistent language choice (L-11), and casing at render time (L-12). They live
there, not here, so a project has exactly one rules document and one counted number.
[check: context]

## Canadian defaults

For products sold across Canada, English + French (Québec French — Bill 96 makes it a legal
requirement for many business software contexts) is the default language pair. Punjabi is
the evidence-backed third language for trucking/fleet products (majority of drivers in the
Toronto and Vancouver areas; heavy ownership representation). Punjabi is written in Gurmukhi:
left-to-right (no RTL work), needs proper Unicode shaping (free on modern browsers/OSes), a
Gurmukhi-capable font fallback (e.g. Noto Sans Gurmukhi), and has no uppercase — see L-12.
Translation quality for domain terminology needs a domain-aware translator, not a generic
vendor. [check: process]
