<!-- coast-rules-version: 4 -->
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

A React Native app ships to both app stores, so both stores' policies
apply wherever a rule names them.

## Money and payments (PAY)

- **PAY-1** Money amounts are stored and calculated with decimal-safe
  types or whole minor units — never JavaScript floating-point arithmetic
  on fractional amounts, which cannot represent cents exactly.
  [Industry-wide practice; see Sources]
- **PAY-2** Every stored money amount carries its currency. Amounts in
  different currencies are never added or compared without an explicit
  conversion step. [Industry-wide practice]
- **PAY-3** Rounding is decided once (which method, at which step) and every
  total is computed in one place and reused — never recomputed slightly
  differently in two places. [Industry-wide practice]
- **PAY-4** Digital goods and features sold inside the app go through each
  store's in-app purchase system (Apple's on iOS, Google Play billing on
  Android). [Apple App Review Guidelines §3.1; Google Play Payments policy]
- **PAY-5** Raw card numbers never touch the app's own code or storage —
  payment collection goes through a certified payment provider's SDK or the
  platform's payment sheet. [PCI DSS scope rules; OWASP]

## Security (SEC)

- **SEC-1** All network traffic uses encrypted connections (HTTPS/TLS) on
  both platforms; cleartext traffic stays disabled in the native
  configuration. [OWASP MASVS-NETWORK]
- **SEC-2** Data arriving from outside the app — user input, network
  responses, deep links, shared files — is validated before use, and
  database queries are parameterized, never assembled from strings.
  [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization]
- **SEC-3** No home-made cryptography. Encryption, hashing, and random
  generation use platform or well-established library implementations.
  [OWASP MASVS-CRYPTO]
- **SEC-4** Secrets — API keys, tokens, credentials — never appear in
  source code, logs, analytics, or error messages. The JavaScript bundle is
  readable in a shipped app, so nothing secret may be embedded in JS code
  or config it can reach. [OWASP MASVS-STORAGE; React Native security guidance]
- **SEC-5** Error messages shown to users never expose internals such as
  stack traces, query text, or file paths. [OWASP Cheat Sheet: Error Handling]
- **SEC-6** JavaScript dependencies are pinned by the lockfile, and
  packages on security-critical paths (payments, auth, storage, crypto)
  are actively maintained and audited before adoption. [OWASP Cheat Sheet:
  NPM Security; supply-chain practice]

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
  user actually needs. [Apple App Review Guidelines §5.1; Google Play User Data policy]
- **PRIV-2** Every kind of data the app collects or shares is declared in
  both stores' privacy listings (App Store privacy details and Play Data
  safety) — no undeclared collection. [Apple App Review Guidelines §5.1; Google Play Data safety requirements]
- **PRIV-3** Personal data never appears in logs, analytics events, crash
  reports, or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging]
- **PRIV-4** Users can delete their account, and the personal data behind
  it, from inside the app. [Apple App Review Guidelines §5.1.1(v); Google Play Account deletion policy]
- **PRIV-5** Personal data stored on the device lives in the app's
  protected container with platform data protection applied — never in
  world-readable locations, and never in plain AsyncStorage when it is
  sensitive. [OWASP MASVS-STORAGE; React Native security guidance]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its
  background (3:1 for large text). [WCAG 2.2 — 1.4.3]
- **ACC-2** Touch targets meet each platform's minimum — 44×44 points on
  iOS, 48×48dp on Android — and never fall below 24×24 pixels.
  [Apple HIG; Material Design accessibility; WCAG 2.2 — 2.5.8]
- **ACC-3** Every interactive element carries an accessibility label
  (`accessibilityLabel`/role) so screen readers can say what it does.
  [WCAG 2.2 — 4.1.2; React Native accessibility docs]
- **ACC-4** Text respects the system text-size setting — font scaling is
  not disabled — without truncating away meaning. [WCAG 2.2 — 1.4.4; React Native accessibility docs]
- **ACC-5** Color is never the only signal — errors, success, and selection
  are also conveyed by text, shape, or icon. [WCAG 2.2 — 1.4.1]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** There is a way to report content, block users, and filter
  objectionable material. [Apple App Review Guidelines §1.2; Google Play UGC policy]
- **UGC-2** Uploaded content is checked for expected type and size before
  it is processed or stored. [OWASP Cheat Sheet: File Upload]

## Architecture (A)

- **A-1** Code lives in its layer: screens display, presentation logic
  (hooks or view models) prepares what screens show, services hold the
  business rules, repositories do the data access. Business rules never
  sit in components, and the UI never talks to storage or the network
  directly. [Industry-standard separation of concerns: Service layer,
  Repository pattern; React docs]
- **A-2** Module dependencies flow one way, with no cycles: features
  depend on shared domain abstractions, never on each other or on concrete
  data code. [SOLID dependency-inversion principle; acyclic-dependencies principle]
- **A-3** A module or component has one job. When a change gives it a
  second job, the change splits it instead. Automated size warnings are
  advisory signals for a reviewer, never automatic failures. [SOLID single-responsibility principle]
- **A-4** No speculative abstraction: an interface exists only where
  something real substitutes for it — a second implementation or a test
  fake. Module-boundary seams qualify by definition. [YAGNI — industry practice]
- **A-5** Standard needs — navigation, state, styling — are met with the
  ecosystem's standard mechanism (e.g. React Navigation, React state or an
  established store), not an invented framework that fights the platform.
  [React Native documentation]
- **A-6** A name says what a thing is, in the industry-standard
  vocabulary — a Screen is a full navigable screen, a Component is
  reusable presentation, a Repository does data access — and never claims
  a different role than the code performs. [Industry-standard pattern names]
- **A-7** If the ecosystem provides the feature, the feature is used. For
  any job the ecosystem already owns — navigation, screen structure, tab
  bars, modals, search, drawers, headers, lists, progress indicators,
  pickers — the standard native mechanism (React Navigation, the platform's
  native containers and controls) is mandatory, and hand-assembling an
  equivalent out of standard parts is still a substitution: "every piece is
  a standard component" is not a defence. Examples (not the whole rule): a
  hand-rolled navigator, a custom tab bar where the navigator's tabs serve,
  a hand-built header instead of the navigator's, a custom modal scheme that
  fights the platform, hand-drawn progress or pickers. Any such workaround
  or substitute appears only where it was explicitly approved as a
  deliberate exception on the plan — never introduced silently or as a quick
  fix — and each UI plan item names the native feature it uses, so a
  substitution is visible at approval time. [React Native documentation;
  deterministic check: Scripts/checks/check_native_patterns.py — an added
  escape-hatch or substitution signature from its list fails the PR unless
  the plan's approved native-deviations list covers it; the React Native
  signature list is seeded by the reviewer's catches and grows over time]

## Coding (C)

- **C-1** The codebase is TypeScript with strict mode on; `any` does not
  pass review where a real type is expressible. [TypeScript documentation —
  deterministic check: the strict compiler flags]
- **C-2** Components are function components using hooks, and the Rules of
  Hooks hold everywhere. State is never mutated in place — updates create
  new values. [React documentation: Rules of Hooks; deterministic check:
  eslint-plugin-react-hooks]
- **C-3** Every promise is awaited or explicitly handled — no floating
  promises; a rejected promise always surfaces as a handled error.
  [TypeScript/ESLint practice — deterministic check: @typescript-eslint/no-floating-promises]
- **C-4** A change merges with zero new TypeScript errors and a clean run
  of the project's ESLint and Prettier configuration. [ESLint / Prettier —
  deterministic check]

## Engineering quality (ENG)

- **ENG-1** Reactive state: any state that can change while it is
  displayed, or that outlives a single function call, lives in React state
  (component state or a store the UI subscribes to) so the UI re-renders
  from it — never module-level variables the UI polls or refreshes
  manually. One-shot values stay plain: no state ceremony around
  constants. [Platform best practice — React]
- **ENG-2** Responsive layout: screens adapt using flex-based layout and
  the platform's size APIs — rotation and window/screen-size changes on
  both platforms. No fixed screen dimensions. [Platform best practice — React Native]
- **ENG-3** Never block the JavaScript thread: long waits — network calls,
  heavy computation, timers — are asynchronous, and heavy work moves off
  the UI path. No busy-waiting, and nothing that blocks is callable from a
  render. [Platform best practice — React Native performance docs]
- **ENG-4** Background work lifetime: any worker, listener, or subscription
  the app starts is tied to its owner's lifetime — unmounting or
  cancelling cleans it up. No leaked timers, listeners, or native
  processes. [Platform best practice — React]
- **ENG-5** No crash on bad input: invalid input or unexpected data
  produces a typed, surfaced error — never an unhandled exception that
  kills the app. [Platform best practice; OWASP Cheat Sheet: Error Handling]
- **ENG-6** Secrets live in the platform's secure store — Keychain on iOS,
  Keystore on Android, reached through a maintained secure-storage
  module — never in plaintext files, JavaScript code, or logs.
  [OWASP MASVS-STORAGE; React Native security guidance]

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

- **DOC-1** Every exported type and function carries a doc comment saying
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
- **OWASP Cheat Sheet Series** (incl. NPM Security) —
  <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **W3C Web Content Accessibility Guidelines (WCAG) 2.2** —
  <https://www.w3.org/TR/WCAG22/> (W3C document license; also ISO/IEC 40500)
- **React Native security and accessibility documentation** —
  <https://reactnative.dev/docs/security> (MIT-licensed docs)
- **React documentation** (incl. Rules of Hooks) —
  <https://react.dev/> (CC BY 4.0 — referenced only, no text reproduced)
- **TypeScript documentation** —
  <https://www.typescriptlang.org/docs/> (referenced only)
- **ESLint / typescript-eslint / Prettier** (standard rule sets, used as
  the deterministic checkers some rules name) — <https://eslint.org/>,
  <https://typescript-eslint.io/>, <https://prettier.io/> (MIT)
- **Apple App Review Guidelines** —
  <https://developer.apple.com/app-store/review/guidelines/> (proprietary — referenced only, no text reproduced)
- **Google Play Developer Program policies** —
  <https://play.google/developer-content-policy/> (proprietary — referenced only, no text reproduced)

No text from these guides is reproduced here — every rule is an original
plain-language statement citing its source — so editing or replacing this
file carries no license obligations for you.
