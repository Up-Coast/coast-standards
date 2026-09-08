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

A React Native app ships to both app stores, so both stores' policies
apply wherever a rule names them.

## Keep it DRY (DRY) — the rule above every other rule

Every piece of knowledge has exactly one home, and everything else uses that
home.

- **DRY-1** Design components are created once and reused. Before any view,
  component or helper is created, an existing one (or a composition of existing
  ones) is checked for; a near-duplicate of an existing component is a review
  failure, and every new component states why nothing existing fit. [Coast
  standard; check: review]
- **DRY-2** Styling lives in one theme file (`theme.ts` (the tokens file)).
  Every colour, font, size, weight and spacing value is a token there; a second
  theme file is never created, and no styling literal is written into a feature
  file. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale (`locales/<lang>/…`).
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
- **L-2** One catalog home per locale (`locales/<lang>/…`). The strings surface
  is the sole authority: additions go through one place, and reuse comes first —
  when an existing key already carries the needed text, that key is used instead
  of a near-duplicate. [Coast standard; check: scan:one-catalog-per-locale]
- **L-3** Keys are semantic, not English: `vehicle.status.doNotDispatch`, not
  `do_not_dispatch_text`. The key names the meaning, so a translation can
  diverge from the English phrasing. [Coast standard; check:
  scan:english-key]
- **L-4** Sentences are never built by concatenation. Text with values in it
  uses the i18n library's interpolation with named placeholders (ICU
  MessageFormat); word order differs across languages, and a template with
  placeholders is itself a catalog entry. [Coast standard; check:
  scan:ui-string-concat]
- **L-5** Plurals go through the platform's plural system (the i18n library's
  plural rules (CLDR categories)), never an `if count == 1` in code. [Coast
  standard; check: scan:manual-plural]
- **L-6** Dates, numbers and currency are formatted by locale-aware formatters
  (`Intl.NumberFormat` / `Intl.DateTimeFormat`), never by string templates. [Up
  Coast standard; check: review]
- **L-7** Layouts tolerate about 30% text expansion: no fixed-width text
  container that clips, tested with a long-string locale (German),
  pseudo-localization and, when in scope, right-to-left. [Coast standard;
  check: review]
- **L-8** Localization plumbing is emitted and managed by tooling (the i18n
  tooling), never hand-authored: the content is written by hand, the plumbing is
  not. [Coast standard; check: review]
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
  `textTransform` style at render time), never baked into the stored string —
  casing rules differ per language, and some scripts have no case at all. [Up
  Coast standard; check: scan:baked-case]

## Design tokens and components (DES)

How the design's values and components reach the code.

- **DES-1** Every visual value is the design's exact token, used by the design's
  token name. A near-match is never inlined, and a value the design needs but
  has no token for is added to the theme as a token, not written at the use
  site. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** A brand-colour or typeface swap is a one-file edit: nothing outside
  the theme file (`theme.ts` (the tokens file)) knows a colour, font or spacing
  value. [Coast standard; check: scan:second-theme-file]
- **DES-3** A new component is justified in writing: the plan or pull request
  names the existing components that were checked and says why none fit, and the
  builder and the approver of a component are different reviews. [Coast
  standard; check: review]
- **DES-4** When the project has a design-system spec, every UI change is
  checked against it: no hardcoded value bypasses the tokens, and a pattern that
  implies a missing token adds the token rather than inlining a value. [Coast
  standard; check: review]
## Money and payments (PAY)

- **PAY-1** Money amounts are stored and calculated with decimal-safe
  types or whole minor units — never JavaScript floating-point arithmetic
  on fractional amounts, which cannot represent cents exactly.
  [Industry-wide practice; see Sources; check: advisory:money-float, review]
- **PAY-2** Every stored money amount carries its currency. Amounts in
  different currencies are never added or compared without an explicit
  conversion step. [Industry-wide practice; check: review]
- **PAY-3** Rounding is decided once (which method, at which step) and every
  total is computed in one place and reused — never recomputed slightly
  differently in two places. [Industry-wide practice; check: tool:jscpd, review]
- **PAY-4** Digital goods and features sold inside the app go through each
  store's in-app purchase system (Apple's on iOS, Google Play billing on
  Android). [Apple App Review Guidelines §3.1; Google Play Payments policy; check:
  review]
- **PAY-5** Raw card numbers never touch the app's own code or storage —
  payment collection goes through a certified payment provider's SDK or the
  platform's payment sheet. [PCI DSS scope rules; OWASP; check: review]

## Security (SEC)

- **SEC-1** All network traffic uses encrypted connections (HTTPS/TLS) on
  both platforms; cleartext traffic stays disabled in the native
  configuration. [OWASP MASVS-NETWORK; check: scan:plaintext-http]
- **SEC-2** Data arriving from outside the app — user input, network
  responses, deep links, shared files — is validated before use, and
  database queries are parameterized, never assembled from strings.
  [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization;
  check: scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography. Encryption, hashing, and random
  generation use platform or well-established library implementations.
  [OWASP MASVS-CRYPTO; check: review]
- **SEC-4** Secrets — API keys, tokens, credentials — never appear in
  source code, logs, analytics, or error messages. The JavaScript bundle is
  readable in a shipped app, so nothing secret may be embedded in JS code
  or config it can reach. [OWASP MASVS-STORAGE; React Native security guidance;
  check: scan:secret-literal]
- **SEC-5** Error messages shown to users never expose internals such as
  stack traces, query text, or file paths. [OWASP Cheat Sheet: Error Handling;
  check: review]
- **SEC-6** JavaScript dependencies are pinned by the lockfile, and
  packages on security-critical paths (payments, auth, storage, crypto)
  are actively maintained and audited before adoption. [OWASP Cheat Sheet: NPM
  Security; supply-chain practice; check: review]

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
  user actually needs. [Apple App Review Guidelines §5.1; Google Play User Data
  policy; check: review]
- **PRIV-2** Every kind of data the app collects or shares is declared in
  both stores' privacy listings (App Store privacy details and Play Data
  safety) — no undeclared collection. [Apple App Review Guidelines §5.1; Google
  Play Data safety requirements; check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash
  reports, or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging; check:
  ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account, and the personal data behind
  it, from inside the app. [Apple App Review Guidelines §5.1.1(v); Google Play
  Account deletion policy; check: review]
- **PRIV-5** Personal data stored on the device lives in the app's
  protected container with platform data protection applied — never in
  world-readable locations, and never in plain AsyncStorage when it is
  sensitive. [OWASP MASVS-STORAGE; React Native security guidance; check: review]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its
  background (3:1 for large text). [WCAG 2.2 — 1.4.3; check: review]
- **ACC-2** Touch targets meet each platform's minimum — 44×44 points on
  iOS, 48×48dp on Android — and never fall below 24×24 pixels.
  [Apple HIG; Material Design accessibility; WCAG 2.2 — 2.5.8; check: review]
- **ACC-3** Every interactive element carries an accessibility label
  (`accessibilityLabel`/role) so screen readers can say what it does.
  [WCAG 2.2 — 4.1.2; React Native accessibility docs; check: review]
- **ACC-4** Text respects the system text-size setting — font scaling is
  not disabled — without truncating away meaning. [WCAG 2.2 — 1.4.4; React Native
  accessibility docs; check: scan:fixed-text-size]
- **ACC-5** Color is never the only signal — errors, success, and selection
  are also conveyed by text, shape, or icon. [WCAG 2.2 — 1.4.1; check: review]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** There is a way to report content, block users, and filter
  objectionable material. [Apple App Review Guidelines §1.2; Google Play UGC
  policy; check: review]
- **UGC-2** Uploaded content is checked for expected type and size before
  it is processed or stored. [OWASP Cheat Sheet: File Upload; check: review]

## Architecture (A)

- **A-1** Code lives in its layer: screens display, presentation logic
  (hooks or view models) prepares what screens show, services hold the
  business rules, repositories do the data access. Business rules never
  sit in components, and the UI never talks to storage or the network
  directly. [Industry-standard separation of concerns: Service layer, Repository
  pattern; React docs; check: scan:layer-import, review]
- **A-2** Module dependencies flow one way, with no cycles: features
  depend on shared domain abstractions, never on each other or on concrete
  data code. [SOLID dependency-inversion principle; acyclic-dependencies
  principle; check: scan:import-matrix]
- **A-3** A module or component has one job. When a change gives it a
  second job, the change splits it instead. Automated size warnings are
  advisory signals for a reviewer, never automatic failures. [SOLID
  single-responsibility principle; check: advisory:type-size, review]
- **A-4** No speculative abstraction: an interface exists only where
  something real substitutes for it — a second implementation or a test
  fake. A boundary between two modules qualifies by definition. [YAGNI — industry
  practice; check: review]
- **A-5** Standard needs — navigation, state, styling — are met with the
  ecosystem's standard mechanism (e.g. React Navigation, React state or an
  established store), not an invented framework that fights the platform.
  [React Native documentation; check: scan:native-pattern]
- **A-6** A name says what a thing is, in the industry-standard
  vocabulary — a Screen is a full navigable screen, a Component is
  reusable presentation, a Repository does data access — and never claims
  a different role than the code performs. [Industry-standard pattern names;
  check: review]
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
  substitution is visible at approval time. An added escape-hatch or substitution
  signature from the native-patterns checker's list fails the PR unless the plan's approved
  native-deviations list covers it; the React Native signature list is seeded by
  the reviewer's catches and grows over time. [React Native documentation;
  check: scan:native-pattern]

## Coding (C)

- **C-1** The codebase is TypeScript with strict mode on; `any` does not
  pass review where a real type is expressible. [TypeScript documentation; check:
  tsc:strict]
- **C-2** Components are function components using hooks, and the Rules of
  Hooks hold everywhere. State is never mutated in place — updates create
  new values. [React documentation: Rules of Hooks; check:
  eslint:react-hooks/rules-of-hooks, eslint:react-hooks/exhaustive-deps]
- **C-3** Every promise is awaited or explicitly handled — no floating
  promises; a rejected promise always surfaces as a handled error.
  [TypeScript/ESLint practice; check:
  eslint:@typescript-eslint/no-floating-promises]
- **C-4** A change merges with zero new TypeScript errors and a clean run
  of the project's ESLint and Prettier configuration. [ESLint / Prettier; check:
  eslint, prettier, tool:warnings-as-errors]

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
  displayed, or that outlives a single function call, lives in React state
  (component state or a store the UI subscribes to) so the UI re-renders
  from it — never module-level variables the UI polls or refreshes
  manually. One-shot values stay plain: no state ceremony around
  constants. [Platform best practice — React; check: review]
- **ENG-2** Responsive layout: screens adapt using flex-based layout and
  the platform's size APIs — rotation and window/screen-size changes on
  both platforms. No fixed screen dimensions. [Platform best practice — React
  Native; check: advisory:fixed-screen-size, review]
- **ENG-3** Never block the JavaScript thread: long waits — network calls,
  heavy computation, timers — are asynchronous, and heavy work moves off
  the UI path. No busy-waiting, and nothing that blocks is callable from a
  render. [Platform best practice — React Native performance docs; check:
  scan:blocking-call]
- **ENG-4** Background work lifetime: any worker, listener, or subscription
  the app starts is tied to its owner's lifetime — unmounting or
  cancelling cleans it up. No leaked timers, listeners, or native
  processes. [Platform best practice — React; check: review]
- **ENG-5** No crash on bad input: invalid input or unexpected data
  produces a typed, surfaced error — never an unhandled exception that
  kills the app. [Platform best practice; OWASP Cheat Sheet: Error Handling;
  check: review]
- **ENG-6** Secrets live in the platform's secure store — Keychain on iOS,
  Keystore on Android, reached through a maintained secure-storage
  module — never in plaintext files, JavaScript code, or logs.
  [OWASP MASVS-STORAGE; React Native security guidance; check:
  scan:secret-literal, review]

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

- **DOC-1** Every exported type and function carries a doc comment saying
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
