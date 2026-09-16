<!-- coast-standards-release: 1.6.0 -->
# Project rules

This file is your project's rule set. It starts as a default drawn from widely used engineering and safety guides, listed under Sources at the end.

**It belongs to you.** Edit any rule, delete rules that don't apply to your product, and add your own. Automated reviewers check every code change against the rules in this file, so a rule you add is enforced from then on.

Each rule has an id (used in reviews, tickets and tests), one statement a reviewer can check, and a tag in square brackets. The tag names the guide the rule comes from and, after `check:`, what enforces it: `review` is a reviewer, `process` is a person or the pipeline, and any other entry names an automated check.

Write new rules the same way. A reviewer must be able to answer "does this change break the rule: yes or no?"

A React Native app ships to both app stores, so both stores' policies apply wherever a rule names them.

## Keep it DRY (DRY) — the rule above every other rule

Each piece of knowledge is defined in one place, and all other code uses it from there.

- **DRY-1** Design components are created once and reused. Before creating a view, component or helper, check for an existing one, or a combination of existing ones, that does the job. A near-duplicate of an existing component fails review. Every new component states why no existing one fit. [Coast standard; check: review]
- **DRY-2** All styling lives in one theme file: `theme.ts`, the tokens file. Every colour, font, size, weight and spacing value is a token in that file. Never create a second theme file, and never write a styling literal in a feature file. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale (`locales/<lang>/…`). Add new strings only there, and reuse an existing key before adding a near-duplicate. [Coast standard; check: scan:one-catalog-per-locale]
- **DRY-4** Error messages are defined in one place, like other strings. Never assemble error text where the error is thrown or shown. [Coast standard; check: scan:ui-string-literal]
- **DRY-5** Shared behaviour, such as gestures, animations, formatting and validation, is defined in one place and called from there. Never re-implement it locally. [Coast standard; check: tool:jscpd, review]
- **DRY-6** Every derived value (a total, a score, a status, a rounding) is computed in one place and reused. Never recompute it slightly differently somewhere else. [Coast standard; check: tool:jscpd, review]
- **DRY-7** Use one name for each thing, everywhere. Choose the vocabulary once, and never introduce a synonym for something that already has a name. [Coast standard; check: review]

## Strings and localization (L)

Build the product ready for translation from the first commit, even if no second language is planned. Moving strings out of code later is expensive; doing it from the start costs nothing.

- **L-1** No hardcoded user-facing text anywhere. Every string a user can see lives in the string catalog under a named key: labels, error messages, empty states, loading text, tooltips, accessibility labels, titles, notification text and units. A check fails the build on any bare user-facing string in view code. [Coast standard; check: scan:ui-string-literal]
- **L-2** Each locale has one catalog (`locales/<lang>/…`), and it is the only source of strings. Add strings only there. If an existing key already holds the text you need, use that key instead of adding a near-duplicate. [Coast standard; check: scan:one-catalog-per-locale]
- **L-3** Keys describe meaning, not English wording: `vehicle.status.doNotDispatch`, not `do_not_dispatch_text`. This lets a translation differ from the English phrasing. [Coast standard; check: scan:english-key]
- **L-4** Never build sentences by joining strings. Text that contains values uses the i18n library's interpolation with named placeholders (ICU MessageFormat), because word order differs between languages. The template with its placeholders is itself a catalog entry. [Coast standard; check: scan:ui-string-concat]
- **L-5** Plurals use the platform's plural system (the i18n library's plural rules, with CLDR categories), never an `if count == 1` in code. [Coast standard; check: scan:manual-plural]
- **L-6** Format dates, numbers and currency with locale-aware formatters (`Intl.NumberFormat` / `Intl.DateTimeFormat`), never with string templates. [Coast standard; check: review]
- **L-7** Layouts handle text that is about 30% longer: no fixed-width text container that clips. Test with a long-text locale (German), with pseudo-localization and, when in scope, with right-to-left. [Coast standard; check: review]
- **L-8** Localization plumbing is generated and managed by tooling (the i18n tooling), never written by hand. People write the text; tooling handles the plumbing. [Coast standard; check: review]
- **L-9** Domain terms use approved translations. Safety-critical or client-owned terms (status tiers, legal words) have approved translations that are used word for word and listed in a glossary file for the project. An agent never makes up its own translation of them. [Coast standard; check: review]
- **L-10** Text that reaches the UI from a database or an API (descriptions, reference data) must be localized too. Either the source provides a field per locale, or the UI maps stable codes to catalog keys. Never assume text from the backend is exempt. [Coast standard; check: review]
- **L-11** Users can see and change the language, the change applies instantly, and the choice persists. Switching language never discards anything the user typed. Store the choice in the profile, local storage or the URL, as the product requires. [Coast standard; check: review]
- **L-12** Apply all-caps and letter-spacing when rendering (a `textTransform` style), never in the stored string. Casing rules differ between languages, and some scripts have no case at all. [Coast standard; check: scan:baked-case]

## Design tokens and components (DES)

How design values and components get into the code.

- **DES-1** Every visual value uses the design's exact token, referenced by its token name. Never inline a near-match. If the design needs a value that has no token, add a token to the theme; don't write the value where it is used. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** Changing the brand colour or typeface is an edit to one file. Nothing outside the theme file (`theme.ts`, the tokens file) knows a colour, font or spacing value. [Coast standard; check: scan:second-theme-file]
- **DES-3** Justify each new component in writing. The plan or pull request names the existing components that were checked and says why none fit. Building a component and approving it are separate reviews. [Coast standard; check: review]
- **DES-4** If the project has a design-system spec, check every UI change against it. No hardcoded value bypasses the tokens. If a pattern needs a token that doesn't exist, add the token instead of inlining a value. [Coast standard; check: review]

## Money and payments (PAY)

- **PAY-1** Store and calculate money with decimal-safe types or whole minor units (such as cents). Never use JavaScript floating-point arithmetic on fractional amounts, which cannot represent cents exactly. [Industry-wide practice; see Sources; check: advisory:money-float, review]
- **PAY-2** Every stored money amount includes its currency. Never add or compare amounts in different currencies without an explicit conversion step. [Industry-wide practice; check: review]
- **PAY-3** Decide rounding once: which method, and at which step. Compute every total in one place and reuse it; never recompute it slightly differently somewhere else. [Industry-wide practice; check: tool:jscpd, review]
- **PAY-4** Digital goods and features sold inside the app use each store's in-app purchase system: Apple's on iOS, Google Play billing on Android. [Apple App Review Guidelines §3.1; Google Play Payments policy; check: review]
- **PAY-5** Raw card numbers never touch the app's own code or storage. Collect payments through a certified payment provider's SDK or the platform's payment sheet. [PCI DSS scope rules; OWASP; check: review]

## Security (SEC)

- **SEC-1** All network traffic on both platforms uses encrypted connections (HTTPS/TLS). Cleartext traffic stays disabled in the native configuration. [OWASP MASVS-NETWORK; check: scan:plaintext-http]
- **SEC-2** Validate all data from outside the app before using it: user input, network responses, deep links and shared files. Database queries use parameters and are never built from strings. [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization; check: scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography. Encryption, hashing and random-number generation use the platform's or a well-established library's implementations. [OWASP MASVS-CRYPTO; check: review]
- **SEC-4** Secrets (API keys, tokens, credentials) never appear in source code, logs, analytics or error messages. Anyone can read the JavaScript bundle of a shipped app, so never embed a secret in JS code or in config the JS can reach. [OWASP MASVS-STORAGE; React Native security guidance; check: scan:secret-literal]
- **SEC-5** Error messages shown to users never reveal internals such as stack traces, query text or file paths. [OWASP Cheat Sheet: Error Handling; check: review]
- **SEC-6** The lockfile pins JavaScript dependencies. Packages on security-critical paths (payments, auth, storage, crypto) must be actively maintained, and are audited before they are adopted. [OWASP Cheat Sheet: NPM Security; supply-chain practice; check: review]

<!-- shared-section: shared/accounts-and-sign-in.md -->
## Accounts and sign-in (AUTH)

- **AUTH-1** Sign-in uses the platform's sign-in system or an established identity provider, never a hand-built account store. If passwords must be stored, hash them with a current memory-hard algorithm (Argon2id, scrypt or bcrypt). Never encrypt them or store them readable. [OWASP Cheat Sheets: Authentication, Password Storage; check: review]
- **AUTH-2** Session tokens expire and can be revoked. A new token is issued at sign-in and whenever the user's privileges change. [OWASP Cheat Sheet: Session Management; check: review]
- **AUTH-3** Sign-in attempts are rate-limited, so accounts can't be brute-forced. [OWASP ASVS; check: review]
- **AUTH-4** Sensitive actions ask the user to confirm their identity again first. These include deleting the account and changing the email, password or payment details. [OWASP ASVS; check: review]
<!-- end shared-section -->

## Privacy and personal data (PRIV)

- **PRIV-1** The app collects only the data that the feature the user is using actually needs. [Apple App Review Guidelines §5.1; Google Play User Data policy; check: review]
- **PRIV-2** Declare every kind of data the app collects or shares in both stores' privacy listings (App Store privacy details and Play Data safety). No undeclared collection. [Apple App Review Guidelines §5.1; Google Play Data safety requirements; check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash reports or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging; check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account, and the personal data behind it, from inside the app. [Apple App Review Guidelines §5.1.1(v); Google Play Account deletion policy; check: review]
- **PRIV-5** Personal data stored on the device lives in the app's protected container, with platform data protection applied. Never store it in world-readable locations, and never store sensitive data in plain AsyncStorage. [OWASP MASVS-STORAGE; React Native security guidance; check: review]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its background (3:1 for large text). [WCAG 2.2 — 1.4.3; check: review]
- **ACC-2** Touch targets meet each platform's minimum (44×44 points on iOS, 48×48dp on Android) and are never smaller than 24×24 pixels. [Apple HIG; Material Design accessibility; WCAG 2.2 — 2.5.8; check: review]
- **ACC-3** Every interactive element has an accessibility label and role (`accessibilityLabel`, role), so screen readers can say what it does. [WCAG 2.2 — 4.1.2; React Native accessibility docs; check: review]
- **ACC-4** Text follows the system text-size setting (font scaling is never turned off), and larger text never gets cut off in a way that loses meaning. [WCAG 2.2 — 1.4.4; React Native accessibility docs; check: scan:fixed-text-size]
- **ACC-5** Color is never the only signal. Errors, success and selection are also shown by text, shape or icon. [WCAG 2.2 — 1.4.1; check: review]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** Users can report content, block other users and filter objectionable material. [Apple App Review Guidelines §1.2; Google Play UGC policy; check: review]
- **UGC-2** Check uploaded content for the expected type and size before processing or storing it. [OWASP Cheat Sheet: File Upload; check: review]

## Architecture (A)

- **A-1** Code lives in its layer. Screens display. Presentation logic (hooks or view models) prepares what screens show. Services hold the business rules. Repositories access data. Business rules never sit in components, and the UI never talks to storage or the network directly. [Industry-standard separation of concerns: Service layer, Repository pattern; React docs; check: scan:layer-import, review]
- **A-2** Module dependencies go one way, with no cycles. Features depend on shared domain abstractions, never on each other or on concrete data code. [SOLID dependency-inversion principle; acyclic-dependencies principle; check: scan:import-matrix]
- **A-3** Each module or component has one job. If a change would give it a second job, split it instead. Automated size warnings are hints for a reviewer, never automatic failures. [SOLID single-responsibility principle; check: advisory:type-size, review]
- **A-4** No speculative abstraction. Add an interface only where something real takes its place: a second implementation or a test fake. A boundary between two modules always counts. [YAGNI — industry practice; check: review]
- **A-5** Meet standard needs (navigation, state, styling) with the ecosystem's standard mechanism, such as React Navigation, React state or an established store. Never build a home-made framework that fights the platform. [React Native documentation; check: scan:native-pattern]
- **A-6** A name says what a thing is, in industry-standard terms: a Screen is a full screen you can navigate to, a Component is reusable presentation, a Repository accesses data. A name never claims a different role than the code performs. [Industry-standard pattern names; check: review]
- **A-7** If the ecosystem provides a feature, use it. For any job the ecosystem already handles, the standard native mechanism (React Navigation, the platform's native containers and controls) is required: navigation, screen structure, tab bars, modals, search, drawers, headers, lists, progress indicators and pickers. Building an equivalent out of standard parts is still a substitute; "every piece is a standard component" is no defence. Examples (not a complete list): a hand-rolled navigator, a custom tab bar where the navigator's tabs would do, a hand-built header instead of the navigator's, a custom modal scheme that fights the platform, hand-drawn progress or pickers. A workaround or substitute is allowed only where the plan explicitly approved it as a deliberate exception, never silently or as a quick fix. Each UI item in the plan names the native feature it uses, so any substitute is visible when the plan is approved. A pull request that adds a code pattern from the native-patterns checker's list of workarounds and substitutes fails, unless the plan's approved list of native deviations covers it. The React Native pattern list starts from what reviewers have caught and grows over time. [React Native documentation; check: scan:native-pattern]

## Coding (C)

- **C-1** The codebase is TypeScript with strict mode on. `any` fails review wherever a real type can be written. [TypeScript documentation; check: tsc:strict]
- **C-2** Components are function components that use hooks, and the Rules of Hooks hold everywhere. Never change state in place; updates create new values. [React documentation: Rules of Hooks; check: eslint:react-hooks/rules-of-hooks, eslint:react-hooks/exhaustive-deps]
- **C-3** Every promise is awaited or explicitly handled; no floating promises. A rejected promise always ends up as a handled error. [TypeScript/ESLint practice; check: eslint:@typescript-eslint/no-floating-promises]
- **C-4** A change merges only with zero new TypeScript errors and a clean run of the project's ESLint and Prettier configuration. [ESLint / Prettier; check: eslint, prettier, tool:warnings-as-errors]
- **C-5** Don't hardcode facts about the world outside the code. These include a repository's default branch, file paths, URLs and ports, plan or platform tiers, and an external system's names or limits. Ask the system that owns each fact, or read it from its one configured location, through one shared function that every caller uses. A hardcoded assumption about external state (a branch named "main", a fixed path or URL) fails review wherever the real answer can be looked up. [Twelve-Factor App, config; check: scan:env-literal]

## Engineering quality (ENG)

- **ENG-1** State is reactive. Any state that can change while it is on screen, or that lives longer than one function call, lives in React state (component state, or a store the UI subscribes to), so the UI re-renders from it. Never use module-level variables that the UI polls or refreshes by hand. One-off values stay plain; don't wrap constants in state. [Platform best practice — React; check: review]
- **ENG-2** Layouts are responsive. Screens adapt to rotation and to window and screen size changes on both platforms, using flex layout and the platform's size APIs. No fixed screen dimensions. [Platform best practice — React Native; check: advisory:fixed-screen-size, review]
- **ENG-3** Never block the JavaScript thread. Long waits (network calls, heavy computation, timers) are asynchronous, and heavy work moves off the UI path. No busy-waiting, and nothing that blocks can be called from a render. [Platform best practice — React Native performance docs; check: scan:blocking-call]
- **ENG-4** Background work ends with its owner. Any worker, listener or subscription the app starts is tied to its owner's lifetime, so unmounting or cancelling cleans it up. No leaked timers, listeners or native processes. [Platform best practice — React; check: review]
- **ENG-5** Bad input never crashes the app. Invalid input or unexpected data produces a typed error that is reported, never an unhandled exception that kills the app. [Platform best practice; OWASP Cheat Sheet: Error Handling; check: review]
- **ENG-6** Secrets live in the platform's secure store (Keychain on iOS, Keystore on Android), reached through a maintained secure-storage module. Never keep them in plain-text files, JavaScript code or logs. [OWASP MASVS-STORAGE; React Native security guidance; check: scan:secret-literal, review]

<!-- shared-section: shared/tests.md -->
## Tests (TEST)

- **TEST-1** Every acceptance criterion has at least one automated test. Each test states which acceptance criterion it verifies. [Project rule; check: scan:test-criterion-tag]
- **TEST-2** Tests that must pass before a merge run without live external services; external dependencies are faked locally. Tests against live services run separately and never block a merge. [Project rule; Google Testing Blog: hermetic testing; check: scan:hermetic-test]
- **TEST-3** A test proves behaviour: it fails when the behaviour it names is broken. Assertions so weak that any implementation passes don't count as coverage. [Project rule; check: review]
- **TEST-4** Test data looks like real data. Fixtures match the size, shape and messiness of the real thing: lists long enough to overflow their container, names long enough to be truncated, and documents written in the industry's words, not the product's. Fakes of outside services can return that service's real failures (403, 404, empty, unreachable, slow), not just success and one tidy error. A fixture built for convenience only tests the fixture. [Project rule; check: review]
- **TEST-5** Stress-test on purpose, as a separate practice. Deliberately go past what is expected: far more items than anyone would have, values at and beyond the stated limits, empty and huge inputs, slow and missing responses. At minimum, every screen that shows project data has one such test. [Project rule; check: review]
- **TEST-6** Every failure path has a test. A feature that calls a model, a network service or a file ships with one test for each result the real thing can return: the answer, a refusal, a timeout, an empty reply, and an answer in the wrong shape. Each test checks two things: what the person sees, in the product's own words, and what they can do next. A flow tested only against a fake that always answers has not been tested. [Project rule; check: review]
- **TEST-7** Done means used. A screen or flow task is finished only after its builder uses it in the built product as a person would: through the screens, buttons and links, not the code. The builder records what they saw: screen captures saved to disk, and the stored data read back after each action. A screenshot of the newly built pane is not enough; the pane's window, title, settings, navigation and relaunch are part of the flow. [Project rule; check: process, review]
<!-- end shared-section -->

<!-- shared-section: shared/documentation-javascript.md -->
## Documentation (DOC)

- **DOC-1** Every exported type and function has a doc comment that says what it does, including its parameters and return value when they aren't obvious. The generated API reference is built from these comments. [Project rule; check: scan:doc-comments]
- **DOC-2** A doc comment matches what the code actually does. A wrong doc comment is a code problem, not a wording problem. [Project rule; check: review]
<!-- end shared-section -->

---

## Sources

- **Coast Standards** — the DRY, strings and design-token rules (DRY, L, DES) are this repository's own rules, applied to every project that adopts it.

The other rules are written in this project's own words. These are the guides they draw on, for reference and further reading:

- **OWASP Mobile Application Security Verification Standard (MASVS) 2.1** — <https://mas.owasp.org/MASVS/> (CC BY-SA 4.0)
- **OWASP Application Security Verification Standard (ASVS) 5.0** — <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** (including NPM Security) — <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **W3C Web Content Accessibility Guidelines (WCAG) 2.2** — <https://www.w3.org/TR/WCAG22/> (W3C document license; also ISO/IEC 40500)
- **React Native security and accessibility documentation** — <https://reactnative.dev/docs/security> (MIT-licensed docs)
- **React documentation** (including Rules of Hooks) — <https://react.dev/> (CC BY 4.0; referenced only, no text reproduced)
- **TypeScript documentation** — <https://www.typescriptlang.org/docs/> (referenced only)
- **ESLint / typescript-eslint / Prettier** (standard rule sets, used as the automated checkers some rules name) — <https://eslint.org/>, <https://typescript-eslint.io/>, <https://prettier.io/> (MIT)
- **Apple App Review Guidelines** — <https://developer.apple.com/app-store/review/guidelines/> (proprietary; referenced only, no text reproduced)
- **Google Play Developer Program policies** — <https://play.google/developer-content-policy/> (proprietary; referenced only, no text reproduced)

No text from these guides is copied here. Every rule is an original plain-language statement that cites its source, so you can edit or replace this file with no license obligations.
