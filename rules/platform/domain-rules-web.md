<!-- coast-rules-version: 9 -->
# Project rules

This file is a starting set of rules for your project. They come from well-known engineering and security guides, listed under Sources at the bottom.

**This file belongs to you.** Edit any rule, delete rules that don't apply, and add your own.

Automated reviewers check every code change against the rules in this file. A rule you add here applies to every change from then on.

How to read a rule:

- The id (for example `SEC-3`) is used in reviews, tickets and tests.
- The sentence after it is one checkable requirement.
- The brackets name the source guide and how the rule is checked.

Keep new rules checkable. A reviewer must be able to answer "does this change break the rule: yes or no?"

## Keep it DRY (DRY) — the rule above every other rule

Every piece of knowledge is defined in exactly one place. Everything else uses it from there.

- **DRY-1** Create design components once and reuse them. Before creating any view, component or helper, check for an existing one, or a combination of existing ones. A near-duplicate of an existing component fails review. Every new component states why nothing existing fit. [Coast standard; check: review]
- **DRY-2** Styling lives in one theme file (`theme.ts` or the tokens stylesheet). Every colour, font, size, weight and spacing value is a token there. Never create a second theme file, and never write a styling value directly in a feature file. [Coast standard; check: scan:styling-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale (`locales/<lang>/…`). Add new strings there. Reuse an existing key before adding a near-duplicate. [Coast standard; check: scan:one-catalog-per-locale]
- **DRY-4** Error messages live in one place, like other strings. Never build error text where it is thrown or shown. [Coast standard; check: scan:ui-string-literal]
- **DRY-5** Shared behaviour (gestures, animations, formatting, validation) lives in one place and is called from there. Never reimplement it locally. [Coast standard; check: tool:jscpd, review]
- **DRY-6** Compute every derived value (a total, a score, a status, a rounding) in one place and reuse it. Never compute it again, slightly differently, somewhere else. [Coast standard; check: tool:jscpd, review]
- **DRY-7** Use one name per thing, everywhere. Choose the vocabulary once. Never add a synonym for something that already has a name. [Coast standard; check: review]

## Strings and localization (L)

Build the product so it can be translated from the first commit, even if no second language is planned. Moving strings out of the code later is expensive; doing it from day one costs nothing.

- **L-1** Never hardcode user-facing text. Every string a user can see lives in the string catalog under a named key. That includes labels, error messages, empty states, loading text, tooltips, accessibility labels, titles, notification text and units. A check fails the build on any bare user-facing string in view code. [Coast standard; check: scan:ui-string-literal]
- **L-2** Each locale has one catalog (`locales/<lang>/…`), and it is the only source of strings. Add new strings there. If an existing key already has the text you need, use that key instead of adding a near-duplicate. [Coast standard; check: scan:one-catalog-per-locale]
- **L-3** Keys describe meaning, not English wording: `vehicle.status.doNotDispatch`, not `do_not_dispatch_text`. Then a translation can differ from the English phrasing. [Coast standard; check: scan:english-key]
- **L-4** Never build sentences by joining strings. Text that contains values uses the i18n library's interpolation with named placeholders (ICU MessageFormat), because word order differs between languages. The template with its placeholders is itself a catalog entry. [Coast standard; check: scan:ui-string-concat]
- **L-5** Handle plurals with the i18n library's plural rules (CLDR categories). Never write `if count == 1` in code. [Coast standard; check: scan:manual-plural]
- **L-6** Format dates, numbers and currency with locale-aware formatters (`Intl.NumberFormat`, `Intl.DateTimeFormat`), never with string templates. [Coast standard; check: review]
- **L-7** Layouts handle text that is about 30% longer. No fixed-width text container clips its text. Test with a long-string locale (German), with pseudo-localization, and with right-to-left when that is in scope. [Coast standard; check: review]
- **L-8** Localization plumbing is generated and managed by the i18n tooling, never written by hand. People write the text; tools write the plumbing. [Coast standard; check: review]
- **L-9** Domain terms need approved translations. Safety-critical or client-owned terms (status tiers, legal words) use approved translations, used word for word. List them in a glossary file for the project. An agent never invents its own translation of them. [Coast standard; check: review]
- **L-10** Text that reaches the UI from a database or API (descriptions, reference data) must be translatable too. Either the source provides a field per locale, or the UI maps stable codes to catalog keys. Never assume backend strings are exempt. [Coast standard; check: review]
- **L-11** Users can see and change the language. The change is instant and it persists (in the profile, local storage or URL, as the product requires). Switching language never loses anything the user typed. [Coast standard; check: review]
- **L-12** Apply all-caps and letter-spacing effects when rendering, with CSS `text-transform`. Never store the string already transformed: casing rules differ by language, and some scripts have no case at all. [Coast standard; check: scan:baked-case]

## Design tokens and components (DES)

How the design's values and components get into the code.

- **DES-1** Every visual value uses the design's exact token, by the design's token name. Never inline a near-match. If the design needs a value that has no token, add a token to the theme; don't write the value where it is used. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** Changing a brand colour or typeface takes an edit to one file. Nothing outside the theme file (`theme.ts` or the tokens stylesheet) knows a colour, font or spacing value. [Coast standard; check: scan:second-theme-file]
- **DES-3** Justify every new component in writing. The plan or pull request names the existing components that were checked and says why none fit. The component's builder and its approver are separate reviews. [Coast standard; check: review]
- **DES-4** If the project has a design-system spec, check every UI change against it. No hardcoded value bypasses the tokens. If a pattern needs a token that doesn't exist, add the token instead of inlining a value. [Coast standard; check: review]

## Money and payments (PAY)

- **PAY-1** Store and calculate money with decimal-safe types or whole minor units. Never use binary floating-point arithmetic on fractional amounts, because it can't represent cents exactly. This applies in JavaScript and in the database (`DECIMAL`/`NUMERIC`, not `FLOAT`). [Industry-wide practice; see Sources; check: advisory:money-float, review]
- **PAY-2** Every stored money amount carries its currency. Never add or compare amounts in different currencies without an explicit conversion step. [Industry-wide practice; check: review]
- **PAY-3** Decide rounding once: which method, and at which step. Compute every total in one place and reuse it; never compute it again slightly differently. Compute totals shown to the user on the server; never trust totals from the browser. [Industry-wide practice; OWASP ASVS; check: tool:jscpd, review]
- **PAY-4** Raw card numbers never touch the product's own code, servers or storage. Collect payments through a certified payment provider's hosted fields, checkout page or SDK. [PCI DSS scope rules; OWASP; check: review]

## Security (SEC)

- **SEC-1** All traffic uses HTTPS. HTTP redirects to HTTPS, and strict transport security (HSTS) is on. [OWASP ASVS; OWASP Cheat Sheet: Transport Layer Security; check: scan:plaintext-http]
- **SEC-2** Validate data from outside on the server before using it. This covers user input, query parameters, request bodies, uploaded files and third-party responses. Parameterize database queries; never build them from strings. [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization; check: scan:sql-string-assembly, review]
- **SEC-3** Render untrusted data through the framework's escaping. Never insert raw HTML (`innerHTML`, `dangerouslySetInnerHTML`) with untrusted content. Set a content security policy. [OWASP Cheat Sheets: XSS Prevention, Content Security Policy; check: scan:raw-html, review]
- **SEC-4** Protect state-changing requests against cross-site request forgery: turn on the framework's CSRF protection and set cookies to `SameSite`. [OWASP Cheat Sheet: CSRF Prevention; check: review]
- **SEC-5** Every server endpoint checks that the signed-in user may access the specific data it returns. Authorize object access by ownership, never by the id being hard to guess. [OWASP ASVS; OWASP Top 10: Broken Access Control; check: review]
- **SEC-6** Don't write your own cryptography. Use the platform's or a well-established library's implementation for encryption, hashing and random generation. [OWASP ASVS; check: review]
- **SEC-7** Secrets (API keys, tokens, credentials) exist only on the server. They never appear in client-side code, the shipped bundle, source control, logs or error messages. [OWASP ASVS; OWASP Cheat Sheet: Secrets Management; check: scan:secret-literal]
- **SEC-8** Error pages and API errors never expose internals such as stack traces, query text or file paths. [OWASP Cheat Sheet: Error Handling; check: review]
- **SEC-9** Pin JavaScript dependencies with the lockfile. Before adopting a package on a security-critical path (payments, auth, storage, crypto), confirm it is actively maintained and audit it. [OWASP Cheat Sheet: NPM Security; check: review]

## Accounts and sign-in (AUTH)

- **AUTH-1** Use an established identity provider or the framework's auth system for sign-in. Never build your own account store. If you must store passwords, hash them with a current memory-hard algorithm (Argon2id, scrypt or bcrypt). Never encrypt them or keep them readable. [OWASP Cheat Sheets: Authentication, Password Storage; check: review]
- **AUTH-2** Session cookies are `Secure`, `HttpOnly` and `SameSite`. Sessions expire and can be revoked. Generate a new session id at sign-in and at every privilege change. [OWASP Cheat Sheet: Session Management; check: review]
- **AUTH-3** Rate-limit sign-in attempts so accounts can't be brute-forced. [OWASP ASVS; check: review]
- **AUTH-4** Sensitive actions (deleting the account, changing email, password or payment details) confirm the user's identity again first. [OWASP ASVS; check: review]

## Privacy and personal data (PRIV)

- **PRIV-1** Collect only the data that the feature in front of the user actually needs. [GDPR data-minimization principle; check: review]
- **PRIV-2** Load non-essential cookies and trackers only after the user consents. The privacy policy states what is collected and why. [GDPR / ePrivacy practice; check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash reports or URLs (including query strings). [OWASP Cheat Sheet: Logging; OWASP ASVS; check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account, and the personal data behind it, from inside the product. [GDPR right to erasure; check: review]
- **PRIV-5** Protect personal data at rest. Encrypt it at the storage layer. Make it reachable only through the server's authorized paths. Never put it in world-readable buckets or public URLs. [OWASP ASVS; OWASP Top 10; check: review]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its background (3:1 for large text). [WCAG 2.2 — 1.4.3; check: review]
- **ACC-2** Click and tap targets are at least 24×24 pixels. Primary actions are comfortably larger. [WCAG 2.2 — 2.5.8; check: review]
- **ACC-3** Every interactive element can be reached and used with the keyboard alone, and shows a visible focus indicator. [WCAG 2.2 — 2.1.1, 2.4.7; check: review]
- **ACC-4** Interactive elements use semantic HTML (or correct ARIA roles) and have labels a screen reader can announce. Images that carry meaning have text alternatives. [WCAG 2.2 — 1.1.1, 4.1.2; check: review]
- **ACC-5** Text can be resized to 200% (browser zoom and text scaling) without cutting off meaning. [WCAG 2.2 — 1.4.4; check: scan:fixed-text-size]
- **ACC-6** Never use colour as the only signal. Show errors, success and selection with text, shape or an icon as well. [WCAG 2.2 — 1.4.1; check: review]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** Users can report content and block other users. Sanitize posted content before displaying it (see SEC-3). [Industry practice; OWASP; check: review]
- **UGC-2** Check uploaded files for expected type and size before processing or storing them. Never serve them back as executable. [OWASP Cheat Sheet: File Upload; check: review]

## Architecture (A)

- **A-1** Code lives in its layer. Pages and components display. Presentation logic prepares what is displayed. Services hold the business rules. Repositories do the data access. Business rules never sit in components or route handlers, and the UI never talks to storage directly. [Industry-standard separation of concerns: Service layer, Repository pattern; check: scan:layer-import, review]
- **A-2** Module dependencies go one way, with no cycles. Features depend on shared domain abstractions, never on each other or on concrete data code. [SOLID dependency-inversion principle; acyclic-dependencies principle; check: scan:import-matrix]
- **A-3** A module or component has one job. If a change would give it a second job, split it as part of that change. Automated size warnings are hints for the reviewer, never automatic failures. [SOLID single-responsibility principle; check: advisory:type-size, review]
- **A-4** Don't add abstractions for imagined needs. Create an interface only where something real substitutes for it: a second implementation or a test fake. A boundary between two modules always counts. [YAGNI — industry practice; check: review]
- **A-5** Use the framework's standard mechanism for standard needs such as routing, state and data fetching. Don't invent a framework that fights the one in use. [Framework documentation — per framework; check: scan:native-pattern]
- **A-6** A name says what a thing is, in standard industry terms: a page or route can be navigated to, a component is reusable presentation, a repository does data access. A name never claims a different role from what the code does. [Industry-standard pattern names; check: review]

## Coding (C)

- **C-1** Write TypeScript with strict mode on. `any` fails review wherever a real type can be written. [TypeScript documentation; check: tsc:strict]
- **C-2** Components and state follow the framework's conventions (for React: function components, hooks, and the Rules of Hooks). Never change state in place; updates create new values. [Framework documentation; check: eslint, review]
- **C-3** Await or explicitly handle every promise. No floating promises: a rejected promise always ends up as a handled error. [TypeScript/ESLint practice; check: eslint:@typescript-eslint/no-floating-promises]
- **C-4** A change merges only with zero new TypeScript errors and a clean run of the project's ESLint and Prettier configuration. [ESLint / Prettier; check: eslint, prettier, tool:warnings-as-errors]
- **C-5** Don't hardcode facts about the world outside the code. Examples: a repository's default branch, a file path, a URL or port, a plan or platform tier, an external system's names or limits. Ask the system that owns the fact, or read it from its single configured location. Either way, go through one shared function that every caller uses. Hardcoding an assumption about external state (a branch named "main", a fixed path or URL) fails review whenever the real answer can be looked up. [Twelve-Factor App, config; check: scan:env-literal]

## Engineering quality (ENG)

- **ENG-1** Reactive state: state that can change while it is on screen, or that lasts longer than one function call, lives in the framework's state system (component state, or a store the UI subscribes to). The UI re-renders from it. Never keep it in module-level variables that the UI polls or refreshes by hand. Values used once stay plain; don't wrap constants in state. [Platform best practice — web frameworks; check: review]
- **ENG-2** Responsive layout: pages adapt to the window size with fluid layout (flexbox or grid, relative units, media queries). No fixed page dimensions, and no horizontal page scrolling at common widths. [Platform best practice — responsive web design; check: advisory:fixed-screen-size, review]
- **ENG-3** Never block the main thread. Long waits (network calls, heavy computation) are asynchronous, and heavy work moves off the UI path (to the server or a worker). No busy-waiting. [Platform best practice — web performance; check: scan:blocking-call]
- **ENG-4** Background work ends with its owner. Every worker, subscription, interval or listener is cleaned up when its owner unmounts, navigates away or is cancelled. Server-side child processes end with their parent. No leaks, no orphans. [Platform best practice; check: review]
- **ENG-5** Bad input never causes a crash. Invalid input or unexpected data produces a typed error that is shown or reported, never an unhandled exception. The server validates on its own; client-side checks are a convenience, not protection. [OWASP ASVS; OWASP Cheat Sheet: Error Handling; check: review]
- **ENG-6** Secrets live in the deployment platform's secret store (environment secrets or a vault). Never put them in plaintext files, source control, client code or logs. [OWASP Cheat Sheet: Secrets Management; check: scan:secret-literal, review]

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

- **Coast Standards** — the DRY, strings and design-token rules (DRY, L, DES) are this repository's own rules. They apply to every project that adopts it.

The rules above are written in this project's own words. They are based on these guides, listed for reference and further reading:

- **OWASP Application Security Verification Standard (ASVS) 5.0** — <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** (XSS Prevention, CSRF Prevention, Session Management, Secrets Management, NPM Security, File Upload, and others) — <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **OWASP Top 10** — <https://owasp.org/www-project-top-ten/> (CC BY-SA 4.0)
- **W3C Web Content Accessibility Guidelines (WCAG) 2.2** — <https://www.w3.org/TR/WCAG22/> (W3C document license; also ISO/IEC 40500)
- **TypeScript documentation** — <https://www.typescriptlang.org/docs/> (referenced only)
- **React documentation** (including the Rules of Hooks; applies when the project uses React) — <https://react.dev/> (CC BY 4.0 — referenced only, no text reproduced)
- **ESLint / typescript-eslint / Prettier** (standard rule sets, used as the automated checkers some rules name) — <https://eslint.org/>, <https://typescript-eslint.io/>, <https://prettier.io/> (MIT)

No text from these guides is copied here. Every rule is written in our own words and cites its source, so you can edit or replace this file with no license obligations.
