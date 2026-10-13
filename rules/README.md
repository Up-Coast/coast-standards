# The rules

An agent holds two files on every task and reads the others only when its task touches their area.

1. **[00-priority-rules.md](00-priority-rules.md)**: the non-negotiables, in priority order. Always loaded.
2. **Your platform's document**, from [the table below](#the-checkable-layer-pick-one): the checkable rules, copied into your project as `docs/domain-rules.md`. Always loaded.
3. **[PROJECT-TYPES.md](PROJECT-TYPES.md)**: which rules apply to your kind of project. Read it when setting a project up.

## Always loaded, and reference

| Set | Files | What it is |
|---|---|---|
| Always loaded | `00-priority-rules.md` and the platform document | Short rules an agent holds on every task. Each rule is one checkable sentence and its check tag. |
| Reference | `01`–`10`, `PROJECT-TYPES.md`, `types/` | Rules for one area. Each file opens with the line "Read this when …", and stays in this repository. |

For example, `04-localization.md` holds the locale defaults; the twelve checked localization rules (`L-1` to `L-12`) are in each platform document.

## Reference files

| File | What it covers | Applies to |
|---|---|---|
| [00-priority-rules.md](00-priority-rules.md) | The non-negotiables, in priority order. **DRY is the rule above all other rules.** | every project |
| [01-working-style.md](01-working-style.md) | How agents work with a project's owner: communication, verification, reporting, decisions | every project |
| [02-architecture-and-code.md](02-architecture-and-code.md) | Layering, single responsibility, naming, DRY, reactive state and responsive layout | all types; the platform-behaviour section is apps only |
| [03-security-owasp.md](03-security-owasp.md) | OWASP-based security rules, and handling sensitive code | every project |
| [04-localization.md](04-localization.md) | Locale defaults and language requirements | apps and frontends only |
| [05-design-and-ui.md](05-design-and-ui.md) | Reading design mocks, interaction rules, copy rules, accessibility | apps and frontends only |
| [06-testing.md](06-testing.md) | Test types, TDD, tests that pass when they shouldn't, what "coverage" means | every project |
| [07-documentation-git-process.md](07-documentation-git-process.md) | Docs, diagrams, decision logs, git and pull-request practice | every project |
| [08-auditing-and-completeness.md](08-auditing-and-completeness.md) | How to audit: rebuild the list from the code, never review the list | every project |
| [09-models-and-agents.md](09-models-and-agents.md) | Default model effort, checking which model is running | every project |
| [10-development-environment.md](10-development-environment.md) | Single commands and permission prompts, disk space, the cost of switching branches | every project |

### By project type

| File | For |
|---|---|
| [PROJECT-TYPES.md](PROJECT-TYPES.md) | Working out which of the four types you have, and what each one changes |
| [types/backend-service.md](types/backend-service.md) | Services with no screen: layering without a UI, API contracts, async work and workers, operations, data safety |
| [types/data-and-ml.md](types/data-and-ml.md) | Pipelines, scoring engines and models: reproducibility, data-quality checks, model versioning, drift, presenting numbers honestly |

## The checkable layer: pick one

Copy one of these into your project when you adopt. "Enforced by a check" counts the rules a machine enforces today; a reviewer holds the rest. That number may only go up.

| Platform | Document | Rules | Enforced by a check |
|---|---|---|---|
| iOS | [platform/domain-rules-ios.md](platform/domain-rules-ios.md) | 76 | 24 |
| macOS | [platform/domain-rules-macos.md](platform/domain-rules-macos.md) | 83 | 25 |
| Android | [platform/domain-rules-android.md](platform/domain-rules-android.md) | 77 | 25 |
| React Native | [platform/domain-rules-react-native.md](platform/domain-rules-react-native.md) | 77 | 26 |
| Web (TypeScript) | [platform/domain-rules-web.md](platform/domain-rules-web.md) | 79 | 24 |
| Python (backend) | [platform/domain-rules-python.md](platform/domain-rules-python.md) | 49 | 15 |
| AI features — **on top of the above** | [platform/ai-features.md](platform/ai-features.md) | 41 | 0 |

[platform/ai-features.md](platform/ai-features.md) is not a platform on its own. Add it if your product calls an AI model. It covers disclosure, consent and data flow, prompt injection, output handling, agent permissions, cost, evaluation, logging, retrieval and supply chain.

### Sections shared by several platforms

A section that is the same on more than one platform is written once, in [`platform/shared/`](https://github.com/Up-Coast/coast-standards/tree/main/rules/platform/shared). Each platform file marks where it goes with a `<!-- shared-section: … -->` comment, so every platform file is still complete on its own. To change a shared section:

1. Edit its file in `rules/platform/shared/`.
2. Run `python3 tools/build_rules.py` to update the platform files. It also marks each changed file `unreleased`, so the next release stamps it.
3. Commit both. A test refuses a platform file that does not match its shared section, and a section copied by hand into two platform files.

## Finding a rule by its id

When a check refuses a change, it names the rule, for example `[ARCH-2]`, `[L-4]` or `[DRY-1]`. The prefix tells you where to find it.

| Prefix | What it covers | Where |
|---|---|---|
| `A` | Architecture and layering | every app platform document |
| `ACC` | Accessibility | every app platform document |
| `AUTH` | Authentication and sessions | every app platform document |
| `C` | Correctness and safe code | every app platform document |
| `DES` | Design tokens and components | every app platform document |
| `DOC` | Doc comments on public code | every app platform document |
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

After you adopt, your own copy is `docs/domain-rules.md` in your project. Reviews run against that copy, including any rules you added.

## How to read a rule

Every rule ends with a tag that says what enforces it:

| Tag | Enforced by |
|---|---|
| `[check: scan:<name>]` | A scanner check. The commit or push is refused. |
| `[check: <linter>]` | Your platform's linter or type checker, run by the pre-push hook. |
| `[check: advisory:<name>]` | Reported only; nothing is refused. |
| `[check: review]` | A reviewer; no machine can check it. |
| `[check: process]` | A working agreement, not a property of the code. |
| `[check: context]` | Given to the agent as context, so it follows the rule while writing. |

- [What gets checked](../docs/what-gets-checked.md) lists the scanner checks in plain words.
- [When a check stops you](../docs/when-a-check-stops-you.md) explains what to do when a check refuses a change, including the approved way to set a check aside.

## Sources

The DRY, L and DES rules are Coast Standards rules. Every other rule is an original plain-language statement drawn from these guides; no text from them is reproduced.

- [OWASP Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard/), [Mobile Application Security Verification Standard (MASVS)](https://mas.owasp.org/MASVS/), [Cheat Sheet Series](https://cheatsheetseries.owasp.org/) and [Top 10](https://owasp.org/www-project-top-ten/) (CC BY-SA 4.0)
- [W3C Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/)
- [PCI Security Standards (PCI DSS)](https://www.pcisecuritystandards.org/)
- [The Twelve-Factor App](https://12factor.net/)
- Apple: [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/), [security documentation](https://developer.apple.com/documentation/security/), [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/), [SwiftLint](https://github.com/realm/SwiftLint)
- Android: [Google Play Developer Program policies](https://play.google/developer-content-policy/), [app security best practices](https://developer.android.com/privacy-and-security/security-tips), [app architecture guidance](https://developer.android.com/topic/architecture), [Material Design accessibility](https://m3.material.io/foundations/accessible-design/overview), [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html), [ktlint](https://github.com/pinterest/ktlint), [detekt](https://github.com/detekt/detekt)
- JavaScript: [React](https://react.dev/), [React Native security](https://reactnative.dev/docs/security), [TypeScript](https://www.typescriptlang.org/docs/), [ESLint](https://eslint.org/), [typescript-eslint](https://typescript-eslint.io/), [Prettier](https://prettier.io/)
- Python: [PEPs 8, 257 and 484](https://peps.python.org/), [PyPA packaging guidance](https://packaging.python.org/), [Python documentation](https://docs.python.org/3/)
- AI features: see the Sources section of [platform/ai-features.md](platform/ai-features.md)

## Changing a rule

Don't edit a rule in your project and push it back here. Follow [CONTRIBUTING.md](../CONTRIBUTING.md). Every rule names a check, the verifier counts how many rules a machine enforces, and that count may not go down.

---

[Documentation](../docs/README.md) · [Quickstart](../docs/quickstart.md) · [How enforcement works](../enforcement/README.md) · [Repository home](../README.md)
