## Accounts and sign-in (AUTH)

- **AUTH-1** Sign-in uses the platform's sign-in system or an established identity provider, never a hand-built account store. If passwords must be stored, hash them with a current memory-hard algorithm (Argon2id, scrypt or bcrypt). Never encrypt them or store them readable. [OWASP Cheat Sheets: Authentication, Password Storage; check: review]
- **AUTH-2** Session tokens expire and can be revoked. A new token is issued at sign-in and whenever the user's privileges change. [OWASP Cheat Sheet: Session Management; check: review]
- **AUTH-3** Sign-in attempts are rate-limited, so accounts can't be brute-forced. [OWASP ASVS; check: review]
- **AUTH-4** Sensitive actions ask the user to confirm their identity again first. These include deleting the account and changing the email, password or payment details. [OWASP ASVS; check: review]
