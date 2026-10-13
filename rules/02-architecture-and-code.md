# Architecture and code

Read this when a task adds or moves code, modules or names. Platform behavior applies to type A only; backends use `types/backend-service.md`.

## Layering

- **Code lives in its layer:** views display, view models prepare, services hold business rules, repositories access data. The UI never touches storage. [check: scan:layer-import, review]
- **Why services:** swappable, testable implementations. [check: context]
- **Data is grabbed one way.** Only repositories touch the database. [check: scan:layer-import, scan:import-matrix]
- **Module dependencies flow one way, no cycles.** No indirect ones, such as a domain service taking a wire DTO. [check: scan:import-matrix]

## Granularity

- **Modularize everything.** Small, decoupled parts with clear APIs. [check: advisory:type-size, review]
- **SRP to the class level:** many small classes and functions. Size warnings never fail the build. [check: advisory:type-size, review]
- **No speculative abstraction (YAGNI).** An interface needs a real substitute or a module seam. [check: review]

## Platform behavior

- **Native/platform-standard first.** Use the platform for navigation, state, modals, windowing and wiring. Route through one shared router (DRY-5). Never assemble native controls into a workaround. [check: scan:native-pattern]
- **Never chase workarounds.** On an unexplained failure, confirm it and ask. Name approved deviations in the plan. [check: scan:native-pattern, process]
- **Reactive state (Coast decision):** publish anything that changes on screen or outlives a call through the observation system; never poll or refresh manually. [check: review]
- **Responsive layout:** platform layout, no fixed screen sizes, unless a fixed canvas is written down. [check: advisory:fixed-screen-size, review]
- **Never block a thread.** Nothing blocking runs from the UI. [check: scan:blocking-call]
- **No crash on bad input.** Show typed errors; assert only programmer errors. Tie background work to its parent. [check: review]

## Naming, comments, and honesty

- **No abbreviations or shortcuts in names.** Use standard terms that match the code's role. [check: review]
- **No inline comments** unless explaining something non-obvious. [check: ratchet:inline-comment]
- **Doc comments required** on every public type and function, with structured parameter docs. [check: scan:doc-comments]
- **Zero new compiler warnings + clean linter run** on every change: SwiftLint, ktlint/Android lint, ESLint/Prettier with strict TypeScript, ruff/mypy. [check: tool:warnings-as-errors]

## DRY mechanics (the how of priority rule 1)

- **Reuse comes first:** use an existing key, token or component and say so. Review rejects near-duplicates. [check: review]
- **Creation must be justified:** state why nothing existing fits. [check: review]

## Boundaries the build system enforces

- **Module boundaries are packages, not conventions.** A forbidden import fails compilation, or dependency-cruiser, import-linter or ArchUnit. [check: scan:import-matrix]
- **Why this matters beyond tidiness:** agents learn module APIs, not code. [check: context]
- **And it draws the line of responsibility.** Each module has one owner. Use its API, never its internals or code; ask its owner for changes. [check: context]
- **Enforcement is structural, not detection-only.** Make unauthorized changes impossible; detection is a backup. [check: process]

## Granularity, with numbers

A type warns above **300 lines** or **7 initializer-injected dependencies**. Advisory only; limits live in config agents cannot edit. [check: advisory:type-size]

## Prove it runs before building it out

- **The first task of a feature is a runnable spike.** [check: process]
- **Flag data and external dependencies in the plan, before writing code.** List datasets, services, licences and accounts with sourcing options, effort and a recommendation. [check: process]

## No silent rework, no silent stalls

Every automatic re-run has a budget, is visible and is recorded. At any attempt, authority or write limit, fail loudly with the full log. Never stall or loop spending money unseen. [check: process]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
