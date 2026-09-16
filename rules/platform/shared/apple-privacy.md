## Privacy and personal data (PRIV)

- **PRIV-1** The app collects only the data that the feature in use actually needs. [Apple App Review Guidelines §5.1; GDPR data-minimization principle; check: review]
- **PRIV-2** Every kind of data the app collects or shares is declared in the store's privacy listing. No undeclared collection. [Apple App Review Guidelines §5.1; check: review]
- **PRIV-3** Personal data never appears in logs, analytics events, crash reports or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging; check: ratchet:pii-in-log, review]
- **PRIV-4** Users can delete their account, and the personal data linked to it, from inside the app. [Apple App Review Guidelines §5.1.1(v); check: review]
- **PRIV-5** Personal data stored on the device stays in the app's protected container, with the platform's data protection applied. Never store it where other apps or users can read it. [OWASP MASVS-STORAGE; check: review]
