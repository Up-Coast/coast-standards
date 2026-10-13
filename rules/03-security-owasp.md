# Security — OWASP-derived rules

Read this when a task touches security, personal data, payments or migrations.

## Network and data handling (SEC)

- **SEC-1** HTTPS/TLS only; redirect HTTP, disable Android cleartext. [check: scan:plaintext-http]
- **SEC-2** Validate all external data. Parameterize queries. [check: scan:sql-string-assembly, review]
- **SEC-3** No home-made crypto. [check: review]
- **SEC-4** Secrets stay out of source, logs and errors, loaded from a secure store. [check: scan:secret-literal]
- **SEC-5** User errors hide internals. [check: review]
- **Web additions:** output encoding, CSRF protection, server-side authorization, locked dependencies. [check: scan:raw-html, review]

## Accounts and sessions (AUTH)

- **AUTH-1** Use platform or established sign-in. Hash stored passwords with Argon2id, scrypt or bcrypt, never encrypt. [check: review]
- **AUTH-2** Sessions expire, revoke and regenerate at sign-in and privilege change. Cookies: `Secure`, `HttpOnly`, `SameSite`. [check: review]
- **AUTH-3** Rate-limit sign-in attempts. [check: review]
- **AUTH-4** Re-authenticate before account deletion or credential and payment changes. [check: review]
- Tokens: store a hash, compare in constant time, allow revoking.

## Privacy and personal data (PRIV)

- **PRIV-1** Collect only needed data. [check: review]
- **PRIV-2** Declare collected data in store listings and cookie consent. [check: review]
- **PRIV-3** No personal data in logs, analytics, crashes or URLs. [check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account and its data. [check: review]
- **PRIV-5** Protect personal data at rest. [check: review]

## Payments (PAY)

- **PAY-1** No floats for money. [check: advisory:money-float, review]
- **PAY-2** Amounts carry currency; convert explicitly. [check: review]
- **PAY-3** Round and total in one place. [check: tool:jscpd, review]
- **PAY-4** Digital goods use in-app purchase via the standard subscription layer. [check: review]
- **PAY-5** Card numbers only via certified SDK or payment sheet. [check: review]

## Sensitive-code handling (process)

- **Sensitive categories, auto-classified:** auth and permissions, payments, billing, personal data and secrets, deletes and irreversible writes, migrations, concurrency, queues, retries, shared libraries and their updates. [check: process]
- Sensitive changes get a security review, abuse tests, a feature flag and, if possible, a second-provider model review.
- **Config and governance files are not agent-editable.** Never edit your own checks, even if approved; ask a person. Keep secrets from agents. [check: session:governing-edit]
- **Schema safety:** schema first, old-version compatible, resumable backfills, drop only unused columns, shipped migration ids never change. [check: process]
- **No hard deletes of user-meaningful records** unless specified; use a status. [check: review]
- Test prompt injection on model inputs, and low connectivity.

## Spreadsheets and uploads

- **CSV and spreadsheet exports escape formula-injection prefixes** (`=`, `+`, `-`, `@`). Show uploaded cells as text. [check: review]
- **Upload endpoints validate type and size BEFORE processing** [check: review]

## Frontend supply chain

- **No CDN-loaded scripts.** [check: scan:cdn-script]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
