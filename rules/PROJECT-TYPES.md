# Which rules apply to your project

Read this when setting a project up or deciding which rules apply.

## The project types

- **A — App with a UI**: anything a person taps or clicks (iOS, Android, React Native, macOS, web frontend).
- **B — Backend service**: API, worker or job with no screen.
- **C — Data / ML pipeline**: ingestion, transformation, scoring, models.
- **D — Library, CLI, or internal tool**: code other developers use.

A project can be several types; say which part you are working in, and follow that part's rules.

## What applies where

Files 01, 03, 06, 07, 08, 09 and 10 apply to every type; type C also reads `types/data-and-ml.md` with 06.

| Rules file | A | B | C | D |
|---|---|---|---|---|
| `00-priority-rules.md` | all | rule 2 scoped | rule 2 scoped | rule 2 scoped |
| `02-architecture-and-code.md` | all | partly | partly | partly |
| `04-localization.md` | yes | no | no | only if it emits user-facing text |
| `05-design-and-ui.md` | yes | no | no | no |
| `types/backend-service.md` | no | yes | yes | no |
| `types/data-and-ml.md` | no | no | yes | no |
| `platform/domain-rules-<platform>.md` | yours | python | python | yours |

## The scoping notes

- **Rule 2** for B, C, D: text a person reads (API errors, emails, notifications, CLI output) lives in one place, per `types/backend-service.md`. No localization catalog.
- **02** for B, C, D: skip the MVVM split, reactive state, responsive layout and "nothing blocking is callable from the UI". All else applies, including every DRY rule. B and C take equivalents from `types/backend-service.md`.
- **Rule 8** applies to every type: a backend uses the framework's DI, migrations, validation and task queue.
- **Checks**: `enforcement/adopt.py` installs the same tooling for every type; the platform file picks which checks apply. The `CLAUDE.md` "enforced by a check N of M" line counts from the project's `docs/domain-rules.md`.
- **Security**: apps focus on storage, transport and permissions; backends on per-endpoint authorization, injection and secrets. Read `03-security-owasp.md`, then the platform file.

## When a project doesn't fit

Add a new type file rather than stretching one: say what it covers, which rules it narrows or replaces, and why. A rule explained away on every use is in the wrong file.

---

[← All rules](README.md) · [Documentation](../docs/README.md)
