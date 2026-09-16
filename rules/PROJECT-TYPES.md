# Which rules apply to your project

*Last updated: 2026-09-16*

Read this before applying the rules to a project that is not an app with a user interface. **Not every rule makes sense for every project.** UI rules applied to a headless service only create noise, and noise teaches people to ignore rules.

The numbered rules are not language- or project-neutral. They were written for an app, and several assume a screen. This page says which ones apply to your kind of project.

## The project types

| Type | What it is | Examples |
|---|---|---|
| **A — App with a UI** | Anything a person looks at and taps or clicks | iOS, Android, React Native, macOS, a web frontend |
| **B — Backend service** | An API, worker, or job with no screen of its own | A Python or Node API, a queue worker, a scheduled job |
| **C — Data / ML pipeline** | Ingestion, transformation, scoring, models | A scoring engine, an ETL pipeline, a training job |
| **D — Library, CLI, or internal tool** | Code other developers use | A shared package, a command-line utility, a build script |

Many projects are more than one type. A product with a web frontend and a Python API is A **and** B, and each part follows its own rules. Say which part you are working in before you apply a rule.

## What applies where

| Rules file | A · App | B · Backend | C · Data/ML | D · Library/CLI |
|---|---|---|---|---|
| `00-priority-rules.md` | ✅ all | ✅ (rule 2 scoped — see below) | ✅ (rule 2 scoped) | ✅ (rule 2 scoped) |
| `01-working-style.md` | ✅ | ✅ | ✅ | ✅ |
| `02-architecture-and-code.md` | ✅ all | ⚠️ partly — see below | ⚠️ partly | ⚠️ partly |
| `03-security-owasp.md` | ✅ | ✅ | ✅ | ✅ |
| `04-localization.md` | ✅ | ❌ — see below | ❌ | ❌ unless it emits user-facing text |
| `05-design-and-ui.md` | ✅ | ❌ | ❌ | ❌ |
| `06-testing.md` | ✅ | ✅ | ✅ + `types/data-and-ml.md` | ✅ |
| `07-documentation-git-process.md` | ✅ | ✅ | ✅ | ✅ |
| `08-auditing-and-completeness.md` | ✅ | ✅ | ✅ | ✅ |
| `09-models-and-agents.md` | ✅ | ✅ | ✅ | ✅ |
| `10-development-environment.md` | ✅ | ✅ | ✅ | ✅ |
| `types/backend-service.md` | — | ✅ | ✅ | — |
| `types/data-and-ml.md` | — | — | ✅ | — |
| `platform/domain-rules-<platform>.md` | pick yours | `domain-rules-python.md` | `domain-rules-python.md` | pick yours |

## The scoping notes

**Priority rule 2 (never hardcode user-facing text)** is for projects with an interface. A backend, pipeline or CLI has little or no user-facing text, and a localization catalog would be needless overhead. The backend version does apply: any text a person will read (API error messages, emails, notifications, CLI output) is defined in **one place**, not scattered as literals through handlers. That is the message rule in `types/backend-service.md`, and it meets rule 2 for types B, C and D.

**`02-architecture-and-code.md` partly assumes an app.**

- These parts apply to every type: layering and one-way module dependencies, data access in one layer only, single responsibility, no speculative abstraction, naming and doc-comment rules, zero warnings and a clean linter, and all of the DRY rules.
- These parts assume a screen and do **not** apply to types B, C or D: the MVVM view/view-model split, reactive state and observation, responsive layout, and "nothing blocking is callable from the UI."
- Types B and C get their equivalents (request/handler separation, async and worker practice, backpressure) from `types/backend-service.md`.

**"Native/platform-standard first"** (priority rule 8) applies to every type: use the framework's own mechanism instead of inventing one that fights it. For a backend, that means the framework's dependency injection, migration system, validation layer and task queue, not home-made substitutes.

**The checks come with the rules.** Every rule names the check that enforces it (`[check: …]`). `enforcement/adopt.py` installs the same scanner, hooks and linter configs for every type. The platform file decides which checks apply: the Python file for types B and C, an app file for type A. The "enforced by a check N of M" line in a project's `CLAUDE.md` is counted from that project's own `docs/domain-rules.md`.

**Security applies everywhere, with a different focus.** For an app, focus on storage, transport and platform permissions. For a backend, focus on authorization on every endpoint, injection and secrets. Read `03-security-owasp.md` for both, then your platform file for the checkable version.

## When a project doesn't fit

Add a new type instead of stretching an existing one. A new type file states what kind of project it covers, which general rules it narrows or replaces, and why, in the same format as the two that exist. If a rule has to be explained away every time it is applied, it is in the wrong file.

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
