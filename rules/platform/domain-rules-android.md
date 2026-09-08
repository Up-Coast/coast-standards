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
- **DRY-2** Styling lives in one theme file (`Theme.kt` (the Material theme and
  its tokens)). Every colour, font, size, weight and spacing value is a token
  there; a second theme file is never created, and no styling literal is written
  into a feature file. [Coast standard; check: scan:styling-literal,
  scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale
  (`res/values-<locale>/strings.xml`). Additions go through that one place, and
  an existing key is reused before a near-duplicate is added. [Coast
  standard; check: scan:one-catalog-per-locale]
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
- **L-2** One catalog home per locale (`res/values-<locale>/strings.xml`). The
  strings surface is the sole authority: additions go through one place, and
  reuse comes first — when an existing key already carries the needed text, that
  key is used instead of a near-duplicate. [Coast standard; check:
  scan:one-catalog-per-locale]
- **L-3** Keys are semantic, not English: `vehicle.status.doNotDispatch`, not
  `do_not_dispatch_text`. The key names the meaning, so a translation can
  diverge from the English phrasing. [Coast standard; check:
  scan:english-key]
- **L-4** Sentences are never built by concatenation. Text with values in it
  uses `getString(R.string.key, …)` with format arguments; word order differs
  across languages, and a template with placeholders is itself a catalog entry.
  [Coast standard; check: scan:ui-string-concat]
- **L-5** Plurals go through the platform's plural system (`<plurals>` resources
  (CLDR quantities)), never an `if count == 1` in code. [Coast standard;
  check: scan:manual-plural]
- **L-6** Dates, numbers and currency are formatted by locale-aware formatters
  (`NumberFormat` / `DateTimeFormatter` with the user's locale), never by string
  templates. [Coast standard; check: review]
- **L-7** Layouts tolerate about 30% text expansion: no fixed-width text
  container that clips, tested with a long-string locale (German),
  pseudo-localization and, when in scope, right-to-left. [Coast standard;
  check: review]
- **L-8** Localization plumbing is emitted and managed by tooling (Android
  resources), never hand-authored: the content is written by hand, the plumbing
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
- **L-12** All-caps and letter-spacing effects are applied at render time (a
  `TextStyle` or `textAllCaps` at render time), never baked into the stored
  string — casing rules differ per language, and some scripts have no case at
  all. [Coast standard; check: scan:baked-case]

## Design tokens and components (DES)

How the design's values and components reach the code.

- **DES-1** Every visual value is the design's exact token, used by the design's
  token name. A near-match is never inlined, and a value the design needs but
  has no token for is added to the theme as a token, not written at the use
  site. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** A brand-colour or typeface swap is a one-file edit: nothing outside
  the theme file (`Theme.kt` (the Material theme and its tokens)) knows a
  colour, font or spacing value. [Coast standard; check:
  scan:second-theme-file]
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
- **PAY-4** Digital goods and features sold inside the app go through
  Google Play's billing system. [Google Play Payments policy; check: review]
- **PAY-5** Raw card numbers never touch the app's own code or storage —
  payment collection goes through a certified payment provider's SDK or the
  platform's payment sheet. [PCI DSS scope rules; OWASP; check: review]

## Security (SEC)

- **SEC-1** All network traffic uses encrypted connections (HTTPS/TLS), and
  cleartext traffic is disabled in the app's network security
  configuration. [OWASP MASVS-NETWORK; Android security best practices; check:
  scan:plaintext-http]
- **SEC-2** Data arriving from outside the app — user input, network
  responses, deep links, shared files, intents — is validated before use,
  and database queries are parameterized, never assembled from strings.
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
- **SEC-6** App components (activities, services, receivers, providers) are
  not exported unless another app genuinely needs to reach them, and every
  exported component validates what it receives. [Android security best practices;
  OWASP MASVS-PLATFORM; check: scan:exported-component]

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
  user actually needs. [Google Play User Data policy; GDPR data-minimization
  principle; check: review]
- **PRIV-2** Every kind of data the app collects or shares is declared in
  the Play Console's Data safety section — no undeclared collection.
  [Google Play Data safety requirements; check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash
  reports, or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging; check:
  ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account, and the personal data behind
  it, from inside the app (with the web deletion path Play policy also
  requires). [Google Play Account deletion policy; check: review]
- **PRIV-5** Personal data stored on the device lives in the app's internal
  storage, encrypted with Keystore-backed keys where it is sensitive —
  never in world-readable locations or external storage. [OWASP MASVS-STORAGE;
  check: review]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its
  background (3:1 for large text). [WCAG 2.2 — 1.4.3; Material Design
  accessibility; check: review]
- **ACC-2** Touch targets are at least 48×48dp per platform guidance, and
  never smaller than 24×24 pixels. [Material Design accessibility; WCAG 2.2 —
  2.5.8; check: review]
- **ACC-3** Every interactive element has a content description so screen
  readers (TalkBack) can say what it does. [WCAG 2.2 — 4.1.2; Material Design
  accessibility; check: review]
- **ACC-4** Text respects the system font-size setting (scalable sp units)
  without truncating away meaning. [Material Design accessibility; WCAG 2.2 —
  1.4.4; check: scan:fixed-text-size]
- **ACC-5** Color is never the only signal — errors, success, and selection
  are also conveyed by text, shape, or icon. [WCAG 2.2 — 1.4.1; check: review]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** There is a way to report content, block users, and filter
  objectionable material. [Google Play User Generated Content policy; check:
  review]
- **UGC-2** Uploaded content is checked for expected type and size before
  it is processed or stored. [OWASP Cheat Sheet: File Upload; check: review]

## Architecture (A)

- **A-1** Code lives in its layer: screens display, view models prepare
  what screens show, services hold the business rules, repositories do the
  data access. Business rules never sit in screens or view models, and the
  UI never talks to storage directly. [Industry-standard separation of concerns:
  MVVM, Service layer, Repository pattern; Android app architecture guidance;
  check: scan:layer-import, review]
- **A-2** Module dependencies flow one way, with no cycles: features
  depend on shared domain abstractions, never on each other or on concrete
  data code. [SOLID dependency-inversion principle; acyclic-dependencies
  principle; check: scan:import-matrix]
- **A-3** A type or module has one job. When a change gives it a second
  job, the change splits it instead. Automated size warnings are advisory
  signals for a reviewer, never automatic failures. [SOLID single-responsibility
  principle; check: advisory:type-size, review]
- **A-4** No speculative abstraction: an interface exists only where
  something real substitutes for it — a second implementation or a test
  fake. A boundary between two modules qualifies by definition. [YAGNI — industry
  practice; check: review]
- **A-5** Standard needs — navigation, state, dependency wiring — are met
  with the platform's standard mechanism, not an invented framework that
  fights the platform. [Android app architecture guidance; check:
  scan:native-pattern]
- **A-6** A name says what a thing is, in the industry-standard
  vocabulary — a ViewModel prepares display state, a Repository does data
  access, a Screen is a full navigable screen — and never claims a
  different role than the code performs. [Industry-standard pattern names; Kotlin
  coding conventions; check: review]
- **A-7** If the platform provides the feature, the feature is used. For any
  job the platform already owns — navigation, surface/window structure, app
  and bottom bars, dialogs and sheets, search, navigation drawers/rails,
  menus, lists, progress indicators, pickers — the platform's mechanism is
  mandatory, and hand-assembling an equivalent out of native parts is still
  a substitution: "every piece is a native component" is not a defence.
  Examples (not the whole rule): a hand-rolled navigation system, a custom
  bottom bar where the platform's navigation bar serves, a hand-built search
  field instead of the platform's search component, a custom drawer, a scrim
  used as a dialog, hand-drawn progress or pickers, a focus override. Any
  such workaround or substitute appears only where it was explicitly
  approved as a deliberate exception on the plan — never introduced silently
  or as a quick fix — and each UI plan item names the native feature it
  uses, so a substitution is visible at approval time. An added escape-hatch or
  substitution signature from the native-patterns checker's list fails the PR unless the plan's approved
  native-deviations list covers it; the Android signature list is seeded by the
  reviewer's catches and grows over time. [Material Design; Android platform
  conventions; check: scan:native-pattern]

## Coding (C)

- **C-1** Names and formatting follow the Kotlin coding conventions —
  clear at the point of use, with no abbreviations a reader must decode.
  [Kotlin coding conventions; check: review]
- **C-2** Data is immutable by default: `val` over `var`, data classes for
  models. Shared mutable state is confined to its owner and exposed
  through the observation system, never reached from multiple threads
  unprotected. [Kotlin coding conventions; Android app architecture guidance;
  check: review]
- **C-3** No `!!` non-null assertions on paths that can be null at
  runtime — nullability is handled with safe calls or validated early.
  `!!` is reserved for invariants the code itself makes provable.
  [Kotlin language practice; check: detekt:UnsafeCallOnNullableType]
- **C-4** A change merges with zero new compiler warnings and a clean lint
  run under the project's ktlint/detekt configuration. [ktlint / detekt standard
  rules; check: ktlint, detekt, androidlint, tool:warnings-as-errors]

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
  the platform's observation system (Kotlin Flows, Compose State, or
  LiveData) — never polled, never manually refreshed. One-shot values stay
  plain: no observation ceremony around constants. [Platform best practice —
  Android; check: review]
- **ENG-2** Responsive layout: screens adapt using the platform's standard
  layout system — rotation, window-size classes, and split-screen on
  Android. No fixed screen dimensions. [Platform best practice — Material Design
  layout; check: advisory:fixed-screen-size, review]
- **ENG-3** Never block a thread: long waits — network calls, spawned
  processes, timers, polling — are asynchronous (coroutines). No sleeping
  on a held thread, and nothing that blocks is callable from the UI (main)
  thread. [Platform best practice — Android; check: scan:blocking-call]
- **ENG-4** Child-process lifetime: any process or worker the app spawns is
  tied to its parent's lifetime — quitting the app or cancelling the task
  cleans it up. No orphaned processes or leaked workers. [Platform best practice;
  check: review]
- **ENG-5** No crash on bad input: invalid input or unexpected data
  produces a typed, surfaced error — never a process crash. Assertions that
  halt the app are reserved for programmer errors, not recoverable
  conditions. [Platform best practice; OWASP Cheat Sheet: Error Handling; check:
  review]
- **ENG-6** Secrets live in the platform's secure store — the Android
  Keystore (with Keystore-backed encryption for stored material) — never in
  plaintext files, source code, or logs. [OWASP MASVS-STORAGE; Android security
  best practices; check: scan:secret-literal, review]

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

- **OWASP Mobile Application Security Verification Standard (MASVS) 2.1** —
  <https://mas.owasp.org/MASVS/> (CC BY-SA 4.0)
- **OWASP Application Security Verification Standard (ASVS) 5.0** —
  <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** — <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **W3C Web Content Accessibility Guidelines (WCAG) 2.2** —
  <https://www.w3.org/TR/WCAG22/> (W3C document license; also ISO/IEC 40500)
- **Google Play Developer Program policies** —
  <https://play.google/developer-content-policy/> (proprietary — referenced only, no text reproduced)
- **Android app security best practices** —
  <https://developer.android.com/privacy-and-security/security-tips> (referenced only)
- **Material Design accessibility guidance** —
  <https://m3.material.io/foundations/accessible-design/overview> (referenced only)
- **Kotlin coding conventions** —
  <https://kotlinlang.org/docs/coding-conventions.html> (referenced only, no text reproduced)
- **Android app architecture guidance** —
  <https://developer.android.com/topic/architecture> (referenced only)
- **ktlint / detekt** (standard rule sets, used as the deterministic
  checkers some rules name) — <https://github.com/pinterest/ktlint>,
  <https://github.com/detekt/detekt> (MIT / Apache 2.0)

No text from these guides is reproduced here — every rule is an original
plain-language statement citing its source — so editing or replacing this
file carries no license obligations for you.
