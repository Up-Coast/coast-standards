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

- **PAY-1** Money amounts are stored and calculated with decimal-safe
  types or whole minor units — never binary floating-point arithmetic on
  fractional amounts, which cannot represent cents exactly (in JavaScript
  and in the database: `DECIMAL`/`NUMERIC`, not `FLOAT`).
  [Industry-wide practice; see Sources]
- **PAY-2** Every stored money amount carries its currency. Amounts in
  different currencies are never added or compared without an explicit
  conversion step. [Industry-wide practice]
- **PAY-3** Rounding is decided once (which method, at which step) and every
  total is computed in one place and reused — never recomputed slightly
  differently in two places. Totals shown to the user are computed
  server-side, never trusted from the browser. [Industry-wide practice; OWASP ASVS]
- **PAY-4** Raw card numbers never touch the product's own code, servers,
  or storage — payment collection goes through a certified payment
  provider's hosted fields, checkout page, or SDK. [PCI DSS scope rules; OWASP]

## Security (SEC)

- **SEC-1** All traffic uses HTTPS, with HTTP redirecting to HTTPS and
  strict transport security (HSTS) enabled. [OWASP ASVS; OWASP Cheat Sheet: Transport Layer Security]
- **SEC-2** Data arriving from outside — user input, query parameters,
  request bodies, uploaded files, third-party responses — is validated
  server-side before use, and database queries are parameterized, never
  assembled from strings. [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization]
- **SEC-3** Untrusted data rendered into a page goes through the
  framework's escaping — never raw HTML insertion (`innerHTML`,
  `dangerouslySetInnerHTML`) with untrusted content — and a content
  security policy is set. [OWASP Cheat Sheets: XSS Prevention, Content Security Policy]
- **SEC-4** State-changing requests are protected against cross-site
  request forgery (framework CSRF protection on, cookies `SameSite`).
  [OWASP Cheat Sheet: CSRF Prevention]
- **SEC-5** Every server endpoint checks that the signed-in user is allowed
  to reach the specific data it returns — object access is authorized by
  ownership, not by the id being hard to guess. [OWASP ASVS; OWASP Top 10: Broken Access Control]
- **SEC-6** No home-made cryptography. Encryption, hashing, and random
  generation use platform or well-established library implementations.
  [OWASP ASVS]
- **SEC-7** Secrets — API keys, tokens, credentials — exist only
  server-side: never in client-side code, the shipped bundle, source
  control, logs, or error messages. [OWASP ASVS; OWASP Cheat Sheet: Secrets Management]
- **SEC-8** Error pages and API errors never expose internals such as stack
  traces, query text, or file paths. [OWASP Cheat Sheet: Error Handling]
- **SEC-9** JavaScript dependencies are pinned by the lockfile, and
  packages on security-critical paths (payments, auth, storage, crypto)
  are actively maintained and audited before adoption. [OWASP Cheat Sheet: NPM Security]

## Accounts and sign-in (AUTH)

- **AUTH-1** Sign-in uses an established identity provider or framework
  auth system — never a hand-rolled account store. If passwords must be
  stored, they are hashed with a current memory-hard algorithm (Argon2id,
  scrypt, or bcrypt), never encrypted or kept readable.
  [OWASP Cheat Sheets: Authentication, Password Storage]
- **AUTH-2** Session cookies are `Secure`, `HttpOnly`, and `SameSite`;
  sessions expire, can be revoked, and the session id is regenerated at
  sign-in and at any privilege change. [OWASP Cheat Sheet: Session Management]
- **AUTH-3** Sign-in attempts are rate-limited so accounts can't be
  brute-forced. [OWASP ASVS]
- **AUTH-4** Sensitive actions — deleting the account, changing email,
  password, or payment details — re-confirm the user's identity first.
  [OWASP ASVS]

## Privacy and personal data (PRIV)

- **PRIV-1** The product collects only the data the feature in front of
  the user actually needs. [GDPR data-minimization principle]
- **PRIV-2** Non-essential cookies and trackers load only after the user
  consents, and the privacy policy states what is collected and why.
  [GDPR / ePrivacy practice]
- **PRIV-3** Personal data never appears in logs, analytics events, crash
  reports, or URLs (including query strings). [OWASP Cheat Sheet: Logging; OWASP ASVS]
- **PRIV-4** Users can delete their account, and the personal data behind
  it, from inside the product. [GDPR right to erasure]
- **PRIV-5** Personal data at rest is protected: encrypted at the storage
  layer, reachable only through the server's authorized paths, never in
  world-readable buckets or public URLs. [OWASP ASVS; OWASP Top 10]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its
  background (3:1 for large text). [WCAG 2.2 — 1.4.3]
- **ACC-2** Click/tap targets are at least 24×24 pixels, and comfortably
  larger for primary actions. [WCAG 2.2 — 2.5.8]
- **ACC-3** Every interactive element is reachable and operable by
  keyboard alone, with a visible focus indicator. [WCAG 2.2 — 2.1.1, 2.4.7]
- **ACC-4** Interactive elements use semantic HTML (or correct ARIA roles)
  and carry labels a screen reader can announce; images that carry meaning
  have text alternatives. [WCAG 2.2 — 1.1.1, 4.1.2]
- **ACC-5** Text can be resized to 200% (browser zoom and text scaling)
  without truncating away meaning. [WCAG 2.2 — 1.4.4]
- **ACC-6** Color is never the only signal — errors, success, and selection
  are also conveyed by text, shape, or icon. [WCAG 2.2 — 1.4.1]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** There is a way to report content and block users, and posted
  content is sanitized before display (see SEC-3). [Industry practice; OWASP]
- **UGC-2** Uploaded files are checked for expected type and size before
  they are processed or stored, and are never served back executable.
  [OWASP Cheat Sheet: File Upload]

## Architecture (A)

- **A-1** Code lives in its layer: pages and components display,
  presentation logic prepares what is displayed, services hold the
  business rules, repositories do the data access. Business rules never
  sit in components or route handlers, and the UI never talks to storage
  directly. [Industry-standard separation of concerns: Service layer,
  Repository pattern]
- **A-2** Module dependencies flow one way, with no cycles: features
  depend on shared domain abstractions, never on each other or on concrete
  data code. [SOLID dependency-inversion principle; acyclic-dependencies principle]
- **A-3** A module or component has one job. When a change gives it a
  second job, the change splits it instead. Automated size warnings are
  advisory signals for a reviewer, never automatic failures. [SOLID single-responsibility principle]
- **A-4** No speculative abstraction: an interface exists only where
  something real substitutes for it — a second implementation or a test
  fake. Module-boundary seams qualify by definition. [YAGNI — industry practice]
- **A-5** Standard needs — routing, state, data fetching — are met with
  the framework's standard mechanism, not an invented framework that
  fights the one in use. [Framework documentation — per framework]
- **A-6** A name says what a thing is, in the industry-standard
  vocabulary — a page/route is navigable, a component is reusable
  presentation, a repository does data access — and never claims a
  different role than the code performs. [Industry-standard pattern names]

## Coding (C)

- **C-1** The codebase is TypeScript with strict mode on; `any` does not
  pass review where a real type is expressible. [TypeScript documentation —
  deterministic check: the strict compiler flags]
- **C-2** Components and state follow the framework's idiomatic
  conventions (for React: function components, hooks, and the Rules of
  Hooks). State is never mutated in place — updates create new values.
  [Framework documentation; deterministic check where the framework ships
  lint rules]
- **C-3** Every promise is awaited or explicitly handled — no floating
  promises; a rejected promise always surfaces as a handled error.
  [TypeScript/ESLint practice — deterministic check: @typescript-eslint/no-floating-promises]
- **C-4** A change merges with zero new TypeScript errors and a clean run
  of the project's ESLint and Prettier configuration. [ESLint / Prettier —
  deterministic check]

## Engineering quality (ENG)

- **ENG-1** Reactive state: any state that can change while it is
  displayed, or that outlives a single function call, lives in the
  framework's state system (component state or a store the UI subscribes
  to) so the UI re-renders from it — never module-level variables the UI
  polls or refreshes manually. One-shot values stay plain: no state
  ceremony around constants. [Platform best practice — web frameworks]
- **ENG-2** Responsive layout: pages adapt to window size with fluid
  layout (flexbox/grid, relative units, media queries). No fixed page
  dimensions, and no horizontal page scroll at common widths.
  [Platform best practice — responsive web design]
- **ENG-3** Never block the main thread: long waits — network calls, heavy
  computation — are asynchronous, and heavy work moves off the UI path
  (server-side or a worker). No busy-waiting. [Platform best practice — web performance]
- **ENG-4** Background work lifetime: any worker, subscription, interval,
  or listener is tied to its owner's lifetime — unmounting, navigation, or
  cancellation cleans it up. Server-side child processes are tied to their
  parent's lifetime. No leaks, no orphans. [Platform best practice]
- **ENG-5** No crash on bad input: invalid input or unexpected data
  produces a typed, surfaced error — never an unhandled exception. The
  server validates independently of the client (client-side checks are
  convenience, not protection). [OWASP ASVS; OWASP Cheat Sheet: Error Handling]
- **ENG-6** Secrets live in the deployment platform's secret store
  (environment secrets/vault) — never in plaintext files, source control,
  client code, or logs. [OWASP Cheat Sheet: Secrets Management]

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
