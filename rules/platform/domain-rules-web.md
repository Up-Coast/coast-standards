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
- **DRY-2** Styling lives in one theme file (`theme.ts` or the tokens
  stylesheet). Every colour, font, size, weight and spacing value is a token
  there; a second theme file is never created, and no styling literal is written
  into a feature file. [Coast standard; check: scan:styling-literal,
  scan:second-theme-file]
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
- **L-12** All-caps and letter-spacing effects are applied at render time (CSS
  `text-transform` at render time), never baked into the stored string — casing
  rules differ per language, and some scripts have no case at all. [Coast
  standard; check: scan:baked-case]

## Design tokens and components (DES)

How the design's values and components reach the code.

- **DES-1** Every visual value is the design's exact token, used by the design's
  token name. A near-match is never inlined, and a value the design needs but
  has no token for is added to the theme as a token, not written at the use
  site. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** A brand-colour or typeface swap is a one-file edit: nothing outside
  the theme file (`theme.ts` or the tokens stylesheet) knows a colour, font or
  spacing value. [Coast standard; check: scan:second-theme-file]
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
  types or whole minor units — never binary floating-point arithmetic on
  fractional amounts, which cannot represent cents exactly (in JavaScript
  and in the database: `DECIMAL`/`NUMERIC`, not `FLOAT`).
  [Industry-wide practice; see Sources; check: advisory:money-float, review]
- **PAY-2** Every stored money amount carries its currency. Amounts in
  different currencies are never added or compared without an explicit
  conversion step. [Industry-wide practice; check: review]
- **PAY-3** Rounding is decided once (which method, at which step) and every
  total is computed in one place and reused — never recomputed slightly
  differently in two places. Totals shown to the user are computed
  server-side, never trusted from the browser. [Industry-wide practice; OWASP
  ASVS; check: tool:jscpd, review]
- **PAY-4** Raw card numbers never touch the product's own code, servers,
  or storage — payment collection goes through a certified payment
  provider's hosted fields, checkout page, or SDK. [PCI DSS scope rules; OWASP;
  check: review]

## Security (SEC)

- **SEC-1** All traffic uses HTTPS, with HTTP redirecting to HTTPS and
  strict transport security (HSTS) enabled. [OWASP ASVS; OWASP Cheat Sheet:
  Transport Layer Security; check: scan:plaintext-http]
- **SEC-2** Data arriving from outside — user input, query parameters,
  request bodies, uploaded files, third-party responses — is validated
  server-side before use, and database queries are parameterized, never
  assembled from strings. [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query
  Parameterization; check: scan:sql-string-assembly, review]
- **SEC-3** Untrusted data rendered into a page goes through the
  framework's escaping — never raw HTML insertion (`innerHTML`,
  `dangerouslySetInnerHTML`) with untrusted content — and a content
  security policy is set. [OWASP Cheat Sheets: XSS Prevention, Content Security
  Policy; check: scan:raw-html, review]
- **SEC-4** State-changing requests are protected against cross-site
  request forgery (framework CSRF protection on, cookies `SameSite`).
  [OWASP Cheat Sheet: CSRF Prevention; check: review]
- **SEC-5** Every server endpoint checks that the signed-in user is allowed
  to reach the specific data it returns — object access is authorized by
  ownership, not by the id being hard to guess. [OWASP ASVS; OWASP Top 10: Broken
  Access Control; check: review]
- **SEC-6** No home-made cryptography. Encryption, hashing, and random
  generation use platform or well-established library implementations.
  [OWASP ASVS; check: review]
- **SEC-7** Secrets — API keys, tokens, credentials — exist only
  server-side: never in client-side code, the shipped bundle, source
  control, logs, or error messages. [OWASP ASVS; OWASP Cheat Sheet: Secrets
  Management; check: scan:secret-literal]
- **SEC-8** Error pages and API errors never expose internals such as stack
  traces, query text, or file paths. [OWASP Cheat Sheet: Error Handling; check:
  review]
- **SEC-9** JavaScript dependencies are pinned by the lockfile, and
  packages on security-critical paths (payments, auth, storage, crypto)
  are actively maintained and audited before adoption. [OWASP Cheat Sheet: NPM
  Security; check: review]

## Accounts and sign-in (AUTH)

- **AUTH-1** Sign-in uses an established identity provider or framework
  auth system — never a hand-rolled account store. If passwords must be
  stored, they are hashed with a current memory-hard algorithm (Argon2id,
  scrypt, or bcrypt), never encrypted or kept readable.
  [OWASP Cheat Sheets: Authentication, Password Storage; check: review]
- **AUTH-2** Session cookies are `Secure`, `HttpOnly`, and `SameSite`;
  sessions expire, can be revoked, and the session id is regenerated at
  sign-in and at any privilege change. [OWASP Cheat Sheet: Session Management;
  check: review]
- **AUTH-3** Sign-in attempts are rate-limited so accounts can't be
  brute-forced. [OWASP ASVS; check: review]
- **AUTH-4** Sensitive actions — deleting the account, changing email,
  password, or payment details — re-confirm the user's identity first.
  [OWASP ASVS; check: review]

## Privacy and personal data (PRIV)

- **PRIV-1** The product collects only the data the feature in front of
  the user actually needs. [GDPR data-minimization principle; check: review]
- **PRIV-2** Non-essential cookies and trackers load only after the user
  consents, and the privacy policy states what is collected and why.
  [GDPR / ePrivacy practice; check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash
  reports, or URLs (including query strings). [OWASP Cheat Sheet: Logging; OWASP
  ASVS; check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account, and the personal data behind
  it, from inside the product. [GDPR right to erasure; check: review]
- **PRIV-5** Personal data at rest is protected: encrypted at the storage
  layer, reachable only through the server's authorized paths, never in
  world-readable buckets or public URLs. [OWASP ASVS; OWASP Top 10; check: review]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its
  background (3:1 for large text). [WCAG 2.2 — 1.4.3; check: review]
- **ACC-2** Click/tap targets are at least 24×24 pixels, and comfortably
  larger for primary actions. [WCAG 2.2 — 2.5.8; check: review]
- **ACC-3** Every interactive element is reachable and operable by
  keyboard alone, with a visible focus indicator. [WCAG 2.2 — 2.1.1, 2.4.7; check:
  review]
- **ACC-4** Interactive elements use semantic HTML (or correct ARIA roles)
  and carry labels a screen reader can announce; images that carry meaning
  have text alternatives. [WCAG 2.2 — 1.1.1, 4.1.2; check: review]
- **ACC-5** Text can be resized to 200% (browser zoom and text scaling)
  without truncating away meaning. [WCAG 2.2 — 1.4.4; check: scan:fixed-text-size]
- **ACC-6** Color is never the only signal — errors, success, and selection
  are also conveyed by text, shape, or icon. [WCAG 2.2 — 1.4.1; check: review]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** There is a way to report content and block users, and posted
  content is sanitized before display (see SEC-3). [Industry practice; OWASP;
  check: review]
- **UGC-2** Uploaded files are checked for expected type and size before
  they are processed or stored, and are never served back executable.
  [OWASP Cheat Sheet: File Upload; check: review]

## Architecture (A)

- **A-1** Code lives in its layer: pages and components display,
  presentation logic prepares what is displayed, services hold the
  business rules, repositories do the data access. Business rules never
  sit in components or route handlers, and the UI never talks to storage
  directly. [Industry-standard separation of concerns: Service layer, Repository
  pattern; check: scan:layer-import, review]
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
- **A-5** Standard needs — routing, state, data fetching — are met with
  the framework's standard mechanism, not an invented framework that
  fights the one in use. [Framework documentation — per framework; check:
  scan:native-pattern]
- **A-6** A name says what a thing is, in the industry-standard
  vocabulary — a page/route is navigable, a component is reusable
  presentation, a repository does data access — and never claims a
  different role than the code performs. [Industry-standard pattern names; check:
  review]

## Coding (C)

- **C-1** The codebase is TypeScript with strict mode on; `any` does not
  pass review where a real type is expressible. [TypeScript documentation; check:
  tsc:strict]
- **C-2** Components and state follow the framework's idiomatic
  conventions (for React: function components, hooks, and the Rules of
  Hooks). State is never mutated in place — updates create new values.
  [Framework documentation; check: eslint, review]
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
  displayed, or that outlives a single function call, lives in the
  framework's state system (component state or a store the UI subscribes
  to) so the UI re-renders from it — never module-level variables the UI
  polls or refreshes manually. One-shot values stay plain: no state
  ceremony around constants. [Platform best practice — web frameworks; check:
  review]
- **ENG-2** Responsive layout: pages adapt to window size with fluid
  layout (flexbox/grid, relative units, media queries). No fixed page
  dimensions, and no horizontal page scroll at common widths.
  [Platform best practice — responsive web design; check:
  advisory:fixed-screen-size, review]
- **ENG-3** Never block the main thread: long waits — network calls, heavy
  computation — are asynchronous, and heavy work moves off the UI path
  (server-side or a worker). No busy-waiting. [Platform best practice — web
  performance; check: scan:blocking-call]
- **ENG-4** Background work lifetime: any worker, subscription, interval,
  or listener is tied to its owner's lifetime — unmounting, navigation, or
  cancellation cleans it up. Server-side child processes are tied to their
  parent's lifetime. No leaks, no orphans. [Platform best practice; check: review]
- **ENG-5** No crash on bad input: invalid input or unexpected data
  produces a typed, surfaced error — never an unhandled exception. The
  server validates independently of the client (client-side checks are
  convenience, not protection). [OWASP ASVS; OWASP Cheat Sheet: Error Handling;
  check: review]
- **ENG-6** Secrets live in the deployment platform's secret store
  (environment secrets/vault) — never in plaintext files, source control,
  client code, or logs. [OWASP Cheat Sheet: Secrets Management; check:
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

- **OWASP Application Security Verification Standard (ASVS) 5.0** —
  <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** (XSS Prevention, CSRF Prevention, Session
  Management, Secrets Management, NPM Security, File Upload, and others) —
  <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **OWASP Top 10** — <https://owasp.org/www-project-top-ten/> (CC BY-SA 4.0)
- **W3C Web Content Accessibility Guidelines (WCAG) 2.2** —
  <https://www.w3.org/TR/WCAG22/> (W3C document license; also ISO/IEC 40500)
- **TypeScript documentation** —
  <https://www.typescriptlang.org/docs/> (referenced only)
- **React documentation** (incl. Rules of Hooks; applies when the project
  uses React) — <https://react.dev/> (CC BY 4.0 — referenced only, no text reproduced)
- **ESLint / typescript-eslint / Prettier** (standard rule sets, used as
  the deterministic checkers some rules name) — <https://eslint.org/>,
  <https://typescript-eslint.io/>, <https://prettier.io/> (MIT)

No text from these guides is reproduced here — every rule is an original
plain-language statement citing its source — so editing or replacing this
file carries no license obligations for you.
