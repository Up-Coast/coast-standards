## Accounts and sign-in (AUTH)

- **AUTH-1** Use the platform's sign-in or an established identity provider, never a hand-built account store; any stored password is hashed with Argon2id, scrypt or bcrypt. [check: review]
- **AUTH-2** Session tokens expire, can be revoked, and are reissued at sign-in and on privilege change. [check: review]
- **AUTH-3** Rate-limit sign-in attempts. [check: review]
- **AUTH-4** Re-confirm identity before account deletion or an email, password or payment change. [check: review]
