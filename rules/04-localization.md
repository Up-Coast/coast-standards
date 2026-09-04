# Localization

> **Applies to:** project type A — apps and frontends with user-facing text. A backend,
> pipeline, or CLI satisfies priority rule 2 through the one-home-for-messages rule in
> `types/backend-service.md` instead. See `PROJECT-TYPES.md`.

Every project with a user interface is built localizable from day one, whether or not a second language is
scheduled. Retrofitting string externalization is expensive; doing it from the first commit
is free. (This section closes a known gap: Coast's shipped per-platform corpus has no L-*
section even though Coast enforces these rules internally via its strings specialist.)

## The rules (L)

- **L-1 — No hardcoded user-facing text, anywhere.** Every user-visible string lives in the
  string catalog / locale resource files under a named key. This includes error messages,
  empty states, loading text, tooltips, accessibility labels, page titles, email/notification
  copy, and units. A guard check (test or lint) fails the build on any bare user-facing
  literal in view/component code. [Coast D36; CoastCopy guard-test pattern; check:
  scan:ui-string-literal]
- **L-2 — One catalog home per locale.** `locales/<lang>/…` (web) or the platform's string
  catalog. The strings surface is sole-authority: additions go through one place, and reuse
  comes first — when an existing key already carries the needed text, use that key instead
  of adding a near-duplicate. [check: scan:one-catalog-per-locale]
- **L-3 — Keys are semantic, not English.** `vehicle.status.doNotDispatch`, not
  `do_not_dispatch_text`. The key names the meaning so translations can diverge from English
  phrasing. [check: scan:english-key]
- **L-4 — Never build sentences by concatenation.** Use the platform's interpolation with
  named placeholders (ICU MessageFormat / i18n interpolation); word order differs across
  languages. Templates with placeholders are themselves catalog entries.
  [check: scan:ui-string-concat]
- **L-5 — Plurals via the platform's plural system** (CLDR categories: zero/one/two/few/
  many/other), never `if count == 1` in code. [Coast CoastStrings/CLDR one-home
  precedent; check: scan:manual-plural]
- **L-6 — Dates, numbers, and currency are formatted by locale-aware formatters**, never by
  string templates. [check: review]
- **L-7 — Layouts tolerate ~30% text expansion.** No fixed-width text containers that clip;
  test with long-string locales (German), pseudo-localization, and — when in scope — RTL.
  "UI must survive the strings/localization specialist's output." [Coast D60;
  check: review]
- **L-8 — Localization plumbing is emitted/managed by tooling, never hand-authored** where
  the platform provides it (String Catalogs, ICU files). Hand-author the content, not the
  plumbing. [check: review]
- **L-9 — Domain vocabulary translates with approval.** Safety-critical or client-owned
  terms (status tiers, legal words) get approved translations treated as verbatim — an agent
  never freelances them. Keep a glossary file per project listing terms whose translations
  are locked. [check: review]
- **L-10 — Data-sourced text needs a translation path too.** Text that reaches the UI from
  a database or API (descriptions, reference data) is part of the localization surface:
  either the source provides per-locale columns/fields, or the UI maps stable codes/IDs to
  catalog keys. Never assume "strings from the backend don't count."
  [check: review]
- **L-11 — The language choice is user-visible, instant, and persistent.** Switching locale
  never requires a reload of anything the user typed; the choice persists (profile, local
  storage, or URL parameter as the product dictates). [check: review]
- **L-12 — All-caps and letter-spacing effects are applied via CSS/text-transform at render
  time**, not baked into the stored string — casing rules differ per language (and some
  scripts have no case at all). [check: scan:baked-case]

## Canadian defaults

For products sold across Canada, English + French (Québec French — Bill 96 makes it a legal
requirement for many business software contexts) is the default language pair. Punjabi is
the evidence-backed third language for trucking/fleet products (majority of drivers in the
Toronto and Vancouver areas; heavy ownership representation). Punjabi is written in Gurmukhi:
left-to-right (no RTL work), needs proper Unicode shaping (free on modern browsers/OSes), a
Gurmukhi-capable font fallback (e.g. Noto Sans Gurmukhi), and has no uppercase — see L-12.
Translation quality for domain terminology needs a domain-aware translator, not a generic
vendor. [check: process]
