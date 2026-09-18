# Priority rules — the non-negotiables

These rules come before convenience, speed and habit. When two rules conflict, the one higher in this list wins.

## 1. DRY is the rule above all other rules

Every piece of knowledge is defined in exactly one place. Everything else uses that place.

The checkable rules are **DRY-1 to DRY-7 in every platform rules document** (`rules/platform/domain-rules-<platform>.md`, copied into a project as `docs/domain-rules.md`). Each one names the check that enforces it.

In short: create a component once and reuse it (DRY-1). Keep styling in one theme file and never inline it (DRY-2). Keep strings in one catalog per locale (DRY-3; see rule 2). Define error messages in one place (DRY-4). Define cross-cutting behaviour in one place (DRY-5). Compute every derived value in one place (DRY-6, PAY-3 generalized). Use one name per thing (DRY-7).

These rules live in the platform document, not here, so a project has one rules document to read and one place where rules are counted. The one case the duplicate-code check cannot see is parallel work streams; how they are sequenced and merged is in `06-testing.md`, under Cadence.
[check: context]

## 2. User-facing text is never hardcoded — always, from day one

**Projects with a user interface (type A):** never hardcode user-facing text in a view, component or template. Every string lives in the string catalog or locale files under a named key, so the product can be localized without code changes. This covers error messages, empty states, accessibility labels and text built from data. Details: `04-localization.md`.

**Backends, pipelines and CLIs (types B, C, D):** a localization catalog is usually unnecessary. But every string a person will read (API error text, emails, notifications, CLI output) is still defined in one place, not scattered as literals through handlers. Details: `types/backend-service.md`.
[check: scan:ui-string-literal]

## 2b. Simple and elegant: clear, easy to read and understand

Write solutions that are simple, elegant, and easy to read and understand. Build them on native solutions, never on workarounds. Native always wins, even when it is the more complex option. A workaround is never acceptable because it makes the code look simpler.

Simplicity describes the finished code, not how little effort it took. It rules out over-engineering: speculative layers, cleverness, and abstractions nothing uses. It equally rules out shortcuts, workarounds and partial solutions. A hack is not simple; it is incomplete.

Each of these is a review finding: a reviewer has to work to understand the code, or the code only "sort of" meets the requirement. The test: a senior engineer reading it should think "of course, that's how you do it."

In practice, implement the standard pattern for the problem, in full, using the native element or platform facility (rule 8). Prefer the boring construct and the obvious name. If an established, well-supported library already solves the problem, use it instead of building or hacking your own; its licence must be compatible and recorded. The same applies inside your own codebase: a helper that already exists is a solved problem, so use it.

This rule prevents over-engineering. It never allows a coding agent to take shortcuts.
[check: review]

## 2c. A coding agent never changes infrastructure unless told to

This is a hard rule. Never create, modify or destroy infrastructure unless the user has told you, in the current conversation, to do that specific thing. Infrastructure includes cloud apps, machines and volumes, storage buckets, secrets and tokens, DNS, deployments, CI pipelines and account settings.

If a task seems to need an infrastructure change, finish every other part, then stop and ask in one sentence. Read-only checks (status, logs, health) are fine. Setup work the user assigns is still the agent's job. Infrastructure changes nobody asked for never are.
[check: session:infra-command]

## 2d. Facts about the world are never hardcoded — ask, don't assume

Never write a fact about something outside the code as a literal where it is used. Examples: a repository's default branch, a file path, a URL or port, a plan or platform tier, an external system's names, formats or limits.

Instead, either ask the system that owns the fact, or read it from its one configured location. Do this through one shared function that every caller uses. This is rule 1 (DRY) applied to environment facts. It prevents a wrong assumption being fixed at one call site but surviving at the others, so the bug keeps coming back.

Enforcement: the rules scanner's `env-literal` check (`.coast/checks/check_rules.py`, installed by `enforcement/adopt.py`) refuses a known environment literal on any added line, at commit and at push. Known literals include a branch name such as "main" or "master", an absolute path, and a hardcoded host or port. It works like `ui-string-literal` and `styling-literal`, which refuse inlined text and styling. The platform rules documents carry it as a checkable rule (C-5 / ARCH-8), so it applies in adopting projects too. [check: scan:env-literal]

## 3. OWASP rules are followed

Every project follows the security rules in `03-security-owasp.md`. They are based on OWASP ASVS, OWASP MASVS and the OWASP Cheat Sheet Series. Any change that touches auth, payments, user input or data access gets a security review before it ships.
[check: process]

## 4. Customer/user data never enters version control

The git repo holds code and deliberate reference data only. Never commit customer data, operational data, user content or credentials.
[check: scan:secret-literal]

## 5. Never invent domain logic behind a safety or business decision

If the client owns a formula, threshold or rule, or it is not defined yet, leave it as a clearly labelled stub. Show gaps openly. Flag nulls, placeholders and unvalidated data in the UI and in the code. Never resolve them silently or fake them. [check: review]

## 6. Tests are mandatory and honest

Write the failing test first. Never weaken a test to make it pass. Never mark a failing task complete. A test must fail when the behaviour it names is broken. Assertions so weak that any implementation passes do not count as coverage. Details: `06-testing.md`.
[check: scan:test-weakened, review]

## 7. Every commit gets pushed — same session, no exceptions

Never commit without pushing in the same session. If the push is refused, fetch, reconcile and push again. Never leave work on only one machine. Commit once per task, not once per session. [check: session:unpushed-at-stop]

## 8. Native/platform-standard first

If the platform provides a feature, use it. Use the native feature unless you have approval to do otherwise. When something fails and you don't know why, do not pile up non-native workarounds. Stop, confirm the failure is real, and ask.
[check: scan:native-pattern]

## 9. The owner is the final QA gate on every release

Nothing is submitted or published until the owner has finished a manual QA pass. Every launch plan includes this as an explicit step, in order. Give the owner a testable build and a feature-by-feature checklist. [check: process]

## 10. Standing decisions (never re-open)

- Every app uses one subscription layer, chosen once. Never reopen the "which billing layer" question for a project.
- Marketing and content: draft freely. Publish only when the owner explicitly says so, each time.
- Before answering, check factual claims about external products, APIs and policies against primary sources. Third-party coverage is a lead to check, never the answer.
[check: process]


## Definition of done: a rule without its guard is not done (2026-09-01)

Every rule here that a machine can check ships with a check that fails the build when the rule is broken: a source-scan test, a lint rule or a CI step. A rule that exists only in a document is a request, and requests lose to whatever is easiest for the agent. Defects with a guard stay fixed; defects without one come back.

A task is done only when all three of these hold:

1. The guard exists and is named: the test or check that stops the rule being broken from that commit on.
2. A reviewer who did not build it confirms it from the code, not from the builder's report.
3. For anything a person can see or press: the builder has used it in the built product, as a person would, and recorded what they saw. A screenshot of the pane just built is not use. The flow includes the surrounding window, its title and settings, navigating in and out, and a relaunch.

Anything marked built without all three is not built. Do not write "verified" unless you can name the test or the on-screen walk. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
