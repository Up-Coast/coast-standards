# Localization

> **Applies to:** project type A, apps and frontends with user-facing text. A backend, pipeline or CLI meets priority rule 2 through the rule in `types/backend-service.md` that keeps all messages in one place. See `PROJECT-TYPES.md`.

Build every project with a user interface so it can be localized from day one, even if no second language is planned. Moving strings out of code later is expensive; doing it from the first commit costs nothing.

## The rules (L)

The twelve checkable rules, **L-1 to L-12**, are in every app platform rules document (`rules/platform/domain-rules-<platform>.md`, which becomes a project's `docs/domain-rules.md`). Each names the check that enforces it. In short: no hardcoded user-facing text (L-1); one catalog per locale (L-2); keys named by meaning (L-3); no sentences built by joining strings (L-4); the platform's plural system (L-5); locale-aware formatters (L-6); room for longer translated text (L-7); localization plumbing managed by tooling (L-8); approved domain vocabulary (L-9); a translation path for text that comes from data (L-10); a visible language choice that is remembered (L-11); and changing letter case at display time (L-12). They live there, not here, so a project has one rules document and one count of rules.
[check: context]

## Canadian defaults

For products sold across Canada, the default language pair is English and French (Québec French; Bill 96 makes it a legal requirement for many business software contexts). For trucking and fleet products, evidence supports Punjabi as the third language: most drivers in the Toronto and Vancouver areas speak it, and many fleet owners do too. Punjabi is written in Gurmukhi. It is left-to-right (no RTL work). It needs proper Unicode shaping (built into modern browsers and operating systems) and a Gurmukhi-capable fallback font (for example Noto Sans Gurmukhi). It has no uppercase; see L-12. Domain terminology needs a translator who knows the domain, not a generic vendor. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
