# Localization

Read this when a task adds or changes user-facing text in an app or frontend (type A). Backends keep messages in one place (`types/backend-service.md`).

## The rules (L)

Rules **L-1 to L-12** live in the platform rules document (`rules/platform/domain-rules-<platform>.md`, a project's `docs/domain-rules.md`), not here. Build every project with a user interface localizable from the first commit, even with one language planned. [check: context]

## Canadian defaults

A product sold across Canada ships English and Québec French; Bill 96 makes French a legal requirement for much business software. A trucking or fleet product adds Punjabi as the third language. Punjabi uses Gurmukhi script, left-to-right, with no uppercase (see L-12). It needs Unicode shaping and a Gurmukhi fallback font such as Noto Sans Gurmukhi. Domain terms need a translator who knows the domain. [check: process]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
