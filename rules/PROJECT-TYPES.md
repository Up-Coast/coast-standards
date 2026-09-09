# Which rules apply to your project

*Last updated: 2026-09-07*

Read this before applying the rules to a project that is not an app with a
user interface. **Not every rule here makes sense everywhere**, and applying
UI rules to a headless service produces noise that trains people to ignore
rules — the opposite of what a standards repo is for.

Filed 20 August 2026, when the owner ruled that different kinds of projects
need different rules. Correcting an earlier claim in this repo that
the numbered rules were language-agnostic — they are not. They were extracted
from an app project and several of them assume a screen.

## The project types

| Type | What it is | Examples |
|---|---|---|
| **A — App with a UI** | Anything a person looks at and taps or clicks | iOS, Android, React Native, macOS, a web frontend |
| **B — Backend service** | An API, worker, or job with no screen of its own | A Python or Node API, a queue worker, a scheduled job |
| **C — Data / ML pipeline** | Ingestion, transformation, scoring, models | A scoring engine, an ETL pipeline, a training job |
| **D — Library, CLI, or internal tool** | Code other developers use | A shared package, a command-line utility, a build script |

A real project is often more than one: a product with a web frontend and a
Python API is A **and** B, and each part follows its own set. Say which part
you are working in before you invoke a rule.

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

**Priority rule 2 (all user-facing strings externalized)** is an
interface-project rule. A backend, pipeline, or CLI has little or no
user-facing text, and forcing a localization catalog on it is ceremony. The
backend equivalent — which does apply — is that any text a person will
eventually read (API error messages, emails, notifications, CLI output) has
**one home** rather than being scattered as literals through handlers. That is
`types/backend-service.md`'s message rule, and it satisfies rule 2 for types
B, C, and D.

**`02-architecture-and-code.md` is partly app-shaped.** These parts are
universal and apply to every type: layering and one-way module dependencies,
data access confined to one layer, single responsibility, no speculative
abstraction, naming and doc-comment rules, zero-warnings/clean-linter, and all
of the DRY mechanics. These parts assume a screen and do **not** apply to
types B, C, or D: the MVVM view/view-model split, reactive state and
observation, responsive layout, and "nothing blocking is callable from the
UI." Types B and C get their equivalents — request/handler separation, async
and worker discipline, backpressure — from `types/backend-service.md`.

**"Native/platform-standard first"** (priority rule 8) generalizes cleanly:
use the framework's own mechanism rather than inventing one that fights it.
For a backend that means the framework's dependency injection, its migration
system, its validation layer, its task queue — not a hand-rolled substitute.

**The checks travel with the rules.** Every rule in every file names the check that
holds it (`[check: …]`), and `enforcement/adopt.py` installs the same scanner, hooks and
linter configs whatever the type; the platform file decides which signatures apply (the
Python file for types B and C, the app file for A). The "enforced by a check N of M" line
in a project's `CLAUDE.md` is computed from that project's own `docs/domain-rules.md`.

**Security applies everywhere, but the weight shifts.** For an app, the
emphasis is storage, transport, and platform permissions. For a backend it is
authorization on every endpoint, injection, and secrets. Read
`03-security-owasp.md` for both, then the platform file for the checkable
version.

## When a project doesn't fit

Add a type rather than bending an existing one. A new type file states what
kind of project it covers, which universal rules it scopes or replaces, and
why — the same shape as the two that exist. A rule that has to be explained
away every time it is applied is a rule in the wrong file.

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
