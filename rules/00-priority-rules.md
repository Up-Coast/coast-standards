# Priority rules — the non-negotiables

Always loaded with the platform rules file (`docs/domain-rules.md`). Other numbered files are reference for their area. Higher rules win.

## 1. DRY is the rule above all other rules

Define each piece of knowledge once. Checkable rules: DRY-1 to DRY-7 in the platform rules file.
[check: context]

## 2. User-facing text is never hardcoded — always, from day one

UI strings, errors and labels included, live in the string catalog. Backends and CLIs keep human-read strings in one place.
[check: scan:ui-string-literal]

## 2b. Simple and elegant: clear, easy to read and understand

Implement the standard native pattern in full: no workarounds, hacks, partial fixes or unused abstractions. Reuse existing helpers, and an established library whose licence is compatible and recorded.
[check: review]

## 2b-1. Fix the class, not the instance

Search for every place with the defect's shape and fix them all through shared code, or record why one is left. Change sibling paths (error, cancel, keyboard, cold load) together, and add a guard. A second rejection of one area means building the shared piece, never a second patch.
[check: review, process]

## 2c. A coding agent never changes infrastructure unless told to

Never change infrastructure (cloud, secrets, DNS, deploys, CI, accounts) unless asked in this conversation; finish the rest and ask. Read-only checks and assigned setup work are fine.
[check: session:infra-command]

## 2d. Facts about the world are never hardcoded — ask, don't assume

Never inline an external fact (branch, path, URL, port, tier, limits). Read it from its owner or one configured place, through one shared function. [check: scan:env-literal]

## 3. OWASP rules are followed

Follow `03-security-owasp.md`. Auth, payment, input and data-access changes get a security review.
[check: process]

## 4. Customer/user data never enters version control

Never commit customer data, operational data, user content or credentials.
[check: scan:secret-literal]

## 5. Never invent domain logic behind a safety or business decision

Stub client-owned or undefined logic, labelled. Flag nulls, placeholders and unvalidated data; never fake them. [check: review]

## 6. Tests are mandatory and honest

Write the failing test first. Never weaken a test or mark a failing task done.
[check: scan:test-weakened, review]

## 7. Every commit gets pushed — same session, no exceptions

Push every commit in its session; if refused, fetch, reconcile, push. Commit once per task. [check: session:unpushed-at-stop]

## 8. Native/platform-standard first

Use platform features unless approved otherwise. On unexplained failure, confirm it and ask; never stack workarounds.
[check: scan:native-pattern]

## 9. The owner is the final QA gate on every release

Publish nothing before the owner's manual QA pass. Supply a testable build and a feature checklist. [check: process]

## 10. Standing decisions (never re-open)

- One subscription layer per app, chosen once.
- Draft marketing freely; publish only on the owner's go, each time.
- Check claims about external products against primary sources.
[check: process]

## Definition of done: a rule without its guard is not done (2026-09-01)

Every checkable rule ships with a guard. Done means:

1. The guard exists and is named.
2. A reviewer who did not build it confirms it from the code.
3. Anything visible was used in the built product (window, navigation, relaunch) and recorded.

Never write "verified" without naming the test or walk. [check: process]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
