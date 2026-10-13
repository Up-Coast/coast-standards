<!-- coast-standards-release: 1.12.1 -->
# Project rules

Your project's rules: edit, delete or add any; reviewers check every change against this file. Each rule ends with what checks it: `review` a reviewer, `scan:` the scanner refuses it, `ratchet:` a count that may only fall, `advisory:` reported only, `tool:`, `ktlint`, `detekt` or `androidlint` the pre-push hook, `process` the pipeline or a person. Write every rule so a reviewer can answer yes or no.

## Keep it DRY (DRY)

DRY comes before every other rule: each piece of knowledge lives in one place.

- **DRY-1** Reuse an existing component or combination before creating one, and state why none fit; a near-duplicate fails review. [check: review]
- **DRY-2** Every colour, font, size, weight and spacing is a token in the one theme file, `Theme.kt` (the Material theme and its tokens); no second theme file, no styling literal in a feature file. [check: scan:styling-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale, `res/values-<locale>/strings.xml`; reuse a key before adding a near-duplicate. [check: scan:one-catalog-per-locale]
- **DRY-4** Error messages live in the catalog; never assemble error text where it is thrown or shown. [check: scan:ui-string-literal]
- **DRY-5** Shared behaviour (routing, gestures, animations, formatting, validation, error and after-save paths) lives in one place; one module decides where every screen, overlay and action goes next, Back, Close, Cancel and errors included, and no screen names its own destinations or calls the navigation API itself. [check: tool:jscpd, review]
- **DRY-6** Compute each derived value (total, score, status, rounding) in one place. [check: tool:jscpd, review]
- **DRY-7** One name per thing everywhere; never add a synonym. [check: review]

## Strings and localization (L)

- **L-1** From the first commit, every user-visible string is a catalog key: labels, errors, empty states, loading text, tooltips, accessibility labels, titles, notifications, units. [check: scan:ui-string-literal]
- **L-2** `res/values-<locale>/strings.xml` is each locale's only string source; reuse an existing key before adding a near-duplicate. [check: scan:one-catalog-per-locale]
- **L-3** Keys name the meaning, not the English (`vehicle.status.doNotDispatch`, not `do_not_dispatch_text`). [check: scan:english-key]
- **L-4** Never join strings into sentences; use `getString(R.string.key, …)` with format arguments, the template itself a catalog entry. [check: scan:ui-string-concat]
- **L-5** Plurals use `<plurals>` resources with CLDR quantities, never `if count == 1`. [check: scan:manual-plural]
- **L-6** Format dates, numbers and currency with `NumberFormat` and `DateTimeFormatter` in the user's locale, never templates. [check: review]
- **L-7** Layouts fit text 30% longer than English without clipping; test German, pseudo-locale and, in scope, right-to-left. [check: review]
- **L-8** Android resource tooling manages the plumbing; write only the text by hand. [check: review]
- **L-9** Safety-critical and client-owned terms use the glossary file's approved translations word for word; never translate them yourself. [check: review]
- **L-10** Database and API text is localized too: per-locale fields, or codes mapped to catalog keys. [check: review]
- **L-11** Users can see and change the language; it applies at once, is saved (profile, local storage or URL) and never discards typed input. [check: review]
- **L-12** Apply all-caps and letter-spacing at render time (a `TextStyle` or `textAllCaps`), never in stored strings. [check: scan:baked-case]

## Design tokens and components (DES)

- **DES-1** Use the design's exact token by its design name, never a near-match; add a missing token to the theme. [check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** A brand colour or typeface change edits only `Theme.kt` and its Material tokens. [check: scan:second-theme-file]
- **DES-3** A new component's plan or pull request names the components checked and why none fit; a different reviewer approves it. [check: review]
- **DES-4** Check every UI change against the project's design-system spec, when there is one. [check: review]

## Money and payments (PAY)

- **PAY-1** Store and compute money as decimal or integer types, never `Float` or `Double`. [check: advisory:money-float, review]
- **PAY-2** Store every amount with its currency; convert explicitly before adding or comparing currencies. [check: review]
- **PAY-3** Choose rounding method and step once; compute every total in one place. [check: tool:jscpd, review]
- **PAY-4** Sell digital goods and features through Google Play billing. [check: review]
- **PAY-5** Card numbers never touch app code or storage; use a certified provider's SDK or the payment sheet. [check: review]

## Security (SEC)

- **SEC-1** All network traffic uses HTTPS; the network security configuration disables cleartext. [check: scan:plaintext-http]
- **SEC-2** Validate all outside data (input, responses, deep links, shared files, intents) and parameterize every query. [check: scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography; use platform or standard-library encryption, hashing and randomness. [check: review]
- **SEC-4** Secrets never appear in source, logs, analytics or error messages. [check: scan:secret-literal]
- **SEC-5** User-facing errors never show stack traces, queries or paths. [check: review]
- **SEC-6** Export an activity, service, receiver or provider only when another app needs it; every exported component validates its input. [check: scan:exported-component]

<!-- shared-section: shared/accounts-and-sign-in.md -->
## Accounts and sign-in (AUTH)

- **AUTH-1** Use the platform's sign-in or an established identity provider, never a hand-built account store; any stored password is hashed with Argon2id, scrypt or bcrypt. [check: review]
- **AUTH-2** Session tokens expire, can be revoked, and are reissued at sign-in and on privilege change. [check: review]
- **AUTH-3** Rate-limit sign-in attempts. [check: review]
- **AUTH-4** Re-confirm identity before account deletion or an email, password or payment change. [check: review]
<!-- end shared-section -->

## Privacy and personal data (PRIV)

- **PRIV-1** Collect only what the feature in use needs. [check: review]
- **PRIV-2** Declare all collected or shared data in the Play Console Data safety section. [check: review]
- **PRIV-3** No personal data in logs, analytics, crash reports or URLs. [check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account and its data in the app, and on the web path Play requires. [check: review]
- **PRIV-5** On-device personal data stays in internal storage, never world-readable or external; encrypt sensitive data with Keystore-backed keys. [check: review]

## Accessibility (ACC)

- **ACC-1** Text contrast is at least 4.5:1 (3:1 for large text). [check: review]
- **ACC-2** Touch targets are at least 48×48dp, never under 24×24 pixels. [check: review]
- **ACC-3** Every interactive element has a content description TalkBack can read. [check: review]
- **ACC-4** Text uses `sp` and follows the system font size without truncation that hides meaning. [check: scan:fixed-text-size]
- **ACC-5** Colour is never the only signal; pair it with text, shape or an icon. [check: review]

## User-generated content (UGC), when users see each other's posts

- **UGC-1** Users can report content, block other users and filter objectionable material. [check: review]
- **UGC-2** Check uploads' type and size before processing or storing them. [check: review]

## Architecture (A)

- **A-1** Screens display, view models prepare display state, only services hold business rules, repositories access data; the UI never touches storage. [check: scan:layer-import, review]
- **A-2** Dependencies go one way with no cycles; features depend on domain abstractions, never on each other or concrete data code. [check: scan:import-matrix]
- **A-3** One job per type or module; split rather than add a second. Size warnings are hints, not failures. [check: advisory:type-size, review]
- **A-4** Add an interface only for a second implementation, a test fake or a module boundary. [check: review]
- **A-5** Use the platform's standard navigation, state and dependency wiring, never a home-made framework. [check: scan:native-pattern]
- **A-6** Names use standard terms and never claim a role the code does not play (a ViewModel prepares display state, a Repository accesses data, a Screen is navigable). [check: review]
- **A-7** Use the platform feature for navigation, surface and window structure, app and bottom bars, dialogs and sheets, search, drawers and rails, menus, lists, progress and pickers; a rebuild from native parts (own navigation, custom bottom bar, own search field, custom drawer, scrim as dialog, drawn progress or pickers, focus override) is a substitute and needs a deviation the plan approved. Each UI plan item names the native feature it uses. [check: scan:native-pattern]

## Coding (C)

- **C-1** Follow the Kotlin coding conventions; no abbreviations. [check: review]
- **C-2** Prefer `val` and data classes; shared mutable state has one owner, is exposed through observation and is never reached unprotected from several threads. [check: review]
- **C-3** No `!!` unless the code itself proves the value non-null; use safe calls or early checks. [check: detekt:UnsafeCallOnNullableType]
- **C-4** Merge only with zero new warnings and clean ktlint, detekt and Android lint runs. [check: ktlint, detekt, androidlint, tool:warnings-as-errors]
- **C-5** Never hardcode outside facts (branch, path, URL, port, tier, external names or limits); get them from their owner or their one configured place, through one shared function. [check: scan:env-literal]

## Engineering quality (ENG)

- **ENG-1** Publish state that changes on screen or outlives a call through Flow, Compose State or LiveData, never polling; values used once stay plain. [check: review]
- **ENG-2** Screens adapt to rotation, window-size classes and split-screen with standard layout; no fixed screen sizes. [check: advisory:fixed-screen-size, review]
- **ENG-3** Never block a thread: waits use coroutines, nothing sleeps on a held thread, the main thread never calls blocking code. [check: scan:blocking-call]
- **ENG-4** Every process or worker the app starts ends when the app quits or the task is cancelled. [check: review]
- **ENG-5** Bad input yields a typed error that is reported, never a crash; assert only on programmer errors. [check: review]
- **ENG-6** Keep secrets in the Android Keystore, with Keystore-backed encryption for stored material, never in files, source or logs. [check: scan:secret-literal, review]

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

<!-- shared-section: shared/documentation-native.md -->
## Documentation (DOC)

- **DOC-1** Every public type and function has a doc comment, with non-obvious parameters and return value. [check: scan:doc-comments]
- **DOC-2** A doc comment that disagrees with the code is a code defect. [check: review]
<!-- end shared-section -->

---

## Sources

DRY, L and DES are Coast Standards rules; the rest are original statements drawn from OWASP, WCAG 2.2, Google Play policies, Android and Material guidance, the Kotlin conventions, PCI DSS, ktlint and detekt ([links](https://github.com/Up-Coast/coast-standards/blob/main/rules/README.md#sources)).
