# Architecture and code

> **Applies to:** all project types for layering, granularity, naming, and DRY; the
> **Platform behavior** section (MVVM split, reactive state, responsive layout, UI
> threading) is for project type A — apps with a user interface — only. Backends and
> pipelines get their equivalents from `types/backend-service.md`. See `PROJECT-TYPES.md`.

The engineering standards Coast enforces on every project it builds, generalized for any
project that adopts them. Per-platform checkable versions live in `platform/domain-rules-*.md`;
this file is the reasoning layer behind them.

## Layering

- **Code lives in its layer:** screens/views display, view models prepare, services hold
  business rules, repositories do data access. Business rules never in screens or view
  models; UI never talks to storage directly. (MVVM + Service layer + Repository)
  [check: scan:layer-import, review]
- **Why services:** service classes give the abstraction that allows swapping things out
  and testing functionality clearly. [check: context]
- **Data is grabbed one way.** All data access goes through the repository/data layer —
  nothing else touches the database directly.
  [check: scan:layer-import, scan:import-matrix]
- **Module dependencies flow one way, no cycles.** No transitively smuggled forbidden
  imports (e.g. a domain service taking a wire-format DTO parameter).
  [check: scan:import-matrix]

## Granularity

- **Modularize everything.** Break things into tiny decoupled parts — heavy decoupling is
  what makes the volume manageable. Clear APIs between layers.
  [check: advisory:type-size, review]
- **SRP to the class level:** favour more, smaller classes over fewer, bigger ones — better
  for testing and robustness. Functions as small as possible. Automated size warnings are
  advisory signals, never automatic failures.
  [check: advisory:type-size, review]
- **No speculative abstraction (YAGNI).** A protocol/interface exists only where something
  real substitutes for it (module-boundary seams qualify by definition).
  [check: review]

## Platform behavior

- **Native/platform-standard first.** Standard needs (navigation, state, modals, windowing,
  dependency wiring) are met with the platform's standard mechanism, never an invented
  framework that fights the platform. "Every piece is a native control" is not a defence
  when the pieces are assembled into a workaround for a native feature.
  [check: scan:native-pattern]
- **Never chase workarounds.** An unexplained failure on a native platform is a reason to
  pause, confirm the failure is real, and ask — not to iterate on non-native hacks. Any
  approved deviation is named on the plan so it's visible at approval time, never introduced
  silently. [check: scan:native-pattern, process]
- **Reactive state (Coast decision):** always use reactive programming. Done properly it
  costs nothing, because data is only output when something subscribes to it — and it
  saves an inexperienced developer from spending weeks building something static that in
  the end needed to be dynamic. Anything that
  can change while displayed, or outlives a function call, is published through the
  platform's observation system — never polled, never manually refreshed. One-shot values
  stay plain. [check: review]
- **Responsive layout:** platform-standard layout system, no fixed screen dimensions,
  correct behavior on screen-size changes. (Exception: a design that deliberately targets a
  fixed canvas — but then that decision is filed, not assumed.)
  [check: advisory:fixed-screen-size, review]
- **Never block a thread.** Long waits are asynchronous; nothing blocking is callable from
  the UI. [check: scan:blocking-call]
- **No crash on bad input.** Typed, surfaced errors; assertions reserved for programmer
  errors. Background work's lifetime is tied to its parent — no orphaned processes.
  [check: review]

## Naming, comments, and honesty

- **No abbreviations or shortcuts in names.** Clear, concise naming of everything; code
  should be self-explanatory. A name says what a thing is, in industry-standard vocabulary,
  and never claims a different role than the code performs. [check: review]
- **No inline comments** unless genuinely required to explain something non-obvious.
  [check: ratchet:inline-comment]
- **Doc comments required** on every public/exported type and function (structured
  function/parameter docs, not inline narration). A doc that reads wrong is a code problem,
  not a wording problem. [check: scan:doc-comments]
- **Zero new compiler warnings + clean linter run** on every change. Use the platform's
  standard linter (SwiftLint, ktlint/Android lint, ESLint/Prettier + strict TypeScript,
  ruff/mypy for Python). [check: tool:warnings-as-errors]

## DRY mechanics (the how of priority rule 1)

- One theme file; one string catalog per locale; one home per cross-cutting concern; one
  computation site per derived value; one predictably-named document per subject.
- **Reuse comes first:** when an existing key/token/component covers the need, use it and
  name the reuse; a near-duplicate is a review rejection with the existing item named.
  [check: review]
- **Creation must be justified:** a new helper/component/template states why nothing
  existing was reused. [check: review]
- Reviews mechanically scan diffs for inlined strings, styling literals, hand-rolled
  versions of platform features, and duplicated logic.

## Boundaries the build system enforces

- **Module boundaries are packages, not conventions.** Realize the module layer so a
  forbidden import is a **compile error**, not a lint finding someone can ignore. Where
  the language can't do it
  natively, use the ecosystem's enforcement tool — dependency-cruiser (JS), import-linter
  (Python), ArchUnit (JVM). [check: scan:import-matrix]
- **Why this matters beyond tidiness:** modularization exists so that agents have better
  context — they need to learn only the API of each module they interact with, not its
  code. The boundary is what makes a small working context possible. [check: context]
- **And it draws the line of responsibility.** Each module has someone — a person or an
  agent — responsible for it. They are not responsible for anyone else's module and must
  not write their code to accommodate the internals of one. Agents are responsible for
  their own area of the code; they do not build their code to make it work with code
  another agent is responsible for. The boundaries of responsibility are drawn
  deliberately, and as long as the other API returns the information the agent needs, that
  is the only thing the agent should care about. Practically: if the API gives you what you
  need, you are done looking. If it doesn't, that is a conversation with its owner about
  the API — never a workaround built on knowledge of their internals, and never a fix you
  reach in and make yourself. [check: context]
- **Enforcement is structural, not detection-only.** It should be impossible for an agent
  to make a change it is not authorized to make. Scoping by prompt or by convention is not
  sufficient on its own; out-of-authority changes should be technically impossible. Detection
  sits behind the wall, never as the wall. [check: process]

## Granularity, with numbers

The advisory thresholds, so "too big" is checkable rather than argued: a type over **300
lines**, or with more than **7 initializer-injected dependencies**, raises a warning. These
are inputs to a judgment about granularity — warnings, never automatic failures — and the
constants live in config the agent can't reach. [check: advisory:type-size]

## Prove it runs before building it out

- **The first task of a feature is a runnable spike.** Decompose into small tasks and make
  task one invoke something that actually runs, with an optional pause for a human to try
  it. This front-loads the "this approach doesn't work" discovery so review cycles aren't
  spent finding it later. [check: process]
- **Flag data and external dependencies in the plan, before writing code.** List the
  non-code inputs the product needs to be genuinely usable — content datasets, third-party
  services, licensing, accounts — with sourcing options, rough effort, and a recommendation,
  in the same plan as the code. (Origin: an entire app was built before anyone flagged that
  its headline feature depended on a food database nobody had sourced. It should have been
  flagged before starting.) [check: process]

## No silent rework, no silent stalls

Nothing retries, re-runs, or spends invisibly. Every automatic re-run is budget-bounded,
visible while it happens, and recorded afterwards. Hitting any attempt, authority, or write
limit fails **loudly**, with the full log as the cause — never a quiet stall, and never a
loop that burns money where nobody can see it. The owner filed this as a rule for the
whole architecture, binding on anything added later: customers must never burn through
credits because of a stuck loop. [check: process]
