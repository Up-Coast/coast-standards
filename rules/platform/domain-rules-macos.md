<!-- coast-rules-version: 8 -->
# Project rules

This file ships with your project as a curated default, sourced from
established, widely used engineering and safety guides (listed under Sources
at the bottom). **It belongs to you.** Edit any rule, delete what doesn't
apply to your product, and add your own rules on top — you never have to
write a document like this from scratch. Automated reviewers check every
code change against exactly the rules in this file, so a rule you add here
is enforced on every change from then on.

How to read a rule: each one has an id (used in reviews, tickets, and
tests), a single checkable statement, and the guide it comes from in
brackets. Keep new rules checkable — a reviewer must be able to answer
"does this change break the rule — yes or no?"

## Keep it DRY (DRY) — the rule above every other rule

Every piece of knowledge has exactly one home, and everything else uses that
home.

- **DRY-1** Design components are created once and reused. Before any view,
  component or helper is created, an existing one (or a composition of existing
  ones) is checked for; a near-duplicate of an existing component is a review
  failure, and every new component states why nothing existing fit. [Coast
  standard; check: review]
- **DRY-2** Styling lives in one theme file (`Theme.swift`). Every colour, font,
  size, weight and spacing value is a token there; a second theme file is never
  created, and no styling literal is written into a feature file. [Coast
  standard; check: scan:styling-literal, ratchet:spacing-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale (`Localizable.xcstrings`).
  Additions go through that one place, and an existing key is reused before a
  near-duplicate is added. [Coast standard; check:
  scan:one-catalog-per-locale]
- **DRY-4** Error messages have one home, like strings: no error text is
  assembled at the site that throws it or shows it. [Coast standard; check:
  scan:ui-string-literal]
- **DRY-5** Cross-cutting behaviour — gestures, animations, formatting,
  validation — has one home and is called from there, never re-implemented
  locally. [Coast standard; check: tool:jscpd, review]
- **DRY-6** Every derived value — a total, a score, a status, a rounding — is
  computed in one place and reused, never recomputed slightly differently in two
  places. [Coast standard; check: tool:jscpd, review]
- **DRY-7** One name per thing, everywhere: the vocabulary is chosen once, and
  no synonym is introduced for something that already has a name. [Coast
  standard; check: review]

## Strings and localization (L)

The product is built localizable from the first commit, whether or not a second
language is scheduled; retrofitting string externalization is expensive, doing
it from day one is free.

- **L-1** No hardcoded user-facing text, anywhere. Every user-visible string —
  labels, error messages, empty states, loading text, tooltips, accessibility
  labels, titles, notification copy, units — lives in the string catalog under a
  named key, and a guard check fails the build on any bare user-facing literal
  in view code. [Coast standard; check: scan:ui-string-literal]
- **L-2** One catalog home per locale (`Localizable.xcstrings`). The strings
  surface is the sole authority: additions go through one place, and reuse comes
  first — when an existing key already carries the needed text, that key is used
  instead of a near-duplicate. [Coast standard; check:
  scan:one-catalog-per-locale]
- **L-3** Keys are semantic, not English: `vehicle.status.doNotDispatch`, not
  `do_not_dispatch_text`. The key names the meaning, so a translation can
  diverge from the English phrasing. [Coast standard; check:
  scan:english-key]
- **L-4** Sentences are never built by concatenation. Text with values in it
  uses `String(localized:)` with `\(…)` placeholders; word order differs across
  languages, and a template with placeholders is itself a catalog entry. [Up
  Coast standard; check: scan:ui-string-concat]
- **L-5** Plurals go through the platform's plural system (the string catalog's
  plural variants (CLDR one/other…)), never an `if count == 1` in code. [Up
  Coast standard; check: scan:manual-plural]
- **L-6** Dates, numbers and currency are formatted by locale-aware formatters
  (`FormatStyle` (`.formatted(.currency…)`, `Date.FormatStyle`)), never by
  string templates. [Coast standard; check: review]
- **L-7** Layouts tolerate about 30% text expansion: no fixed-width text
  container that clips, tested with a long-string locale (German),
  pseudo-localization and, when in scope, right-to-left. [Coast standard;
  check: review]
- **L-8** Localization plumbing is emitted and managed by tooling (Xcode String
  Catalogs), never hand-authored: the content is written by hand, the plumbing
  is not. [Coast standard; check: review]
- **L-9** Domain vocabulary translates with approval: safety-critical or
  client-owned terms (status tiers, legal words) get approved translations
  treated as verbatim, listed in a glossary file per project, and an agent never
  freelances them. [Coast standard; check: review]
- **L-10** Text that reaches the UI from a database or an API (descriptions,
  reference data) is part of the localization surface: either the source
  provides per-locale fields, or the UI maps stable codes to catalog keys.
  "Strings from the backend don't count" is never assumed. [Coast standard;
  check: review]
- **L-11** The language choice is user-visible, instant and persistent:
  switching locale never discards anything the user typed, and the choice
  persists (profile, local storage or URL, as the product dictates). [Coast
  standard; check: review]
- **L-12** All-caps and letter-spacing effects are applied at render time
  (`.textCase(.uppercase)` at render time), never baked into the stored string —
  casing rules differ per language, and some scripts have no case at all. [Up
  Coast standard; check: scan:baked-case]

## Design tokens and components (DES)

How the design's values and components reach the code.

- **DES-1** Every visual value is the design's exact token, used by the design's
  token name. A near-match is never inlined, and a value the design needs but
  has no token for is added to the theme as a token, not written at the use
  site. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** A brand-colour or typeface swap is a one-file edit: nothing outside
  the theme file (`Theme.swift`) knows a colour, font or spacing value. [Up
  Coast standard; check: scan:second-theme-file]
- **DES-3** A new component is justified in writing: the plan or pull request
  names the existing components that were checked and says why none fit, and the
  builder and the approver of a component are different reviews. [Coast
  standard; check: review]
- **DES-4** When the project has a design-system spec, every UI change is
  checked against it: no hardcoded value bypasses the tokens, and a pattern that
  implies a missing token adds the token rather than inlining a value. [Coast
  standard; check: review]
## Money and payments (PAY)

- **PAY-1** Money amounts are stored and calculated with decimal or
  whole-number types — never binary floating-point types (`Float`,
  `Double`), which cannot represent cents exactly. [Industry-wide practice; see
  Sources; check: advisory:money-float, review]
- **PAY-2** Every stored money amount carries its currency. Amounts in
  different currencies are never added or compared without an explicit
  conversion step. [Industry-wide practice; check: review]
- **PAY-3** Rounding is decided once (which method, at which step) and every
  total is computed in one place and reused — never recomputed slightly
  differently in two places. [Industry-wide practice; check: tool:jscpd, review]
- **PAY-4** In the Mac App Store build, digital goods and features sold
  inside the app go through Apple's in-app purchase system. The
  direct-download build may use its own payment provider, but the two
  builds never mislead the store reviewer about what the app sells.
  [Apple App Review Guidelines §3.1; check: review]
- **PAY-5** Raw card numbers never touch the app's own code or storage —
  payment collection goes through a certified payment provider's SDK or the
  platform's payment sheet. [PCI DSS scope rules; OWASP; check: review]

## Security (SEC)

- **SEC-1** All network traffic uses encrypted connections (HTTPS/TLS).
  No plaintext HTTP endpoints. [OWASP ASVS; OWASP MASVS-NETWORK; check:
  scan:plaintext-http]
- **SEC-2** Data arriving from outside the app — user input, network
  responses, deep links, shared files — is validated before use, and
  database queries are parameterized, never assembled from strings.
  [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization;
  check: scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography. Encryption, hashing, and random
  generation use the platform or standard library implementations.
  [OWASP MASVS-CRYPTO; check: review]
- **SEC-4** Secrets — API keys, tokens, credentials — never appear in
  source code, logs, analytics, or error messages. [OWASP ASVS; MASVS-STORAGE;
  check: scan:secret-literal]
- **SEC-5** Error messages shown to users never expose internals such as
  stack traces, query text, or file paths. [OWASP Cheat Sheet: Error Handling;
  check: review]

## Accounts and sign-in (AUTH)

- **AUTH-1** Sign-in uses the platform's sign-in system or an established
  identity provider — never a hand-rolled account store. If passwords must
  be stored, they are hashed with a current memory-hard algorithm
  (Argon2id, scrypt, or bcrypt), never encrypted or kept readable.
  [OWASP Cheat Sheets: Authentication, Password Storage; check: review]
- **AUTH-2** Session tokens expire, can be revoked, and are regenerated at
  sign-in and at any privilege change. [OWASP Cheat Sheet: Session Management;
  check: review]
- **AUTH-3** Sign-in attempts are rate-limited so accounts can't be
  brute-forced. [OWASP ASVS; check: review]
- **AUTH-4** Sensitive actions — deleting the account, changing email,
  password, or payment details — re-confirm the user's identity first.
  [OWASP ASVS; check: review]

## Privacy and personal data (PRIV)

- **PRIV-1** The app collects only the data the feature in front of the
  user actually needs. [Apple App Review Guidelines §5.1; GDPR data-minimization
  principle; check: review]
- **PRIV-2** Every kind of data the app collects or shares is declared in
  the store's privacy listing — no undeclared collection. [Apple App Review
  Guidelines §5.1; check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash
  reports, or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging; check:
  ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account, and the personal data behind
  it, from inside the app. [Apple App Review Guidelines §5.1.1(v); check: review]
- **PRIV-5** Personal data stored on the device lives in the app's
  protected container with the platform's data protection applied — never
  in world-readable locations. [OWASP MASVS-STORAGE; check: review]

## macOS platform behavior (MAC)

- **MAC-1** The app runs in Apple's App Sandbox in BOTH distribution
  builds. The Mac App Store requires it; keeping the direct-download build
  sandboxed too means one behavior everywhere, and any capability the
  sandbox needs (file access, network) is declared as an entitlement, never
  worked around. [Apple App Sandbox documentation; Mac App Store requirement;
  check: review]
- **MAC-2** Windows behave like Mac windows: the native title bar and
  traffic-light controls stay, state restoration works, and the app keeps
  running when its last window closes only if that matches its purpose.
  [Apple HIG — macOS Windows; check: review]
- **MAC-3** Every user-facing command lives in the menu bar in its
  standard menu, with the standard keyboard shortcuts (Cmd-W close,
  Cmd-Q quit, Cmd-, settings). A feature reachable only by pointer is
  incomplete. [Apple HIG — The menu bar; check: review]
- **MAC-4** Settings are a standard Settings scene/window, not a custom
  modal. [Apple HIG — Settings; check: review]
- **MAC-5** The app supports full keyboard navigation and standard
  text-editing behavior (undo, copy/paste, drag and drop) wherever text or
  content is edited. [Apple HIG; WCAG 2.2 — 2.1.1; check: review]
- **MAC-6** Destructive confirmations are a deliberate click — the
  destructive button never takes the Return-key default. [Project rule, from Apple
  HIG alert guidance; check: scan:destructive-default-key]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its
  background (3:1 for large text). [WCAG 2.2 — 1.4.3; check: review]
- **ACC-2** Click targets follow platform guidance and are never smaller
  than 24×24 pixels; standard controls at standard sizes satisfy this.
  [Apple HIG; WCAG 2.2 — 2.5.8; check: review]
- **ACC-3** Every interactive element has a screen-reader label that says
  what it does. [WCAG 2.2 — 4.1.2; Apple HIG Accessibility; check: review]
- **ACC-4** Text respects the system text-size setting (Dynamic Type on
  Apple platforms) without truncating away meaning. [Apple HIG; WCAG 2.2 — 1.4.4;
  check: scan:fixed-text-size]
- **ACC-5** Color is never the only signal — errors, success, and selection
  are also conveyed by text, shape, or icon. [WCAG 2.2 — 1.4.1; check: review]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** There is a way to report content, block users, and filter
  objectionable material. [Apple App Review Guidelines §1.2; check: review]
- **UGC-2** Uploaded content is checked for expected type and size before
  it is processed or stored. [OWASP Cheat Sheet: File Upload; check: review]

## Architecture (A)

- **A-1** Code lives in its layer: screens display, view models prepare
  what screens show, services hold the business rules, repositories do the
  data access. Business rules never sit in screens or view models, and the
  UI never talks to storage directly. [Industry-standard separation of concerns:
  MVVM, Service layer, Repository pattern; check: scan:layer-import, review]
- **A-2** Module dependencies flow one way, with no cycles: features
  depend on shared domain abstractions, never on each other or on concrete
  data code. [SOLID dependency-inversion principle; acyclic-dependencies
  principle; check: scan:import-matrix]
- **A-3** A type or module has one job. When a change gives it a second
  job, the change splits it instead. Automated size warnings are advisory
  signals for a reviewer, never automatic failures. [SOLID single-responsibility
  principle; check: advisory:type-size, review]
- **A-4** No speculative abstraction: a protocol or interface exists only
  where something real substitutes for it — a second implementation or a
  test fake. A boundary between two modules qualifies by definition. [YAGNI —
  industry practice; check: review]
- **A-5** Standard needs — navigation, state, dependency wiring — are met
  with the platform's standard mechanism, not an invented framework that
  fights the platform. [Apple platform conventions; check: scan:native-pattern]
- **A-6** A name says what a thing is, in the industry-standard
  vocabulary — a ViewModel prepares display state, a Repository does data
  access, a Screen is a full navigable screen — and never claims a
  different role than the code performs. [Industry-standard pattern names; Swift
  API Design Guidelines; check: review]
- **A-7** If the platform provides the feature, the feature is used. For any
  job the platform already owns — window chrome and the title bar/toolbar,
  navigation, tab bars, modals and alerts, search, sidebars/split views,
  menus, lists, progress indicators, pickers — the native mechanism is
  mandatory, and hand-assembling an equivalent out of native parts is still
  a substitution: "every piece is a native control" is not a defence.
  Examples (not the whole rule): a hand-rolled router, a custom header/title
  bar in a hidden-title-bar window, a custom tab bar where `TabView` serves,
  a hand-rolled search field instead of `.searchable`, a custom sidebar
  instead of `NavigationSplitView`, a scrim overlay used as a modal,
  hand-drawn progress or pickers, a focus or key-handling override. Any such
  workaround or substitute appears only where it was explicitly approved as
  a deliberate exception on the plan — never introduced silently or as a
  quick fix — and each UI plan item names the native feature it uses, so a
  substitution is visible at approval time. An added escape-hatch or substitution
  signature from the native-patterns checker's list fails the PR unless the plan's approved
  native-deviations list covers it. [Apple HIG; Apple platform conventions;
  check: scan:native-pattern]

## Coding (C)

- **C-1** Names follow the Swift API Design Guidelines: clear at the point
  of use, reading naturally at the call site, with no abbreviations a
  reader must decode. [Swift API Design Guidelines; check: review]
- **C-2** Model data uses value types (`struct`, `enum`) by default;
  classes are reserved for identity or lifecycle needs; shared mutable
  state is protected by the language's concurrency model (actors,
  main-actor UI state). [Swift API Design Guidelines; Apple concurrency
  documentation; check: review]
- **C-3** No force-unwraps or force-tries (`!`, `try!`) on paths that can
  fail at runtime — optionals and errors are handled. Force operations are
  reserved for invariants the code itself makes provable. [Swift language
  practice; check: swiftlint:force_unwrapping, swiftlint:force_try,
  swiftlint:force_cast]
- **C-4** A change merges with zero new compiler warnings and a clean lint
  run under the project's SwiftLint configuration. [SwiftLint standard rules;
  check: swiftlint, swiftformat, tool:warnings-as-errors]

- **C-5** No hardcoded facts about the world outside the code. A
  repository's default branch, a file path, a URL or port, a plan or
  platform tier, an external system's names or limits — every such fact
  is either asked of the system that owns it or read from its one
  configured home, through one shared function every caller uses. A
  literal assumption about external state (a branch named "main", a
  fixed path or URL) is a review failure wherever the real answer can
  be asked for. [Twelve-Factor App, config; check: scan:env-literal]

## Engineering quality (ENG)

- **ENG-1** Reactive state: any state that can change while it is
  displayed, or that outlives a single function call, is published through
  the platform's observation system (Observation/Combine on Apple
  platforms) — never polled, never manually refreshed. One-shot values stay
  plain: no observation ceremony around constants. [Platform best practice —
  Apple; check: review]
- **ENG-2** Responsive layout: screens adapt using the platform's standard
  layout system — window-size changes on desktop and web, rotation and
  size-class changes on phones and tablets. No fixed screen dimensions.
  [Platform best practice — Apple HIG Layout; check: advisory:fixed-screen-size,
  review]
- **ENG-3** Never block a thread: long waits — network calls, spawned
  processes, timers, polling — are asynchronous. No sleeping on a held
  thread, and nothing that blocks is callable from the UI. [Platform best practice
  — Apple; check: scan:blocking-call]
- **ENG-4** Child-process lifetime: any process or worker the app spawns is
  tied to its parent's lifetime — quitting the app or cancelling the task
  cleans it up. No orphaned processes. [Platform best practice; check: review]
- **ENG-5** No crash on bad input: invalid input or unexpected data
  produces a typed, surfaced error — never a process crash. Assertions that
  halt the app are reserved for programmer errors, not recoverable
  conditions. [Platform best practice; OWASP Cheat Sheet: Error Handling; check:
  review]
- **ENG-6** Secrets live in the platform's secure store — the Keychain on
  macOS — never in plaintext files, source code, or logs.
  [OWASP MASVS-STORAGE; Apple platform security; check: scan:secret-literal,
  review]
- **ENG-7** The app is signed and, for direct distribution, notarized with
  the hardened runtime enabled; nothing in the app requires disabling
  library validation or code-signing enforcement to run. (Coast's release
  stage performs the signing and notarization; this rule keeps the code
  compatible with it.) [Apple notarization + hardened runtime documentation;
  check: process]

## Tests (TEST)

- **TEST-1** Every acceptance criterion has at least one automated test,
  and each test states which acceptance criterion it verifies. [Project rule;
  check: scan:test-criterion-tag]
- **TEST-2** Tests that gate a merge run without live external services —
  external dependencies are faked locally. Tests against live services run
  separately and never block a merge. [Project rule; Google Testing Blog: hermetic
  testing; check: scan:hermetic-test]
- **TEST-3** A test proves behavior: it fails when the behavior it names is
  broken. Assertions so weak that any implementation passes don't count as
  coverage. [Project rule; check: review]
- **TEST-4** Test data looks like real data. Fixtures are the size, shape
  and messiness of the real thing: lists long enough to overflow a
  container, names long enough to truncate, documents written in the
  industry's words rather than the product's, and stand-ins for outside
  services that can express that service's real refusals (403, 404, empty,
  unreachable, slow) — not merely success and one tidy error. A fixture
  built to be convenient tests the fixture. [Project rule; check: review]
- **TEST-5** Pressure-test on purpose, as its own discipline: deliberately
  push past what is expected — many more items than anyone would have,
  values at and beyond the declared limits, empty and enormous, slow and
  absent. At least the surfaces that render project data carry one case
  each. [Project rule; check: review]

## Documentation (DOC)

- **DOC-1** Every public type and function carries a doc comment saying
  what it does — including parameters and return value where they aren't
  obvious. The generated API reference is built from these. [Project rule; check:
  scan:doc-comments]
- **DOC-2** A doc comment must match what the code actually does. A doc
  that reads wrong is treated as a code problem, not a wording problem.
  [Project rule; check: review]

---

## Sources

- **Coast Standards** — the DRY, strings and design-token rules (DRY, L, DES) are
  this repository's own standing rules, applied to every project that adopts it.
The rules above are written in this project's own words; the guides they
are sourced from (for provenance and further reading):

- **OWASP Application Security Verification Standard (ASVS) 5.0** —
  <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Mobile Application Security Verification Standard (MASVS) 2.1** —
  <https://mas.owasp.org/MASVS/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** — <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **W3C Web Content Accessibility Guidelines (WCAG) 2.2** —
  <https://www.w3.org/TR/WCAG22/> (W3C document license; also ISO/IEC 40500)
- **Apple App Sandbox / notarization / hardened runtime documentation** —
  <https://developer.apple.com/documentation/security/> (proprietary — referenced only)
- **Apple App Review Guidelines** —
  <https://developer.apple.com/app-store/review/guidelines/> (proprietary — referenced only, no text reproduced)
- **Apple Human Interface Guidelines** —
  <https://developer.apple.com/design/human-interface-guidelines/> (proprietary — referenced only)
- **Swift API Design Guidelines** —
  <https://www.swift.org/documentation/api-design-guidelines/> (Swift.org — referenced only, no text reproduced)
- **SwiftLint** (standard rule set, used as the deterministic checker some
  rules name) — <https://github.com/realm/SwiftLint> (MIT)

No text from these guides is reproduced here — every rule is an original
plain-language statement citing its source — so editing or replacing this
file carries no license obligations for you.
