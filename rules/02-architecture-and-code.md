# Architecture and code

> **Applies to:** all project types for layering, granularity, naming and DRY. The **Platform behavior** section (MVVM split, reactive state, responsive layout, UI threading) applies only to project type A, apps with a user interface. Backends and pipelines get their equivalents from `types/backend-service.md`. See `PROJECT-TYPES.md`.

The engineering standards for every project that adopts them. The checkable version for each platform is in `platform/domain-rules-*.md`. This file explains the reasoning behind those rules.

## Layering

- **Code lives in its layer:** views display, view models prepare, services hold business rules, and repositories access data. Business rules never go in views or view models. The UI never talks to storage directly. (MVVM + Service layer + Repository) [check: scan:layer-import, review]
- **Why services:** service classes provide an abstraction that makes it easy to swap implementations and to test behaviour clearly. [check: context]
- **Data is grabbed one way.** All data access goes through the repository (data) layer. Nothing else touches the database directly. [check: scan:layer-import, scan:import-matrix]
- **Module dependencies flow one way, no cycles.** Don't sneak a forbidden dependency in indirectly, for example a domain service that takes a wire-format DTO as a parameter. [check: scan:import-matrix]

## Granularity

- **Modularize everything.** Split code into small, decoupled parts with clear APIs between layers. Strong decoupling is what keeps a large codebase manageable. [check: advisory:type-size, review]
- **SRP to the class level:** prefer more, smaller classes over fewer, bigger ones; they are easier to test and more robust. Keep functions as small as possible. Automatic size warnings are advisory only; they never fail the build. [check: advisory:type-size, review]
- **No speculative abstraction (YAGNI).** Only create a protocol or interface when something real substitutes for it. Module-boundary seams always qualify. [check: review]

## Platform behavior

- **Native/platform-standard first.** Use the platform's standard mechanism for standard needs: navigation, state, modals, windowing and dependency wiring. Never invent a framework that fights the platform. "Every piece is a native control" is no defence if the pieces are assembled into a workaround for a native feature. [check: scan:native-pattern]
- **Never chase workarounds.** When something fails on a native platform and you don't know why, stop, confirm the failure is real, and ask. Don't keep trying non-native hacks. Any approved deviation is named in the plan so it is visible at approval time, never added silently. [check: scan:native-pattern, process]
- **Reactive state (Coast decision):** always use reactive programming. Done well it costs nothing, because data is only produced when something subscribes to it. It also stops a developer building something static that later has to become dynamic. Anything that can change while on screen, or that lives longer than a function call, is published through the platform's observation system. Never poll it and never refresh it manually. One-time values stay plain. [check: review]
- **Responsive layout:** use the platform's standard layout system. No fixed screen dimensions. Layout must behave correctly when the screen size changes. Exception: a design that deliberately targets a fixed canvas, and then that decision is written down, not assumed. [check: advisory:fixed-screen-size, review]
- **Never block a thread.** Long waits are asynchronous. Nothing that blocks can be called from the UI. [check: scan:blocking-call]
- **No crash on bad input.** Return typed errors and show them. Use assertions only for programmer errors. Tie background work's lifetime to its parent, so no processes are left orphaned. [check: review]

## Naming, comments, and honesty

- **No abbreviations or shortcuts in names.** Name everything clearly and concisely, so the code explains itself. A name says what a thing is, in standard industry terms, and never suggests a different role from what the code does. [check: review]
- **No inline comments** unless one is really needed to explain something non-obvious. [check: ratchet:inline-comment]
- **Doc comments required** on every public or exported type and function. Use structured function and parameter docs, not inline narration. A doc comment that reads wrong means the code has a problem, not just the wording. [check: scan:doc-comments]
- **Zero new compiler warnings + clean linter run** on every change. Use the platform's standard linter: SwiftLint, ktlint or Android lint, ESLint/Prettier with strict TypeScript, or ruff/mypy for Python. [check: tool:warnings-as-errors]

## DRY mechanics (the how of priority rule 1)

- One theme file. One string catalog per locale. One place for each cross-cutting concern. One place where each derived value is computed. One predictably named document per subject.
- **Reuse comes first:** when an existing key, token or component covers the need, use it and say that you reused it. A near-duplicate is rejected in review, with the existing item named. [check: review]
- **Creation must be justified:** a new helper, component or template states why nothing existing could be reused. [check: review]
- Reviews scan every diff for inlined strings, styling literals, home-made versions of platform features, and duplicated logic.

## Boundaries the build system enforces

- **Module boundaries are packages, not conventions.** Build the module layer so that a forbidden import is a **compile error**, not a lint finding someone can ignore. Where the language can't do this natively, use the ecosystem's enforcement tool: dependency-cruiser (JS), import-linter (Python) or ArchUnit (JVM). [check: scan:import-matrix]
- **Why this matters beyond tidiness:** modules give agents a smaller context. An agent only needs to learn the API of each module it uses, not the module's code. The boundary is what makes that small context possible. [check: context]
- **And it draws the line of responsibility.** Each module has one owner, a person or an agent. Owners are responsible only for their own module. They must not write their code around the internals of someone else's module. Responsibility boundaries are drawn on purpose. If another module's API returns the information you need, that is all you should care about, and you are done looking. If it doesn't, talk to that module's owner about the API. Never build a workaround that depends on their internals, and never reach in and change their code yourself. [check: context]
- **Enforcement is structural, not detection-only.** An agent should be unable to make a change it is not authorized to make. Limiting an agent by prompt or by convention is not enough on its own; out-of-scope changes should be technically impossible. Detection is a backup behind that barrier, never the barrier itself. [check: process]

## Granularity, with numbers

These advisory limits make "too big" measurable instead of a matter of opinion. A type raises a warning if it is over **300 lines**, or has more than **7 dependencies injected through its initializer**. The warnings feed a judgement about granularity; they never fail the build automatically. The limits are stored in config that agents cannot edit. [check: advisory:type-size]

## Prove it runs before building it out

- **The first task of a feature is a runnable spike.** Break the feature into small tasks. Make task one call something that actually runs, optionally pausing so a person can try it. This finds out early if an approach doesn't work, instead of during later reviews. [check: process]
- **Flag data and external dependencies in the plan, before writing code.** In the same plan as the code, list the non-code inputs the product needs to be usable: content datasets, third-party services, licensing and accounts. For each, give sourcing options, rough effort and a recommendation. This prevents building a whole app before anyone notices that its main feature depends on data nobody has sourced. [check: process]

## No silent rework, no silent stalls

Nothing retries, re-runs or spends money without being visible. Every automatic re-run has a budget limit, is visible while it runs, and is recorded afterwards. When any limit on attempts, authority or writes is reached, fail **loudly**, with the full log as the cause. Never stall quietly, and never loop and spend money where nobody can see it. This applies to the whole architecture, including anything added later: customers must never burn through credits because of a stuck loop. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
