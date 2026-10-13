<!-- coast-standards-release: 1.12.1 -->
# Project rules

Your project's rules: edit, delete or add any; reviewers check every change against this file. Each rule ends with what checks it: `review` a reviewer, `scan:` the scanner refuses it, `ratchet:` a count that may only fall, `advisory:` reported only, `tool:`, `tsc`, `eslint` or `prettier` the pre-push hook, `process` the pipeline or a person. Write every rule so a reviewer can answer yes or no. The app ships to both stores, so both stores' policies apply wherever a rule names them.

## Keep it DRY (DRY)

DRY comes before every other rule: each piece of knowledge lives in one place.

- **DRY-1** Reuse an existing component or combination before creating one, and state why none fit; a near-duplicate fails review. [check: review]
- **DRY-2** Every colour, font, size, weight and spacing is a token in the one theme file, `theme.ts`; no second theme file, no styling literal in a feature file. [check: scan:styling-literal, ratchet:spacing-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale, `locales/<lang>/…`; reuse a key before adding a near-duplicate. [check: scan:one-catalog-per-locale]
- **DRY-4** Error messages live in the catalog; never assemble error text where it is thrown or shown. [check: scan:ui-string-literal]
- **DRY-5** Shared behaviour (routing, gestures, animations, formatting, validation, error and after-save paths) lives in one place; one module decides where every screen, overlay and action goes next, Back, Close, Cancel and errors included, and no screen names its own destinations or calls the navigator itself. [check: tool:jscpd, review]
- **DRY-6** Compute each derived value (total, score, status, rounding) in one place. [check: tool:jscpd, review]
- **DRY-7** One name per thing everywhere; never add a synonym. [check: review]

## Strings and localization (L)

- **L-1** From the first commit, every user-visible string is a catalog key: labels, errors, empty states, loading text, tooltips, accessibility labels, titles, notifications, units. [check: scan:ui-string-literal]
- **L-2** `locales/<lang>/…` is each locale's only string source; reuse an existing key before adding a near-duplicate. [check: scan:one-catalog-per-locale]
- **L-3** Keys name the meaning, not the English (`vehicle.status.doNotDispatch`, not `do_not_dispatch_text`). [check: scan:english-key]
- **L-4** Never join strings into sentences; use the i18n library's named ICU MessageFormat placeholders, the template itself a catalog entry. [check: scan:ui-string-concat]
- **L-5** Plurals use the i18n library's CLDR plural rules, never `if count == 1`. [check: scan:manual-plural]
- **L-6** Format dates, numbers and currency with `Intl.NumberFormat` and `Intl.DateTimeFormat`, never templates. [check: review]
- **L-7** Layouts fit text 30% longer than English without clipping; test German, pseudo-locale and, in scope, right-to-left. [check: review]
- **L-8** The i18n tooling manages the plumbing; write only the text by hand. [check: review]
- **L-9** Safety-critical and client-owned terms use the glossary file's approved translations word for word; never translate them yourself. [check: review]
- **L-10** Database and API text is localized too: per-locale fields, or codes mapped to catalog keys. [check: review]
- **L-11** Users can see and change the language; it applies at once, is saved (profile, local storage or URL) and never discards typed input. [check: review]
- **L-12** Apply all-caps and letter-spacing at render time (a `textTransform` style), never in stored strings. [check: scan:baked-case]

## Design tokens and components (DES)

- **DES-1** Use the design's exact token by its design name, never a near-match; add a missing token to the theme. [check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** A brand colour or typeface change edits only `theme.ts`. [check: scan:second-theme-file]
- **DES-3** A new component's plan or pull request names the components checked and why none fit; a different reviewer approves it. [check: review]
- **DES-4** Check every UI change against the project's design-system spec, when there is one. [check: review]

## Money and payments (PAY)

- **PAY-1** Store and compute money as decimal-safe types or integer minor units (cents), never JavaScript floating point on fractional amounts. [check: advisory:money-float, review]
- **PAY-2** Store every amount with its currency; convert explicitly before adding or comparing currencies. [check: review]
- **PAY-3** Choose rounding method and step once; compute every total in one place. [check: tool:jscpd, review]
- **PAY-4** Sell digital goods and features through each store's in-app purchase: Apple's on iOS, Google Play billing on Android. [check: review]
- **PAY-5** Card numbers never touch app code or storage; use a certified provider's SDK or the payment sheet. [check: review]

## Security (SEC)

- **SEC-1** All network traffic on both platforms uses HTTPS; the native configuration keeps cleartext disabled. [check: scan:plaintext-http]
- **SEC-2** Validate all outside data (input, responses, deep links, shared files) and parameterize every query. [check: scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography; use the platform's or a well-established library's encryption, hashing and randomness. [check: review]
- **SEC-4** Secrets never appear in source, logs, analytics or error messages, nor in JS code or config the JS can reach; the shipped bundle is readable. [check: scan:secret-literal]
- **SEC-5** User-facing errors never show stack traces, queries or paths. [check: review]
- **SEC-6** The lockfile pins JavaScript dependencies; packages on payments, auth, storage or crypto paths are actively maintained and audited before adoption. [check: review]

<!-- shared-section: shared/accounts-and-sign-in.md -->
## Accounts and sign-in (AUTH)

- **AUTH-1** Use the platform's sign-in or an established identity provider, never a hand-built account store; any stored password is hashed with Argon2id, scrypt or bcrypt. [check: review]
- **AUTH-2** Session tokens expire, can be revoked, and are reissued at sign-in and on privilege change. [check: review]
- **AUTH-3** Rate-limit sign-in attempts. [check: review]
- **AUTH-4** Re-confirm identity before account deletion or an email, password or payment change. [check: review]
<!-- end shared-section -->

## Privacy and personal data (PRIV)

- **PRIV-1** Collect only what the feature in use needs. [check: review]
- **PRIV-2** Declare all collected or shared data in both stores' listings (App Store privacy details, Play Data safety). [check: review]
- **PRIV-3** No personal data in logs, analytics, crash reports or URLs. [check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account and its data in the app. [check: review]
- **PRIV-5** On-device personal data stays in the protected container with data protection on, never world-readable; no sensitive data in plain AsyncStorage. [check: review]

## Accessibility (ACC)

- **ACC-1** Text contrast is at least 4.5:1 (3:1 for large text). [check: review]
- **ACC-2** Touch targets meet each platform's minimum (44×44 points iOS, 48×48dp Android), never under 24×24 pixels. [check: review]
- **ACC-3** Every interactive element has an `accessibilityLabel` and role saying what it does. [check: review]
- **ACC-4** Text follows the system text size (font scaling never off) without truncation that hides meaning. [check: scan:fixed-text-size]
- **ACC-5** Colour is never the only signal; pair it with text, shape or an icon. [check: review]

## User-generated content (UGC), when users see each other's posts

- **UGC-1** Users can report content, block users and filter objectionable material, as both stores require. [check: review]
- **UGC-2** Check uploads' type and size before processing or storing them. [check: review]

## Architecture (A)

- **A-1** Screens display, hooks or view models prepare display state, only services hold business rules, repositories access data; components hold no business rules and the UI never touches storage or the network. [check: scan:layer-import, review]
- **A-2** Dependencies go one way with no cycles; features depend on domain abstractions, never on each other or concrete data code. [check: scan:import-matrix]
- **A-3** One job per module or component; split rather than add a second. Size warnings are hints, not failures. [check: advisory:type-size, review]
- **A-4** Add an interface only for a second implementation, a test fake or a module boundary. [check: review]
- **A-5** Use the ecosystem's standard navigation, state and styling (React Navigation, React state, an established store), never a home-made framework. [check: scan:native-pattern]
- **A-6** Names use standard terms and never claim a role the code does not play (a Screen is navigable, a Component is reusable presentation, a Repository accesses data). [check: review]
- **A-7** Use React Navigation and the platform's native containers and controls for navigation, screen structure, tab bars, modals, search, drawers, headers, lists, progress and pickers; a rebuild from standard parts (own navigator, custom tab bar or header, own modal scheme, drawn progress or pickers) is a substitute and needs a deviation the plan approved. Each UI plan item names the native feature it uses. [check: scan:native-pattern]

## Coding (C)

- **C-1** Use TypeScript in strict mode; `any` fails review wherever a real type can be written. [check: tsc:strict]
- **C-2** Use function components with hooks, keep the Rules of Hooks, and never mutate state in place. [check: eslint:react-hooks/rules-of-hooks, eslint:react-hooks/exhaustive-deps]
- **C-3** Await or explicitly handle every promise so every rejection ends as a handled error. [check: eslint:@typescript-eslint/no-floating-promises]
- **C-4** Merge only with zero new TypeScript errors and clean ESLint and Prettier runs. [check: eslint, prettier, tool:warnings-as-errors]
- **C-5** Never hardcode outside facts (branch, path, URL, port, tier, external names or limits); get them from their owner or their one configured place, through one shared function. [check: scan:env-literal]

## Engineering quality (ENG)

- **ENG-1** Keep state that changes on screen or outlives a call in React state or a subscribed store, never module variables the UI polls; values used once stay plain. [check: review]
- **ENG-2** Screens adapt to rotation and window and screen size on both platforms with flex layout and size APIs; no fixed screen sizes. [check: advisory:fixed-screen-size, review]
- **ENG-3** Never block the JavaScript thread: waits are async, heavy work moves off the UI path, no busy-waiting, nothing blocking runs in a render. [check: scan:blocking-call]
- **ENG-4** Every worker, listener, timer or subscription the app starts ends when its owner unmounts or the task is cancelled. [check: review]
- **ENG-5** Bad input yields a typed error that is reported, never an unhandled exception that kills the app. [check: review]
- **ENG-6** Keep secrets in the Keychain or Keystore through a maintained secure-storage module, never in files, JavaScript or logs. [check: scan:secret-literal, review]

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

DRY, L and DES are Coast Standards rules; the rest are original statements drawn from OWASP, WCAG 2.2, Apple's and Google Play's policies, the React, React Native and TypeScript docs, PCI DSS, ESLint and Prettier ([links](https://github.com/Up-Coast/coast-standards/blob/main/rules/README.md#sources)).
