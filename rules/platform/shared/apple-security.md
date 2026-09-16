## Security (SEC)

- **SEC-1** All network traffic is encrypted (HTTPS/TLS). No plaintext HTTP endpoints. [OWASP ASVS; OWASP MASVS-NETWORK; check: scan:plaintext-http]
- **SEC-2** Validate all data from outside the app before using it: user input, network responses, deep links and shared files. Database queries are parameterized, never built from strings. [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization; check: scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography. Encryption, hashing and random-number generation use the platform's or the standard library's implementations. [OWASP MASVS-CRYPTO; check: review]
- **SEC-4** Secrets (API keys, tokens, credentials) never appear in source code, logs, analytics or error messages. [OWASP ASVS; MASVS-STORAGE; check: scan:secret-literal]
- **SEC-5** Error messages shown to users never expose internals such as stack traces, query text or file paths. [OWASP Cheat Sheet: Error Handling; check: review]
