# Architecture and code

> **Applies to:** all project types for layering, granularity, naming, and DRY; the
> **Platform behavior** section (MVVM split, reactive state, responsive layout, UI
> threading) is for project type A — apps with a user interface — only. Backends and
> pipelines get their equivalents from `types/backend-service.md`. See `PROJECT-TYPES.md`.

The engineering standards Coast enforces on every project it builds, generalized for any
Up Coast project. Per-platform checkable versions live in `platform/domain-rules-*.md`;
this file is the reasoning layer behind them.

## Layering

- **Code lives in its layer:** screens/views display, view models prepare, services hold
  business rules, repositories do data access. Business rules never in screens or view
  models; UI never talks to storage directly. (MVVM + Service layer + Repository)
- **Why services:** "service classes... allow the abstraction which allows for swapping
  things out and testing functionality clearly." (Abbey)
- **Data is grabbed one way.** All data access goes through the repository/data layer —
  nothing else touches the database directly.
- **Module dependencies flow one way, no cycles.** No transitively smuggled forbidden
  imports (e.g. a domain service taking a wire-format DTO parameter).

## Granularity

- **Modularize everything.** "Break things into tiny, tiny decoupled parts — heavy
  decoupling is what makes the volume manageable." Clear APIs between layers.
- **SRP to the class level:** favour more, smaller classes over fewer, bigger ones — better
  for testing and robustness. Functions as small as possible. Automated size warnings are
  advisory signals, never automatic failures.
- **No speculative abstraction (YAGNI).** A protocol/interface exists only where something
  real substitutes for it (module-boundary seams qualify by definition).

## Platform behavior

- **Native/platform-standard first.** Standard needs (navigation, state, modals, windowing,
  dependency wiring) are met with the platform's standard mechanism, never an invented
  framework that fights the platform. "Every piece is a native control" is not a defence
  when the pieces are assembled into a workaround for a native feature.
- **Never chase workarounds.** An unexplained failure on a native platform is a reason to
  pause, confirm the failure is real, and ask — not to iterate on non-native hacks. Any
  approved deviation is named on the plan so it's visible at approval time, never introduced
  silently.
- **Reactive state (Coast D113, Abbey verbatim):** "they always use reactive programming.
  There is no cost to this if it is done properly because the data is only outputted if
  there are subscribers to it anyway… I would hate for an inexperienced user to spend weeks
  building something which in the end was static and needed to be dynamic." Anything that
  can change while displayed, or outlives a function call, is published through the
  platform's observation system — never polled, never manually refreshed. One-shot values
  stay plain.
- **Responsive layout:** platform-standard layout system, no fixed screen dimensions,
  correct behavior on screen-size changes. (Exception: a design that deliberately targets a
  fixed canvas — but then that decision is filed, not assumed.)
- **Never block a thread.** Long waits are asynchronous; nothing blocking is callable from
  the UI.
- **No crash on bad input.** Typed, surfaced errors; assertions reserved for programmer
  errors. Background work's lifetime is tied to its parent — no orphaned processes.

## Naming, comments, and honesty

- **No abbreviations or shortcuts in names.** Clear, concise naming of everything; code
  should be self-explanatory. A name says what a thing is, in industry-standard vocabulary,
  and never claims a different role than the code performs.
- **No inline comments** unless genuinely required to explain something non-obvious.
- **Doc comments required** on every public/exported type and function (structured
  function/parameter docs, not inline narration). A doc that reads wrong is a code problem,
  not a wording problem.
- **Zero new compiler warnings + clean linter run** on every change. Use the platform's
  standard linter (SwiftLint, ktlint/Android lint, ESLint/Prettier + strict TypeScript,
  ruff/mypy for Python).

## DRY mechanics (the how of priority rule 1)

- One theme file; one string catalog per locale; one home per cross-cutting concern; one
  computation site per derived value; one predictably-named document per subject.
- **Reuse comes first:** when an existing key/token/component covers the need, use it and
  name the reuse; a near-duplicate is a review rejection with the existing item named.
- **Creation must be justified:** a new helper/component/template states why nothing
  existing was reused.
- Reviews mechanically scan diffs for inlined strings, styling literals, hand-rolled
  versions of platform features, and duplicated logic.

## Boundaries the build system enforces

- **Module boundaries are packages, not conventions.** Realize the module layer so a
  forbidden import is a **compile error**, not a lint finding someone can ignore. (Abbey:
  *"I think modules should be enforced as packages."*) Where the language can't do it
  natively, use the ecosystem's enforcement tool — dependency-cruiser (JS), import-linter
  (Python), ArchUnit (JVM).
- **Why this matters beyond tidiness**, in Abbey's words: modularization exists *"so that
  the AIs could have better context (they just need to learn the APIs of each module they
  need to interact with rather than learn the code for example)."* The boundary is what
  makes a small working context possible.
- **Enforcement is structural, not detection-only.** *"It should be impossible for agents to
  make changes they are not authorized to do."* Scoping by prompt or by convention is not
  sufficient on its own; out-of-authority changes should be technically impossible. Detection
  sits behind the wall, never as the wall.

## Granularity, with numbers

The advisory thresholds, so "too big" is checkable rather than argued: a type over **300
lines**, or with more than **7 initializer-injected dependencies**, raises a warning. These
are inputs to a judgment about granularity — warnings, never automatic failures — and the
constants live in config the agent can't reach.

## Prove it runs before building it out

- **The first task of a feature is a runnable spike.** Decompose into small tasks and make
  task one invoke something that actually runs, with an optional pause for a human to try
  it. This front-loads the "this approach doesn't work" discovery so review cycles aren't
  spent finding it later.
- **Flag data and external dependencies in the plan, before writing code.** List the
  non-code inputs the product needs to be genuinely usable — content datasets, third-party
  services, licensing, accounts — with sourcing options, rough effort, and a recommendation,
  in the same plan as the code. (Origin: an entire app was built before anyone flagged that
  its headline feature depended on a food database nobody had sourced. Abbey: *"you should
  have flagged this before even starting."*)

## No silent rework, no silent stalls

Nothing retries, re-runs, or spends invisibly. Every automatic re-run is budget-bounded,
visible while it happens, and recorded afterwards. Hitting any attempt, authority, or write
limit fails **loudly**, with the full log as the cause — never a quiet stall, and never a
loop that burns money where nobody can see it. Abbey filed this as a rule for the whole
architecture, binding on anything added later: *"We don't want to risk customers burning
through credits due to a stuck loop."*
