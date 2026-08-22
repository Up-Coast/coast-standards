# Client project full scope — FleetSignal example

Not a rule. This is a reference snapshot of everything delivered on the FleetSignal
engagement (client: Jay Hachkowski and David Falk) **outside** the frontend dashboard build
that was the formal ask — kept here so Abbey can pull it up when scoping what a client
project should include as a rule of thumb, without re-deriving it from git history each time.

Captured 2026-08-21 from `clients/fleetsignal` git history (95 commits) and repo state.

## 1. Backend hardening (before design started)

The client's original code was structurally sound but had gaps. Filled via a staged "R1–R5"
pass: build-the-database script, ingestion run history for auditability, the documented
scoring formula transcribed into code (never invented), the canonical per-vehicle status
function (with the founder-owned blend formula deliberately stubbed, not guessed), and the
full data layer + API the frontend talks to. Also: a real bug fix (`is None` vs `pd.isna()`
on a boundary check that was silently misclassifying high-risk vehicles as CLEARED) turned
into a standing project rule. Backed by a real test suite (77 pytest tests across 12 files).

## 2. Coding standards & product rules

A checkable rule corpus adopted from shared web/platform domain rules; a frontend rules doc
(DRY above all, every user-facing string externalized for localization, one theme file,
native HTML elements over div-widgets); a locked backend decisions doc; a glossary locking
terminology and its translations; a log of every default authored where the design was silent
so the client can veto it. Automated guard tests enforce string externalization, theme-only
styling, translation-key parity, and real `<table>` markup.

## 3. Security

Tenant auth via hashed tokens + constant-time comparison, never plaintext. Admin auth same
discipline, closed (401) by default if the secret is unset. A reversible-encryption vault
(Fernet) for the one case that needed a token re-displayed, kept strictly separate from the
hash-based auth path. OWASP security headers on both the API and the static site. CORS locked
to the exact deployed origin, no wildcards. Customer data never in version control.

## 4. Git / deployment infrastructure

A staging → production branch model where production only changes via a human clicking Merge
on a PR — enforced by a git hook that refuses direct pushes to main on every clone, not just
by convention. Full CI/CD: tests on every push/PR, automatic deploy on green, calendar-based
version tagging with auto-generated releases. Production infra: managed app host with an
encrypted volume, continuous off-site backup, static-site hosting for the frontend — all
written up in a deployment reference doc with a complete secrets table and a runbook for
moving to a new set of accounts. A visible "test server" banner that derives from the live
deployed version string, so staging can never be mistaken for production.

## 5. Analytics / usage tracking

A minimal, PII-free usage-events table and endpoint; the frontend fires events for page
visits and named actions; rolled into a summary the client can see so real usage data informs
decisions instead of guesses.

## 6. Localization / translation

Full bilingual (English/French) support built into the frontend from day one — one
translation namespace per screen, idiomatic regional translation seeded and confirmed against
the client's own vocabulary, a locked glossary so terms never drift. A third-language ask was
explicitly deferred (documented, not started) rather than scope-crept in.

## 7. Internal ops tooling (not part of the customer product)

A separate one-page status artifact built for the non-technical founders: production health,
test-server status, CI status, server status, product/usage counts, a one-click release
control — generated from real data sources (repo host, deploy host, admin API), never
fabricated placeholder numbers.

## 8. Handoff documentation

Plain-language guides so a non-technical founder (or a fresh agent session) can operate the
system without the person who built it: what changes, test server vs. production, the release
button, how to file a bug.

## Reading this as a rule of thumb

When scoping a client engagement that starts as "build the frontend" or "build feature X",
default to treating categories 1–4 above as generally in scope even when unstated — hardening
existing code, a real test suite, security on anything handling auth or customer data, and a
working deploy pipeline with a production guard are baseline production quality, not
upsells. Categories 5–8 (analytics, localization, internal ops tooling, handoff docs) are
scope calls to make explicitly per project, not assume — FleetSignal needed all four because
of its bilingual market and non-technical founders, but a different client may not.
