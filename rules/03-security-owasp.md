# Security — OWASP-derived rules

Based on OWASP ASVS 5.0, OWASP MASVS 2.1, the OWASP Cheat Sheet Series, PCI DSS scope rules and platform review guidelines. Each rule is our own plain-language statement that cites its source; no source text is copied. This file is the cross-platform core. The checkable version for each platform is in `platform/`.

## Network and data handling (SEC)

- **SEC-1** All network traffic uses encrypted connections (HTTPS/TLS). No plaintext HTTP endpoints. Web: redirect HTTP to HTTPS. Android: disable cleartext in the network security config. [OWASP ASVS; MASVS-NETWORK; check: scan:plaintext-http]
- **SEC-2** Validate external data before using it: user input, network responses, deep links, and uploaded or shared files. Database queries are parameterized, never built from strings. [OWASP Cheat Sheets: Input Validation, Query Parameterization; check:
  scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography. Use platform or standard-library implementations for encryption, hashing and random numbers. [OWASP MASVS-CRYPTO; check: review]
- **SEC-4** Secrets (API keys, tokens, credentials) never appear in source code, logs, analytics or error messages. Keep them in the platform's secure store or the deployment platform's secret store, and load them through environment or config outside the repo. [OWASP
  ASVS; MASVS-STORAGE; check: scan:secret-literal]
- **SEC-5** Error messages shown to users never expose internals such as stack traces, query text or file paths. [OWASP Cheat Sheet: Error Handling; check: review]
- **Web additions:** use contextual output encoding against XSS. Protect every state-changing request against CSRF. Check authorization on the server for every endpoint, never only in the client. Pin JS dependencies with a lockfile. [check: scan:raw-html, review]

## Accounts and sessions (AUTH)

- **AUTH-1** Use the platform's sign-in or an established identity provider. Never build your own account store. If you must store passwords, hash them with Argon2id, scrypt or bcrypt. Never store them encrypted or readable. [OWASP Cheat Sheets: Authentication, Password Storage; check:
  review]
- **AUTH-2** Session tokens expire, can be revoked, and are regenerated at sign-in and at every privilege change. Web cookies are `Secure`, `HttpOnly` and `SameSite`. [OWASP: Session
  Mgmt; check: review]
- **AUTH-3** Rate-limit sign-in attempts. [OWASP ASVS; check: review]
- **AUTH-4** Before a sensitive action (deleting the account, changing email, password or payment details), confirm the user's identity again. [OWASP ASVS; check: review]
- Shared-secret and token schemes (link-token access, API tokens): store only a hash of the token, compare in constant time, and support revocation with an active/inactive status.

## Privacy and personal data (PRIV)

- **PRIV-1** Collect only the data that the feature in front of the user actually needs. [GDPR data-minimization; Apple ARG §5.1; check: review]
- **PRIV-2** Declare every kind of data collected or shared: in the store privacy listing, and on the web as consent for non-essential cookies. [check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash reports or URLs. [OWASP MASVS-STORAGE; Cheat Sheet: Logging; check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account and the data behind it. [Apple ARG
  §5.1.1(v); check: review]
- **PRIV-5** Store personal data at rest in protected storage, never world-readable. [check: review]

## Payments (PAY)

- **PAY-1** Store and calculate money with decimal or whole-number types, never binary floating point. [check: advisory:money-float, review]
- **PAY-2** Every stored amount carries its currency. No math across currencies without an explicit conversion. [check: review]
- **PAY-3** Decide rounding once. Compute every total in one place and reuse it. [check: tool:jscpd, review]
- **PAY-4** In-app digital goods go through the platform's in-app purchase system, using the subscription layer the owner has standardized on. [Apple ARG §3.1; check: review]
- **PAY-5** Raw card numbers never touch the app's own code or storage. Use only a certified provider SDK or the platform's payment sheet. [PCI DSS; OWASP; check: review]

## Sensitive-code handling (process)

- **Sensitive categories, auto-classified:** auth and permissions · payments · billing · personal data and secrets · deletes or irreversible writes · schema migrations · concurrency · queues · retries · shared libraries and library updates. [check: process]
- Changes to sensitive code get the extra-careful path: a dedicated security review (`/security-review` or equivalent), extra load and abuse testing, and a feature flag. Where more than one model provider is available, add a second review by a different provider, because models favour output from their own family.
- **Config and governance files are not agent-editable.** Agents never edit the files that define their own checks or evaluation rules, even with approval. Such changes are flagged to a person. Secrets and config are kept where agents cannot reach them. [check: session:governing-edit]
- **Schema safety:** make schema and model changes FIRST, before the code that depends on them. A new schema must work with old app versions. Backfills must be resumable. Dropping a column is blocked until nothing uses it. Migration identifiers that have shipped never change. [check: process]
- **No hard deletes of user-meaningful records** unless the product spec explicitly requires them. Prefer an active/inactive status. [check: review]
- Test for prompt injection on any surface that passes external text to a model. Test low-connectivity behaviour everywhere.

## Spreadsheets and uploads

- **CSV and spreadsheet exports escape formula-injection prefixes** (`=`, `+`, `-`, `@`), so an exported cell can't run when the file is opened. Show cell content from an uploaded file as text; never interpret it. [OWASP CSV Injection; check:
  review]
- **Upload endpoints validate type and size BEFORE processing**, not after. The order is the rule: validating after parsing means the risky step has already run. [OWASP Cheat Sheet: File Upload; check: review]

## Frontend supply chain

- **No CDN-loaded scripts.** Install dependencies and pin them with a lockfile. A script loaded from a CDN at runtime bypasses the lockfile and can change without you knowing. [check: scan:cdn-script]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
