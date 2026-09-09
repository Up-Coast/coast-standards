# The rules

*Last updated: 2026-09-08*

643 rules. You do not read them front to back — you read two files, then the one
document for your platform, and let the checks hold the rest.

- **[00-priority-rules.md](00-priority-rules.md) — read this first, always.** The
  non-negotiables in priority order. DRY is the rule above all other rules.
- **[PROJECT-TYPES.md](PROJECT-TYPES.md) — read this second.** Which rules apply to your
  kind of project: app, backend service, data/ML pipeline, library/CLI. A project with a
  frontend and an API is two types, one per part.
- **Your platform's document**, from the table below. That is the one with the checkable
  rules in it, and the one that gets copied into your project.

## Two layers, and which is which

The numbered files are the **reasoning layer**: why a rule exists, what it is trying to
prevent, and how to apply judgement where a machine cannot. They stay in this repository
and are read in place.

The platform documents are the **checkable layer**: the same standards written as
numbered rules a reviewer or a scanner can answer yes or no about. One of them is copied
into your project as `docs/domain-rules.md` when you adopt, and from then on it is yours
to edit.

So `04-localization.md` explains why an app is built localizable from day one; the twelve
rules that are actually checked (`L-1` to `L-12`) live in each platform document.

## The reasoning layer

| File | What it covers | Applies to |
|---|---|---|
| [00-priority-rules.md](00-priority-rules.md) | The non-negotiables, in priority order. **DRY is the rule above all other rules.** | every project |
| [01-working-style.md](01-working-style.md) | How agents work with the owner of a project: communication, verification, reporting, decisions | every project |
| [02-architecture-and-code.md](02-architecture-and-code.md) | Layering, single responsibility, naming, the DRY mechanics; MVVM, reactive state and responsive layout | all types; the platform-behaviour section is apps only |
| [03-security-owasp.md](03-security-owasp.md) | OWASP-derived security rules, and handling sensitive code | every project |
| [04-localization.md](04-localization.md) | Why every app is built localizable from day one, and the Canadian defaults | apps and frontends only |
| [05-design-and-ui.md](05-design-and-ui.md) | Reading design mocks, interaction rulings, copy rules, accessibility | apps and frontends only |
| [06-testing.md](06-testing.md) | Test types, TDD, false-passing patterns, what "coverage" means | every project |
| [07-documentation-git-process.md](07-documentation-git-process.md) | Docs, diagrams, decision logs, git and pull-request discipline | every project |
| [08-auditing-and-completeness.md](08-auditing-and-completeness.md) | How to audit: rebuild the list from the code, never review the list. Includes the case log of real audit misses | every project |
| [09-models-and-agents.md](09-models-and-agents.md) | Model effort defaults, verifying which model is running, commit attribution | every project |
| [10-development-environment.md](10-development-environment.md) | Atomic commands and permission prompts, disk hygiene, the cost of branch switching | every project |

### By project type

| File | For |
|---|---|
| [PROJECT-TYPES.md](PROJECT-TYPES.md) | Deciding which of the four types you have, and what each one changes |
| [types/backend-service.md](types/backend-service.md) | Services with no screen: layering without a UI, API contracts, async and workers, operability, data safety |
| [types/data-and-ml.md](types/data-and-ml.md) | Pipelines, scoring engines and models: reproducibility, data-quality gates, model versioning, drift, presenting numbers honestly |

## The checkable layer — pick one

One of these is copied into your project when you adopt. `enforced` counts the rules a
machine holds today; the rest are held by a reviewer. That number only ever goes up.

| Platform | Document | Rules | Enforced by a check |
|---|---|---|---|
| iOS | [platform/domain-rules-ios.md](platform/domain-rules-ios.md) | 74 | 24 |
| macOS | [platform/domain-rules-macos.md](platform/domain-rules-macos.md) | 81 | 25 |
| Android | [platform/domain-rules-android.md](platform/domain-rules-android.md) | 75 | 25 |
| React Native | [platform/domain-rules-react-native.md](platform/domain-rules-react-native.md) | 75 | 26 |
| Web (TypeScript) | [platform/domain-rules-web.md](platform/domain-rules-web.md) | 77 | 24 |
| Python (backend) | [platform/domain-rules-python.md](platform/domain-rules-python.md) | 47 | 15 |
| AI features — **on top of the above** | [platform/ai-features.md](platform/ai-features.md) | 41 | 0 |

[platform/ai-features.md](platform/ai-features.md) is not a platform of its own. Add it
when your product calls a model: disclosure, consent and data flow, prompt injection,
output handling, agency, cost, evaluation, logging, retrieval and supply chain.

## Finding a rule by its id

A refusal names the rule that stopped you — `[ARCH-2]`, `[L-4]`, `[DRY-1]`. The prefix
tells you where it lives.

| Prefix | What it covers | Where |
|---|---|---|
| `A` | Architecture and layering | every app platform document |
| `ACC` | Accessibility | every app platform document |
| `AUTH` | Authentication and sessions | every app platform document |
| `C` | Correctness and safe code | every app platform document |
| `DES` | Design tokens and components | every app platform document |
| `DOC` | Doc comments on public surface | every app platform document |
| `DRY` | Duplication | every app platform document |
| `ENG` | Engineering craft | every app platform document |
| `L` | Localization (`L-1` to `L-12`) | every app platform document |
| `PAY` | Payments and subscriptions | every app platform document |
| `PRIV` | Privacy and data handling | every app platform document |
| `SEC` | Security | every platform document |
| `TEST` | Testing | every platform document |
| `UGC` | User-generated content | every app platform document |
| `MAC` | macOS-specific | [platform/domain-rules-macos.md](platform/domain-rules-macos.md) |
| `API` `ARCH` `ASYNC` `DATA` `OBS` `STYLE` | Backend service rules | [platform/domain-rules-python.md](platform/domain-rules-python.md) |
| `AGENT` `AIS` `COST` `DISC` `EU` `EVAL` `FLOW` `LOG` `OUT` `PROMPT` `RAG` `REL` `STORE` `SUPPLY` | AI features | [platform/ai-features.md](platform/ai-features.md) |

If you have adopted the standards, your own copy is `docs/domain-rules.md` inside your
project — that is the one your reviews are run against, including any rule you added.

## How to read a rule

Every rule ends with a tag naming what holds it:

- `[check: scan:<name>]` — a scanner signature. Refused before the commit or the push.
- `[check: <linter>]` — your platform's linter or type checker, run by the push gate.
- `[check: advisory:<name>]` — reported, but nothing is refused.
- `[check: review]` — a reviewer answers it; no machine can.
- `[check: process]` — a working agreement rather than a property of the code.
- `[check: context]` — carried into an agent's context so it is followed while writing.

[What gets checked](../docs/what-gets-checked.md) lists the scanner signatures in plain
words. [When a check stops you](../docs/when-a-check-stops-you.md) covers what to do
about a refusal, including the sanctioned way to set one aside.

## Changing a rule

Rules are not edited in a project and pushed back. [CONTRIBUTING.md](../CONTRIBUTING.md)
has the route: every rule names a check, the verifier counts how many rules a machine
holds, and that number may not fall.

---

[Documentation](../docs/README.md) · [Quickstart](../docs/quickstart.md) ·
[How enforcement works](../enforcement/README.md) · [Repository home](../README.md)
