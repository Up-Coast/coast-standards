<!-- coast-standards-release: 1.12.1 -->
# Project rules

Your project's rules: edit, delete or add any; reviewers check every change against this file. Each rule ends with what checks it: `review` a reviewer, `scan:` the scanner refuses it, `ratchet:` a count that may only fall, `advisory:` reported only, `tool:`, `tsc`, `eslint` or `prettier` the pre-push hook, `process` the pipeline or a person. Write every rule so a reviewer can answer yes or no.

## Keep it DRY (DRY)

DRY comes before every other rule: each piece of knowledge lives in one place.

- **DRY-1** Reuse an existing component, helper or combination before creating one, and state why none fit; a near-duplicate fails review. [check: review]
- **DRY-2** Every colour, font, size, weight and spacing is a token in the one theme file (`theme.ts` or the tokens stylesheet); no second theme file, no styling value in a feature file. [check: scan:styling-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale (`locales/<lang>/…`); reuse a key before adding a near-duplicate. [check: scan:one-catalog-per-locale]
- **DRY-4** Error messages live in the catalog; never build error text where it is thrown or shown. [check: scan:ui-string-literal]
- **DRY-5** Shared behaviour (routing, gestures, animations, formatting, validation, error and after-save paths) lives in one place; one module decides where every screen, overlay and action goes next, Back, Close, Cancel and errors included, and a screen never names its own destinations or calls the navigation API itself. [check: tool:jscpd, review]
- **DRY-6** Compute each derived value (total, score, status, rounding) in one place. [check: tool:jscpd, review]
- **DRY-7** One name per thing everywhere; never add a synonym. [check: review]

## Strings and localization (L)

- **L-1** From the first commit, every user-visible string is a catalog key: labels, errors, empty states, loading text, tooltips, accessibility labels, titles, notifications, units; the build fails on a bare string in view code. [check: scan:ui-string-literal]
- **L-2** The `locales/<lang>/…` catalog is each locale's only string source (see DRY-3). [check: scan:one-catalog-per-locale]
- **L-3** Keys name the meaning, not the English (`vehicle.status.doNotDispatch`, not `do_not_dispatch_text`). [check: scan:english-key]
- **L-4** Never join strings into sentences; use the i18n library's ICU MessageFormat named placeholders, with the template itself a catalog entry. [check: scan:ui-string-concat]
- **L-5** Plurals use the i18n library's CLDR plural rules, never `if count == 1`. [check: scan:manual-plural]
- **L-6** Format dates, numbers and currency with `Intl.NumberFormat` and `Intl.DateTimeFormat`, never templates. [check: review]
- **L-7** Layouts fit text 30% longer than English without clipping; test German, pseudo-locale and, in scope, right-to-left. [check: review]
- **L-8** The i18n tooling generates and manages the plumbing; write only the text by hand. [check: review]
- **L-9** Safety-critical and client-owned terms (status tiers, legal words) use the glossary file's approved translations word for word; never translate them yourself. [check: review]
- **L-10** Database and API text is localized too: per-locale fields, or stable codes mapped to catalog keys. [check: review]
- **L-11** Users can see and change the language; it applies at once, persists (profile, local storage or URL) and never discards typed input. [check: review]
- **L-12** Apply all-caps and letter-spacing at render time with CSS `text-transform`, never in stored strings. [check: scan:baked-case]

## Design tokens and components (DES)

- **DES-1** Use the design's exact token by its design name, never a near-match; add a missing token to the theme. [check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** A brand colour or typeface change edits only the theme file (`theme.ts` or the tokens stylesheet). [check: scan:second-theme-file]
- **DES-3** A new component's plan or pull request names the components checked and why none fit; a different reviewer approves it. [check: review]
- **DES-4** Check every UI change against the project's design-system spec, when there is one; no value bypasses the tokens. [check: review]

## Money and payments (PAY)

- **PAY-1** Store and compute money as decimal types or whole minor units, never binary floats, in JavaScript and the database (`DECIMAL`/`NUMERIC`, not `FLOAT`). [check: advisory:money-float, review]
- **PAY-2** Store every amount with its currency; convert explicitly before adding or comparing currencies. [check: review]
- **PAY-3** Choose rounding method and step once; compute every total in one place, on the server, never trusting browser totals. [check: tool:jscpd, review]
- **PAY-4** Card numbers never touch the product's code, servers or storage; use a certified provider's hosted fields, checkout page or SDK. [check: review]

## Security (SEC)

- **SEC-1** All traffic uses HTTPS; HTTP redirects to HTTPS and HSTS is on. [check: scan:plaintext-http]
- **SEC-2** Validate all outside data (input, query parameters, bodies, uploads, third-party responses) on the server and parameterize every query. [check: scan:sql-string-assembly, review]
- **SEC-3** Render untrusted data through the framework's escaping, never `innerHTML` or `dangerouslySetInnerHTML`; set a content security policy. [check: scan:raw-html, review]
- **SEC-4** Turn on the framework's CSRF protection for state-changing requests and set cookies `SameSite`. [check: review]
- **SEC-5** Every endpoint checks the signed-in user may access the specific data returned; authorize by ownership, never by a hard-to-guess id. [check: review]
- **SEC-6** Never write your own cryptography; use the platform's or an established library's encryption, hashing and random generation. [check: review]
- **SEC-7** Secrets exist only on the server, never in client code, the bundle, source control, logs or error messages. [check: scan:secret-literal]
- **SEC-8** Error pages and API errors never show stack traces, query text or file paths. [check: review]
- **SEC-9** Pin dependencies with the lockfile; confirm a package on a security-critical path (payments, auth, storage, crypto) is maintained and audit it before adopting it. [check: review]

## Accounts and sign-in (AUTH)

- **AUTH-1** Use an established identity provider or the framework's auth, never a hand-built account store; any stored password is hashed with Argon2id, scrypt or bcrypt, never encrypted or readable. [check: review]
- **AUTH-2** Session cookies are `Secure`, `HttpOnly` and `SameSite`; sessions expire, can be revoked, and get a new id at sign-in and on privilege change. [check: review]
- **AUTH-3** Rate-limit sign-in attempts. [check: review]
- **AUTH-4** Re-confirm identity before account deletion or an email, password or payment change. [check: review]

## Privacy and personal data (PRIV)

- **PRIV-1** Collect only what the feature in use needs. [check: review]
- **PRIV-2** Load non-essential cookies and trackers only after consent; the privacy policy states what is collected and why. [check: review]
- **PRIV-3** No personal data in logs, analytics, crash reports or URLs, query strings included. [check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account and its personal data in the product. [check: review]
- **PRIV-5** Encrypt personal data at rest and reach it only through the server's authorized paths, never world-readable buckets or public URLs. [check: review]

## Accessibility (ACC)

- **ACC-1** Text contrast is at least 4.5:1 (3:1 for large text). [check: review]
- **ACC-2** Click and tap targets are at least 24×24 pixels; primary actions are larger. [check: review]
- **ACC-3** Every interactive element works by keyboard alone and shows a visible focus indicator. [check: review]
- **ACC-4** Interactive elements use semantic HTML or correct ARIA roles with announceable labels; meaningful images have text alternatives. [check: review]
- **ACC-5** Text resizes to 200% without losing meaning. [check: scan:fixed-text-size]
- **ACC-6** Colour is never the only signal; pair it with text, shape or an icon. [check: review]

## User-generated content (UGC), when users see each other's posts

- **UGC-1** Users can report content and block users; sanitize posted content before display (see SEC-3). [check: review]
- **UGC-2** Check uploads' type and size before processing or storing them; never serve them back as executable. [check: review]

## Architecture (A)

- **A-1** Pages and components display, presentation logic prepares display state, only services hold business rules, repositories access data; no business rules in components or route handlers, and the UI never touches storage. [check: scan:layer-import, review]
- **A-2** Dependencies go one way with no cycles; features depend on domain abstractions, never on each other or concrete data code. [check: scan:import-matrix]
- **A-3** One job per module or component; split rather than add a second. Size warnings are hints, not failures. [check: advisory:type-size, review]
- **A-4** Add an interface only for a second implementation, a test fake or a module boundary. [check: review]
- **A-5** Use the framework's standard routing, state and data fetching, never a home-made framework. [check: scan:native-pattern]
- **A-6** Names use standard terms and never claim a role the code does not play (a page or route is navigable, a component is reusable presentation, a repository accesses data). [check: review]

## Coding (C)

- **C-1** Write TypeScript in strict mode; `any` fails review wherever a real type fits. [check: tsc:strict]
- **C-2** Follow the framework's component and state conventions (React: function components, hooks, Rules of Hooks); never mutate state in place. [check: eslint, review]
- **C-3** Await or handle every promise; a rejection always becomes a handled error. [check: eslint:@typescript-eslint/no-floating-promises]
- **C-4** Merge only with zero new TypeScript errors and clean ESLint and Prettier runs. [check: eslint, prettier, tool:warnings-as-errors]
- **C-5** Never hardcode outside facts (branch, path, URL, port, tier, external names or limits); get them from their owner or their one configured place, through one shared function. [check: scan:env-literal]

## Engineering quality (ENG)

- **ENG-1** Keep state that changes on screen or outlives a call in the framework's state system (component state or a subscribed store), never module variables the UI polls; values used once stay plain. [check: review]
- **ENG-2** Pages adapt to window size with fluid layout (flexbox, grid, relative units, media queries); no fixed page dimensions or horizontal page scroll at common widths. [check: advisory:fixed-screen-size, review]
- **ENG-3** Never block the main thread: waits are async, heavy work moves to the server or a worker, no busy-waiting. [check: scan:blocking-call]
- **ENG-4** Every worker, subscription, interval and listener is cleaned up on unmount, navigation or cancel; server child processes end with their parent. [check: review]
- **ENG-5** Bad input yields a typed error that is shown or reported, never an unhandled exception; the server validates on its own. [check: review]
- **ENG-6** Keep secrets in the deployment platform's secret store, never in plaintext files, source control, client code or logs. [check: scan:secret-literal, review]

<!-- shared-section: shared/tests.md -->
## Tests (TEST)

- **TEST-1** Every acceptance criterion has an automated test that names it. [check: scan:test-criterion-tag]
- **TEST-2** Merge-gating tests fake every outside service; live tests never block a merge. [check: scan:hermetic-test]
- **TEST-3** A test fails when its behaviour breaks; assertions any code passes are not coverage. [check: review]
- **TEST-4** Fixtures match real data's size and mess (overflowing lists, truncating names), and fakes return real failures (403, 404, empty, unreachable, slow). [check: review]
- **TEST-5** Every screen showing project data has a stress test past its limits: huge, empty and boundary inputs, slow and missing responses. [check: review]
- **TEST-6** Test each result an outside call can return (answer, refusal, timeout, empty, wrong shape), checking what the person sees and can do next. [check: review]
- **TEST-7** A flow is done only when its builder has used it in the built product (window, settings, navigation, relaunch), saving screen captures and reading stored data back after each action. [check: process, review]
<!-- end shared-section -->

<!-- shared-section: shared/documentation-javascript.md -->
## Documentation (DOC)

- **DOC-1** Every exported type and function has a doc comment, with non-obvious parameters and return value. [check: scan:doc-comments]
- **DOC-2** A doc comment that disagrees with the code is a code defect. [check: review]
<!-- end shared-section -->

---

## Sources

DRY, L and DES are Coast Standards rules; the rest are original statements drawn from OWASP, WCAG 2.2, PCI DSS, TypeScript, React, ESLint and Prettier ([links](https://github.com/Up-Coast/coast-standards/blob/main/rules/README.md#sources)).
