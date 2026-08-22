<!-- coast-rules-version: 3 -->
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

## Money and payments (PAY)

- **PAY-1** Money amounts are stored and calculated with decimal or
  whole-number types — never binary floating-point types (`Float`,
  `Double`), which cannot represent cents exactly. [Industry-wide practice;
  see Sources]
- **PAY-2** Every stored money amount carries its currency. Amounts in
  different currencies are never added or compared without an explicit
  conversion step. [Industry-wide practice]
- **PAY-3** Rounding is decided once (which method, at which step) and every
  total is computed in one place and reused — never recomputed slightly
  differently in two places. [Industry-wide practice]
- **PAY-4** Digital goods and features sold inside the app go through
  Google Play's billing system. [Google Play Payments policy]
- **PAY-5** Raw card numbers never touch the app's own code or storage —
  payment collection goes through a certified payment provider's SDK or the
  platform's payment sheet. [PCI DSS scope rules; OWASP]

## Security (SEC)

- **SEC-1** All network traffic uses encrypted connections (HTTPS/TLS), and
  cleartext traffic is disabled in the app's network security
  configuration. [OWASP MASVS-NETWORK; Android security best practices]
- **SEC-2** Data arriving from outside the app — user input, network
  responses, deep links, shared files, intents — is validated before use,
  and database queries are parameterized, never assembled from strings.
  [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization]
- **SEC-3** No home-made cryptography. Encryption, hashing, and random
  generation use the platform or standard library implementations.
  [OWASP MASVS-CRYPTO]
- **SEC-4** Secrets — API keys, tokens, credentials — never appear in
  source code, logs, analytics, or error messages. [OWASP ASVS; MASVS-STORAGE]
- **SEC-5** Error messages shown to users never expose internals such as
  stack traces, query text, or file paths. [OWASP Cheat Sheet: Error Handling]
- **SEC-6** App components (activities, services, receivers, providers) are
  not exported unless another app genuinely needs to reach them, and every
  exported component validates what it receives. [Android security best practices;
  OWASP MASVS-PLATFORM]

## Accounts and sign-in (AUTH)

- **AUTH-1** Sign-in uses the platform's sign-in system or an established
  identity provider — never a hand-rolled account store. If passwords must
  be stored, they are hashed with a current memory-hard algorithm
  (Argon2id, scrypt, or bcrypt), never encrypted or kept readable.
  [OWASP Cheat Sheets: Authentication, Password Storage]
- **AUTH-2** Session tokens expire, can be revoked, and are regenerated at
  sign-in and at any privilege change. [OWASP Cheat Sheet: Session Management]
- **AUTH-3** Sign-in attempts are rate-limited so accounts can't be
  brute-forced. [OWASP ASVS]
- **AUTH-4** Sensitive actions — deleting the account, changing email,
  password, or payment details — re-confirm the user's identity first.
  [OWASP ASVS]

## Privacy and personal data (PRIV)

- **PRIV-1** The app collects only the data the feature in front of the
  user actually needs. [Google Play User Data policy; GDPR data-minimization principle]
- **PRIV-2** Every kind of data the app collects or shares is declared in
  the Play Console's Data safety section — no undeclared collection.
  [Google Play Data safety requirements]
- **PRIV-3** Personal data never appears in logs, analytics events, crash
  reports, or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging]
- **PRIV-4** Users can delete their account, and the personal data behind
  it, from inside the app (with the web deletion path Play policy also
  requires). [Google Play Account deletion policy]
- **PRIV-5** Personal data stored on the device lives in the app's internal
  storage, encrypted with Keystore-backed keys where it is sensitive —
  never in world-readable locations or external storage. [OWASP MASVS-STORAGE]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its
  background (3:1 for large text). [WCAG 2.2 — 1.4.3; Material Design accessibility]
- **ACC-2** Touch targets are at least 48×48dp per platform guidance, and
  never smaller than 24×24 pixels. [Material Design accessibility; WCAG 2.2 — 2.5.8]
- **ACC-3** Every interactive element has a content description so screen
  readers (TalkBack) can say what it does. [WCAG 2.2 — 4.1.2; Material Design accessibility]
- **ACC-4** Text respects the system font-size setting (scalable sp units)
  without truncating away meaning. [Material Design accessibility; WCAG 2.2 — 1.4.4]
- **ACC-5** Color is never the only signal — errors, success, and selection
  are also conveyed by text, shape, or icon. [WCAG 2.2 — 1.4.1]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** There is a way to report content, block users, and filter
  objectionable material. [Google Play User Generated Content policy]
- **UGC-2** Uploaded content is checked for expected type and size before
  it is processed or stored. [OWASP Cheat Sheet: File Upload]

## Architecture (A)

- **A-1** Code lives in its layer: screens display, view models prepare
  what screens show, services hold the business rules, repositories do the
  data access. Business rules never sit in screens or view models, and the
  UI never talks to storage directly. [Industry-standard separation of
  concerns: MVVM, Service layer, Repository pattern; Android app architecture guidance]
- **A-2** Module dependencies flow one way, with no cycles: features
  depend on shared domain abstractions, never on each other or on concrete
  data code. [SOLID dependency-inversion principle; acyclic-dependencies principle]
- **A-3** A type or module has one job. When a change gives it a second
  job, the change splits it instead. Automated size warnings are advisory
  signals for a reviewer, never automatic failures. [SOLID single-responsibility principle]
- **A-4** No speculative abstraction: an interface exists only where
  something real substitutes for it — a second implementation or a test
  fake. Module-boundary seams qualify by definition. [YAGNI — industry practice]
- **A-5** Standard needs — navigation, state, dependency wiring — are met
  with the platform's standard mechanism, not an invented framework that
  fights the platform. [Android app architecture guidance]
- **A-6** A name says what a thing is, in the industry-standard
  vocabulary — a ViewModel prepares display state, a Repository does data
  access, a Screen is a full navigable screen — and never claims a
  different role than the code performs. [Industry-standard pattern names;
  Kotlin coding conventions]
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
  uses, so a substitution is visible at approval time. [Material Design;
  Android platform conventions; deterministic check:
  Scripts/checks/check_native_patterns.py — an added escape-hatch or
  substitution signature from its list fails the PR unless the plan's
  approved native-deviations list covers it; the Android signature list is
  seeded by the reviewer's catches and grows over time]

## Coding (C)

- **C-1** Names and formatting follow the Kotlin coding conventions —
  clear at the point of use, with no abbreviations a reader must decode.
  [Kotlin coding conventions]
- **C-2** Data is immutable by default: `val` over `var`, data classes for
  models. Shared mutable state is confined to its owner and exposed
  through the observation system, never reached from multiple threads
  unprotected. [Kotlin coding conventions; Android app architecture guidance]
- **C-3** No `!!` non-null assertions on paths that can be null at
  runtime — nullability is handled with safe calls or validated early.
  `!!` is reserved for invariants the code itself makes provable.
  [Kotlin language practice; deterministic check: detekt UnsafeCallOnNullableType]
- **C-4** A change merges with zero new compiler warnings and a clean lint
  run under the project's ktlint/detekt configuration. [ktlint / detekt
  standard rules — deterministic check]

## Engineering quality (ENG)

- **ENG-1** Reactive state: any state that can change while it is
  displayed, or that outlives a single function call, is published through
  the platform's observation system (Kotlin Flows, Compose State, or
  LiveData) — never polled, never manually refreshed. One-shot values stay
  plain: no observation ceremony around constants. [Platform best practice — Android]
- **ENG-2** Responsive layout: screens adapt using the platform's standard
  layout system — rotation, window-size classes, and split-screen on
  Android. No fixed screen dimensions. [Platform best practice — Material Design layout]
- **ENG-3** Never block a thread: long waits — network calls, spawned
  processes, timers, polling — are asynchronous (coroutines). No sleeping
  on a held thread, and nothing that blocks is callable from the UI (main)
  thread. [Platform best practice — Android]
- **ENG-4** Child-process lifetime: any process or worker the app spawns is
  tied to its parent's lifetime — quitting the app or cancelling the task
  cleans it up. No orphaned processes or leaked workers. [Platform best practice]
- **ENG-5** No crash on bad input: invalid input or unexpected data
  produces a typed, surfaced error — never a process crash. Assertions that
  halt the app are reserved for programmer errors, not recoverable
  conditions. [Platform best practice; OWASP Cheat Sheet: Error Handling]
- **ENG-6** Secrets live in the platform's secure store — the Android
  Keystore (with Keystore-backed encryption for stored material) — never in
  plaintext files, source code, or logs. [OWASP MASVS-STORAGE; Android security best practices]

## Tests (TEST)

- **TEST-1** Every acceptance criterion has at least one automated test,
  and each test states which acceptance criterion it verifies. [Project rule]
- **TEST-2** Tests that gate a merge run without live external services —
  external dependencies are faked locally. Tests against live services run
  separately and never block a merge. [Project rule; Google Testing Blog: hermetic testing]
- **TEST-3** A test proves behavior: it fails when the behavior it names is
  broken. Assertions so weak that any implementation passes don't count as
  coverage. [Project rule]

## Documentation (DOC)

- **DOC-1** Every public type and function carries a doc comment saying
  what it does — including parameters and return value where they aren't
  obvious. The generated API reference is built from these. [Project rule]
- **DOC-2** A doc comment must match what the code actually does. A doc
  that reads wrong is treated as a code problem, not a wording problem.
  [Project rule]

---

## Sources

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
