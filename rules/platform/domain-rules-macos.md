<!-- coast-standards-release: 1.6.0 -->
# Project rules

These are your project's rules. They are a starting set drawn from widely used engineering and safety guides, listed under Sources at the bottom.

**This file belongs to you.** Edit any rule, delete rules that don't apply to your product, and add your own. Automated reviewers check every code change against exactly the rules in this file, so a rule you add is enforced on every change from then on.

Each rule has:

- an id, used in reviews, tickets and tests;
- one checkable statement;
- a bracket at the end naming the guide it comes from and how it is checked.

| In the bracket | What checks the rule |
|---|---|
| `review` | A reviewer, on every change |
| `scan:<name>` | The rules scanner; a finding refuses the change |
| `ratchet:<name>` | The rules scanner, against a count of existing problems that may only go down |
| `advisory:<name>` | The rules scanner reports it; nothing fails |
| `tool:<name>`, `swiftlint`, `swiftformat` | A tool or linter the pre-push hook runs |
| `process` | The pipeline or a person |

Keep new rules checkable. A reviewer must be able to answer "does this change break the rule?" with yes or no.

<!-- shared-section: shared/apple-dry.md -->
## Keep it DRY (DRY) — the rule above every other rule

Every piece of knowledge lives in exactly one place, and everything else uses that place.

- **DRY-1** Design components are built once and reused. Before creating a view, component or helper, check for an existing one, or a combination of existing ones. A near-duplicate of an existing component fails review. Every new component states why nothing existing fit. [Coast standard; check: review]
- **DRY-2** All styling lives in one theme file (`Theme.swift`). Every colour, font, size, weight and spacing value is a token there. Never create a second theme file, and never write a styling literal in a feature file. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale (`Localizable.xcstrings`). All new strings go there. Reuse an existing key before adding a near-duplicate. [Coast standard; check: scan:one-catalog-per-locale]
- **DRY-4** Error messages live in one place, like other strings. Never assemble error text where the error is thrown or shown. [Coast standard; check: scan:ui-string-literal]
- **DRY-5** Shared behaviour (gestures, animations, formatting, validation) lives in one place and is called from there. Never re-implement it locally. [Coast standard; check: tool:jscpd, review]
- **DRY-6** Every derived value (a total, a score, a status, a rounding) is computed in one place and reused. Never compute it again, slightly differently, somewhere else. [Coast standard; check: tool:jscpd, review]
- **DRY-7** Each thing has one name everywhere. Choose the vocabulary once, and never introduce a synonym for something that already has a name. [Coast standard; check: review]
<!-- end shared-section -->

<!-- shared-section: shared/apple-strings.md -->
## Strings and localization (L)

Build the product localizable from the first commit, even if no second language is planned. Moving strings out of the code later is expensive; doing it from day one costs nothing.

- **L-1** No hardcoded user-facing text anywhere. Every string a user can see lives in the string catalog under a named key: labels, error messages, empty states, loading text, tooltips, accessibility labels, titles, notification text and units. A check fails the build on any bare user-facing literal in view code. [Coast standard; check: scan:ui-string-literal]
- **L-2** Each locale has one catalog (`Localizable.xcstrings`), and it is the only source of strings. All new strings go there. Reuse comes first: if an existing key already has the text you need, use that key instead of adding a near-duplicate. [Coast standard; check: scan:one-catalog-per-locale]
- **L-3** Keys describe meaning, not English wording: `vehicle.status.doNotDispatch`, not `do_not_dispatch_text`. This lets a translation differ from the English phrasing. [Coast standard; check: scan:english-key]
- **L-4** Never build sentences by joining strings. Text that contains values uses `String(localized:)` with `\(…)` placeholders. Word order differs between languages, and the template with its placeholders is itself a catalog entry. [Coast standard; check: scan:ui-string-concat]
- **L-5** Plurals use the platform's plural system, the string catalog's plural variants (CLDR one/other…). Never write `if count == 1` in code. [Coast standard; check: scan:manual-plural]
- **L-6** Dates, numbers and currency are formatted with locale-aware formatters (`FormatStyle`, such as `.formatted(.currency…)` and `Date.FormatStyle`), never with string templates. [Coast standard; check: review]
- **L-7** Layouts handle text about 30% longer than English. No fixed-width text container clips. Test with a long-string locale (German), with pseudo-localization and, when in scope, with right-to-left. [Coast standard; check: review]
- **L-8** Tooling (Xcode String Catalogs) generates and manages the localization plumbing. Write the text by hand; never hand-write the plumbing. [Coast standard; check: review]
- **L-9** Domain terms need approved translations. Safety-critical or client-owned terms (status tiers, legal words) use approved translations, word for word, listed in a per-project glossary file. An agent never translates them on its own. [Coast standard; check: review]
- **L-10** Text that reaches the UI from a database or an API (descriptions, reference data) must be localized too. Either the source provides a field per locale, or the UI maps stable codes to catalog keys. Never assume backend strings are exempt. [Coast standard; check: review]
- **L-11** The user can see and change the language. The change applies instantly and is saved. Switching language never discards anything the user typed. The choice is saved in the profile, local storage or URL, as the product requires. [Coast standard; check: review]
- **L-12** Apply all-caps and letter-spacing when rendering (`.textCase(.uppercase)`), never in the stored string. Casing rules differ by language, and some scripts have no case at all. [Coast standard; check: scan:baked-case]
<!-- end shared-section -->

<!-- shared-section: shared/apple-design-tokens.md -->
## Design tokens and components (DES)

How the design's values and components reach the code.

- **DES-1** Every visual value uses the design's exact token, by the design's token name. Never inline a near-match. If the design needs a value that has no token, add a token to the theme instead of writing the value where it is used. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** Changing the brand colour or typeface is a one-file edit. No code outside the theme file (`Theme.swift`) knows a colour, font or spacing value. [Coast standard; check: scan:second-theme-file]
- **DES-3** A new component is justified in writing. The plan or pull request names the existing components that were checked and says why none fit. The person who builds a component and the person who approves it are different reviewers. [Coast standard; check: review]
- **DES-4** If the project has a design-system spec, every UI change is checked against it. No hardcoded value bypasses the tokens. If a pattern needs a token that doesn't exist, add the token instead of inlining a value. [Coast standard; check: review]
<!-- end shared-section -->

## Money and payments (PAY)

- **PAY-1** Store and calculate money with decimal or whole-number types. Never use binary floating-point types (`Float`, `Double`); they cannot represent cents exactly. [Industry-wide practice; see Sources; check: advisory:money-float, review]
- **PAY-2** Every stored money amount includes its currency. Never add or compare amounts in different currencies without an explicit conversion step. [Industry-wide practice; check: review]
- **PAY-3** Decide rounding once: which method, and at which step. Compute every total in one place and reuse it. Never compute it again, slightly differently, somewhere else. [Industry-wide practice; check: tool:jscpd, review]
- **PAY-4** In the Mac App Store build, digital goods and features sold inside the app use Apple's in-app purchase system. The direct-download build may use its own payment provider. The two builds never mislead the App Store reviewer about what the app sells. [Apple App Review Guidelines §3.1; check: review]
- **PAY-5** Raw card numbers never touch the app's own code or storage. Collect payments through a certified payment provider's SDK or the platform's payment sheet. [PCI DSS scope rules; OWASP; check: review]

<!-- shared-section: shared/apple-security.md -->
## Security (SEC)

- **SEC-1** All network traffic is encrypted (HTTPS/TLS). No plaintext HTTP endpoints. [OWASP ASVS; OWASP MASVS-NETWORK; check: scan:plaintext-http]
- **SEC-2** Validate all data from outside the app before using it: user input, network responses, deep links and shared files. Database queries are parameterized, never built from strings. [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization; check: scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography. Encryption, hashing and random-number generation use the platform's or the standard library's implementations. [OWASP MASVS-CRYPTO; check: review]
- **SEC-4** Secrets (API keys, tokens, credentials) never appear in source code, logs, analytics or error messages. [OWASP ASVS; MASVS-STORAGE; check: scan:secret-literal]
- **SEC-5** Error messages shown to users never expose internals such as stack traces, query text or file paths. [OWASP Cheat Sheet: Error Handling; check: review]
<!-- end shared-section -->

<!-- shared-section: shared/accounts-and-sign-in.md -->
## Accounts and sign-in (AUTH)

- **AUTH-1** Sign-in uses the platform's sign-in system or an established identity provider, never a hand-built account store. If passwords must be stored, hash them with a current memory-hard algorithm (Argon2id, scrypt or bcrypt). Never encrypt them or store them readable. [OWASP Cheat Sheets: Authentication, Password Storage; check: review]
- **AUTH-2** Session tokens expire and can be revoked. A new token is issued at sign-in and whenever the user's privileges change. [OWASP Cheat Sheet: Session Management; check: review]
- **AUTH-3** Sign-in attempts are rate-limited, so accounts can't be brute-forced. [OWASP ASVS; check: review]
- **AUTH-4** Sensitive actions ask the user to confirm their identity again first. These include deleting the account and changing the email, password or payment details. [OWASP ASVS; check: review]
<!-- end shared-section -->

<!-- shared-section: shared/apple-privacy.md -->
## Privacy and personal data (PRIV)

- **PRIV-1** The app collects only the data that the feature in use actually needs. [Apple App Review Guidelines §5.1; GDPR data-minimization principle; check: review]
- **PRIV-2** Every kind of data the app collects or shares is declared in the store's privacy listing. No undeclared collection. [Apple App Review Guidelines §5.1; check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash reports or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging; check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account, and the personal data linked to it, from inside the app. [Apple App Review Guidelines §5.1.1(v); check: review]
- **PRIV-5** Personal data stored on the device stays in the app's protected container, with the platform's data protection applied. Never store it where other apps or users can read it. [OWASP MASVS-STORAGE; check: review]
<!-- end shared-section -->

## macOS platform behavior (MAC)

- **MAC-1** The app runs in Apple's App Sandbox in both builds: Mac App Store and direct download. The Mac App Store requires it, and sandboxing the direct-download build too keeps behaviour the same everywhere. Declare every capability the sandbox needs (file access, network) as an entitlement; never work around the sandbox. [Apple App Sandbox documentation; Mac App Store requirement; check: review]
- **MAC-2** Windows behave like Mac windows. Keep the native title bar and the red, yellow and green window buttons. State restoration works. The app keeps running after its last window closes only if that suits its purpose. [Apple HIG — macOS Windows; check: review]
- **MAC-3** Every user-facing command is in the menu bar, in its standard menu, with the standard keyboard shortcuts (Cmd-W close, Cmd-Q quit, Cmd-, settings). A feature that only works with a mouse or trackpad is incomplete. [Apple HIG — The menu bar; check: review]
- **MAC-4** Settings use a standard Settings scene or window, not a custom modal. [Apple HIG — Settings; check: review]
- **MAC-5** The app supports full keyboard navigation. Wherever text or content is edited, standard editing works: undo, copy and paste, drag and drop. [Apple HIG; WCAG 2.2 — 2.1.1; check: review]
- **MAC-6** Confirming a destructive action takes a deliberate click. The destructive button is never the default button that Return presses. [Project rule, from Apple HIG alert guidance; check: scan:destructive-default-key]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its background (3:1 for large text). [WCAG 2.2 — 1.4.3; check: review]
- **ACC-2** Click targets follow platform guidance and are never smaller than 24×24 pixels. Standard controls at standard sizes meet this. [Apple HIG; WCAG 2.2 — 2.5.8; check: review]
- **ACC-3** Every interactive element has a screen-reader label that says what it does. [WCAG 2.2 — 4.1.2; Apple HIG Accessibility; check: review]
- **ACC-4** Text follows the system text-size setting (Dynamic Type on Apple platforms) without truncation that hides meaning. [Apple HIG; WCAG 2.2 — 1.4.4; check: scan:fixed-text-size]
- **ACC-5** Colour is never the only signal. Errors, success and selection are also shown with text, shape or an icon. [WCAG 2.2 — 1.4.1; check: review]

<!-- shared-section: shared/apple-user-generated-content.md -->
## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** Users can report content, block other users, and filter objectionable material. [Apple App Review Guidelines §1.2; check: review]
- **UGC-2** Uploaded content is checked for the expected type and size before it is processed or stored. [OWASP Cheat Sheet: File Upload; check: review]
<!-- end shared-section -->

<!-- shared-section: shared/apple-architecture.md -->
## Architecture (A)

- **A-1** Code stays in its layer. Screens display. View models prepare what screens show. Services hold the business rules. Repositories access data. Business rules never sit in screens or view models, and the UI never talks to storage directly. [Industry-standard separation of concerns: MVVM, Service layer, Repository pattern; check: scan:layer-import, review]
- **A-2** Module dependencies go one way, with no cycles. Features depend on shared domain abstractions, never on each other or on concrete data code. [SOLID dependency-inversion principle; acyclic-dependencies principle; check: scan:import-matrix]
- **A-3** Each type or module has one job. If a change would give it a second job, split it instead. Automated size warnings are hints for a reviewer, never automatic failures. [SOLID single-responsibility principle; check: advisory:type-size, review]
- **A-4** No speculative abstraction. A protocol or interface exists only where something real replaces it: a second implementation or a test fake. A boundary between two modules always qualifies. [YAGNI — industry practice; check: review]
- **A-5** Standard needs (navigation, state, dependency wiring) use the platform's standard mechanism, not a home-made framework that fights the platform. [Apple platform conventions; check: scan:native-pattern]
- **A-6** A name says what a thing is, using standard industry terms, and never claims a role the code doesn't perform. A ViewModel prepares display state, a Repository accesses data, and a Screen is a full screen the user can navigate to. [Industry-standard pattern names; Swift API Design Guidelines; check: review]
- **A-7** If the platform provides a feature, use it. For any job the platform already handles, the native mechanism is required: window chrome and the title bar or toolbar, navigation, tab bars, modals and alerts, search, sidebars and split views, menus, lists, progress indicators and pickers. Building an equivalent out of native parts is still a substitute; "every piece is a native control" is not an excuse. Examples, not a full list: a home-made router, a custom header or title bar in a window with a hidden title bar, a custom tab bar where `TabView` works, a home-made search field instead of `.searchable`, a custom sidebar instead of `NavigationSplitView`, a dimmed overlay used as a modal, hand-drawn progress indicators or pickers, and overriding focus or key handling. A workaround or substitute is allowed only where the plan explicitly approved it as a deliberate exception; never add one silently or as a quick fix. Each UI plan item names the native feature it uses, so any substitute is visible when the plan is approved. A pull request that adds a workaround or substitute pattern from the native-patterns checker's list fails, unless the plan's approved list of native deviations covers it. [Apple HIG; Apple platform conventions; check: scan:native-pattern]
<!-- end shared-section -->

<!-- shared-section: shared/apple-coding.md -->
## Coding (C)

- **C-1** Names follow the Swift API Design Guidelines: clear where they are used, reading naturally at the call site, with no abbreviations the reader must decode. [Swift API Design Guidelines; check: review]
- **C-2** Model data uses value types (`struct`, `enum`) by default. Use classes only when something needs identity or a lifecycle. Shared mutable state is protected by the language's concurrency model (actors, main-actor UI state). [Swift API Design Guidelines; Apple concurrency documentation; check: review]
- **C-3** No force-unwraps or force-tries (`!`, `try!`) on code paths that can fail at runtime; handle the optional or the error. Force operations are only for conditions the code itself proves can't fail. [Swift language practice; check: swiftlint:force_unwrapping, swiftlint:force_try, swiftlint:force_cast]
- **C-4** A change merges only with zero new compiler warnings and a clean lint run under the project's SwiftLint configuration. [SwiftLint standard rules; check: swiftlint, swiftformat, tool:warnings-as-errors]
- **C-5** No hardcoded facts about the world outside the code. This covers a repository's default branch, a file path, a URL or port, a plan or platform tier, and an external system's names or limits. Get each such fact from the system that owns it, or read it from the one place it is configured, through one shared function that every caller uses. Where the real answer can be looked up, a hardcoded assumption about external state (a branch named "main", a fixed path or URL) fails review. [Twelve-Factor App, config; check: scan:env-literal]
<!-- end shared-section -->

## Engineering quality (ENG)

- **ENG-1** Reactive state: any state that can change while it is on screen, or that lives longer than one function call, is published through the platform's observation system (Observation or Combine on Apple platforms). Never poll it or refresh it by hand. Values used once stay plain; don't wrap constants in observation. [Platform best practice — Apple; check: review]
- **ENG-2** Responsive layout: screens adapt using the platform's standard layout system. On desktop and web they adapt to window size; on phones and tablets, to rotation and size-class changes. No fixed screen dimensions. [Platform best practice — Apple HIG Layout; check: advisory:fixed-screen-size, review]
- **ENG-3** Never block a thread. Long waits (network calls, spawned processes, timers, polling) are asynchronous. Never sleep on a held thread, and never make blocking code callable from the UI. [Platform best practice — Apple; check: scan:blocking-call]
- **ENG-4** Child processes end with their parent. Any process or worker the app starts is tied to the app's lifetime, so quitting the app or cancelling the task cleans it up. No orphaned processes. [Platform best practice; check: review]
- **ENG-5** Bad input never crashes the app. Invalid input or unexpected data produces a typed error that is shown or passed on. Assertions that stop the app are only for programmer errors, not for conditions the app can recover from. [Platform best practice; OWASP Cheat Sheet: Error Handling; check: review]
- **ENG-6** Secrets are kept in the platform's secure store (the Keychain on macOS), never in plaintext files, source code or logs. [OWASP MASVS-STORAGE; Apple platform security; check: scan:secret-literal, review]
- **ENG-7** The app is signed and runs with the hardened runtime enabled. The direct-download build is also notarized. Nothing in the app needs library validation or code-signing enforcement turned off to run. Coast's release step does the signing and notarization; this rule keeps the code compatible with it. [Apple notarization + hardened runtime documentation; check: process]

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

<!-- shared-section: shared/documentation-native.md -->
## Documentation (DOC)

- **DOC-1** Every public type and function has a doc comment saying what it does, including parameters and return value where they aren't obvious. The generated API reference is built from these comments. [Project rule; check: scan:doc-comments]
- **DOC-2** A doc comment matches what the code actually does. A wrong doc comment is a code problem, not a wording problem. [Project rule; check: review]
<!-- end shared-section -->

---

## Sources

- **Coast Standards** — the DRY, strings and design-token rules (DRY, L, DES) are this repository's own rules, applied to every project that adopts it.

The other rules are written in this project's own words. They are drawn from these guides, listed for reference and further reading:

- **OWASP Application Security Verification Standard (ASVS) 5.0** — <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Mobile Application Security Verification Standard (MASVS) 2.1** — <https://mas.owasp.org/MASVS/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** — <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **W3C Web Content Accessibility Guidelines (WCAG) 2.2** — <https://www.w3.org/TR/WCAG22/> (W3C document license; also ISO/IEC 40500)
- **Apple App Sandbox, notarization and hardened runtime documentation** — <https://developer.apple.com/documentation/security/> (proprietary; referenced only)
- **Apple App Review Guidelines** — <https://developer.apple.com/app-store/review/guidelines/> (proprietary; referenced only, no text reproduced)
- **Apple Human Interface Guidelines** — <https://developer.apple.com/design/human-interface-guidelines/> (proprietary; referenced only)
- **Swift API Design Guidelines** — <https://www.swift.org/documentation/api-design-guidelines/> (Swift.org; referenced only, no text reproduced)
- **SwiftLint** (standard rule set; the automatic checker some rules name) — <https://github.com/realm/SwiftLint> (MIT)

No text from these guides is reproduced here. Every rule is an original plain-language statement that cites its source, so you can edit or replace this file with no license obligations.
