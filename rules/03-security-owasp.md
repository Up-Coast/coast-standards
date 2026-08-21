# Security — OWASP-derived rules

Sourced from OWASP ASVS 5.0, OWASP MASVS 2.1, the OWASP Cheat Sheet Series, PCI DSS scope
rules, and platform review guidelines. Every rule is an original plain-language statement
citing its source — no source text is reproduced. The per-platform files in `platform/`
carry the checkable per-platform variants; this is the cross-platform core.

## Network and data handling (SEC)

- **SEC-1** All network traffic uses encrypted connections (HTTPS/TLS); no plaintext HTTP
  endpoints. Web: HTTP→HTTPS redirect. Android: cleartext disabled in the network security
  config. [OWASP ASVS; MASVS-NETWORK]
- **SEC-2** External data — user input, network responses, deep links, uploaded/shared
  files — is validated before use; database queries are parameterized, never assembled from
  strings. [OWASP Cheat Sheets: Input Validation, Query Parameterization]
- **SEC-3** No home-made cryptography. Encryption, hashing, and random generation use
  platform/standard-library implementations. [OWASP MASVS-CRYPTO]
- **SEC-4** Secrets — API keys, tokens, credentials — never appear in source code, logs,
  analytics, or error messages. They live in the platform's secure store or the deployment
  platform's secret store, loaded via environment/config outside the repo. [OWASP ASVS;
  MASVS-STORAGE]
- **SEC-5** Error messages shown to users never expose internals (stack traces, query text,
  file paths). [OWASP Cheat Sheet: Error Handling]
- **Web additions:** contextual output encoding against XSS; CSRF protection on every
  state-changing request; server-side authorization on every endpoint (never client-only);
  JS dependencies pinned by lockfile.

## Accounts and sessions (AUTH)

- **AUTH-1** Platform sign-in or an established identity provider — never a hand-rolled
  account store. If passwords must be stored: Argon2id, scrypt, or bcrypt — never encrypted
  or readable. [OWASP Cheat Sheets: Authentication, Password Storage]
- **AUTH-2** Session tokens expire, can be revoked, and are regenerated at sign-in and any
  privilege change. Web cookies: `Secure`, `HttpOnly`, `SameSite`. [OWASP: Session Mgmt]
- **AUTH-3** Sign-in attempts are rate-limited. [OWASP ASVS]
- **AUTH-4** Sensitive actions (delete account, change email/password/payment) re-confirm
  identity first. [OWASP ASVS]
- Shared-secret/token schemes (link-token access, API tokens): store only a hash of the
  token, compare in constant time, and support revocation via an active/inactive status.

## Privacy and personal data (PRIV)

- **PRIV-1** Collect only the data the feature in front of the user actually needs.
  [GDPR data-minimization; Apple ARG §5.1]
- **PRIV-2** Every kind of data collected or shared is declared (store privacy listing /
  consent for non-essential cookies on web).
- **PRIV-3** Personal data never appears in logs, analytics events, crash reports, or URLs.
  [OWASP MASVS-STORAGE; Cheat Sheet: Logging]
- **PRIV-4** Users can delete their account and the data behind it. [Apple ARG §5.1.1(v)]
- **PRIV-5** Personal data at rest lives in protected storage, never world-readable.

## Payments (PAY)

- **PAY-1** Money is stored/calculated with decimal or whole-number types — never binary
  floating point.
- **PAY-2** Every stored amount carries its currency; no cross-currency math without
  explicit conversion.
- **PAY-3** Rounding is decided once; every total is computed in one place and reused.
- **PAY-4** Digital goods in-app go through the platform's IAP system (for Abbey's apps:
  via RevenueCat, always). [Apple ARG §3.1]
- **PAY-5** Raw card numbers never touch the app's own code or storage — certified provider
  SDK or platform payment sheet only. [PCI DSS; OWASP]

## Sensitive-code handling (process)

- **Sensitive categories, auto-classified:** auth & permissions · payments · billing ·
  PII/secrets · deletes or irreversible writes · schema migrations · concurrency · queues ·
  retries · shared libraries/library updates.
- Touching sensitive code triggers the heavy path: a dedicated security review pass
  (`/security-review` or equivalent), extra load/abuse testing, feature-flag gating, and —
  where multiple model providers are available — cross-provider double review (models favor
  their own family's output).
- **Config and governance files are not agent-editable.** Agents never edit the files that
  define their own checks or evaluation rules, not even with approval; such changes are
  flagged to a human. Secrets/config live outside agent reach.
- **Schema safety:** schema/model changes happen FIRST, before dependent code; new schema
  works with old app versions; backfills are resumable; destructive column drops are blocked
  until the column is unused; shipped migration identifiers are frozen.
- **No hard deletes of user-meaningful records** unless the product's spec explicitly calls
  for them — prefer active/inactive status.
- Prompt-injection coverage is part of testing on any surface that feeds external text to a
  model. Low-connectivity behavior is tested on everything.

## Spreadsheets and uploads

- **CSV and spreadsheet exports escape formula-injection prefixes** (`=`, `+`, `-`, `@`) so
  an exported cell can't execute when the file is opened. Cell content from an uploaded
  file is rendered as text, never interpreted. [OWASP CSV Injection]
- **Upload endpoints validate type and size BEFORE processing**, not after — the ordering is
  the rule, because validation after parsing has already run the risky step. [OWASP Cheat
  Sheet: File Upload]

## Frontend supply chain

- **No CDN-loaded scripts.** Dependencies are installed and pinned by lockfile; a script
  fetched from a CDN at runtime defeats the lockfile entirely and changes under you.
