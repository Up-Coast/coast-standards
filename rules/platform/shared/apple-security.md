## Security (SEC)

- **SEC-1** All network traffic uses HTTPS. [check: scan:plaintext-http]
- **SEC-2** Validate all outside data (input, responses, deep links, shared files) and parameterize every query. [check: scan:sql-string-assembly, review]
- **SEC-3** No home-made cryptography, hashing or random numbers. [check: review]
- **SEC-4** Secrets never appear in source, logs, analytics or error messages. [check: scan:secret-literal]
- **SEC-5** User-facing errors never show stack traces, queries or paths. [check: review]
