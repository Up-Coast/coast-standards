# Priority rules — the non-negotiables

These override convenience, speed, and any conflicting habit. Where two rules collide, the
one higher on this list wins.

## 1. DRY is the rule above all other rules

Every piece of knowledge has exactly ONE home, and everything else uses that home.
(Set by the owner, 2026-08-20, as the rule above all other rules.)

The concrete, checkable rules are **DRY-1 to DRY-7 in every platform rules document**
(`rules/platform/domain-rules-<platform>.md`, copied into a project as its
`docs/domain-rules.md`), each with the check that holds it named: components are created
once and reused (DRY-1), styling lives in one theme file and is never inlined (DRY-2),
strings live in one catalog per locale (DRY-3 — see rule 2), error messages have one home
(DRY-4), cross-cutting behaviour has one home (DRY-5), every derived value is computed in
one place (DRY-6, PAY-3 generalized), and one name per thing (DRY-7). They live there, not
here, so a project has exactly one rules document to read and one place the number is
counted.
[check: context]

## 2. User-facing text is never hardcoded — always, from day one

**Projects with a user interface (type A):** no user-facing text is ever hardcoded in a
view, component, or template. Every string lives in the string catalog/locale files under a
named key, so the product is localizable without touching code. This applies to error
messages, empty states, accessibility labels, and text assembled from data. Full mechanics
in `04-localization.md`. (Coast decision)

**Backends, pipelines, and CLIs (types B, C, D):** a localization catalog is usually
ceremony, but every string a person will eventually read — API error text, emails,
notifications, CLI output — still has exactly ONE home rather than sitting as literals
scattered through handlers. Mechanics in `types/backend-service.md`.
[check: scan:ui-string-literal]

## 2b. Simple and elegant: clear, easy to read and understand

Solutions should be simple and elegant — clear, easy to read and easy to understand — built
on native solutions, never on workarounds. Native always wins, even when it is the more
complex option: a workaround is never acceptable just because it makes the code look
simpler. Favour native solutions. Simplicity is a quality of the finished code, not a
measure of how little effort it took. It rules out
over-engineering (speculative layers, cleverness, abstractions nothing uses) and it equally
rules out shortcuts, workarounds, and partial solutions: a hack is not simple, it is
incomplete. If a reviewer has to work to understand the code, that is a finding; if a
reviewer can see it only "sort of" meets the requirement, that is a finding too. Test: a
senior engineer reading it should think "of course, that's how you do it."

Concretely: implement the standard pattern for the problem, in full, with the native
element or platform facility (rule 8); prefer the boring construct and the obvious name;
when an established, well-supported library already solves it, use it rather than building
or hacking (licence compatible and recorded). The same standard applies to your own
codebase: a helper that already exists is an already-solved problem too.

Origin: the owner's instruction to the agent that built this repo — solutions should be
simple and elegant, clear and easy to read and understand. Clarified 21 Aug 2026 after an
agent read an earlier paraphrase as permission for shortcuts: the rule exists to prevent
over-engineering; it never licenses a coding agent to take shortcuts.
[check: review]

## 2c. A coding agent never changes infrastructure unless told to

(Hard rule, 2026-08-21.) Never create, modify, or destroy infrastructure — cloud
apps/machines/volumes, storage buckets, secrets and tokens, DNS, deployments, CI pipelines,
account settings — unless the user has told you, in the current conversation, to do that
specific thing. If a task appears to need it, finish every part that doesn't, then stop and
ask in one sentence. Read-only checks (status, logs, health) are fine. Setup work the user
assigns is still the agent's job; unprompted infrastructure changes never are. Origin: a
session asked for UI fixes created and destroyed a staging app, volume, bucket and secrets
on the user's account on its own initiative — a breach of trust.
[check: session:infra-command]

## 2d. Facts about the world are never hardcoded — ask, don't assume

(Filed 2026-08-29, after a hardcoded branch name blocked a Coast build — something the
guidelines should already have prevented.) A fact about anything outside the code — a
repository's default branch, a file path, a URL or port, a plan or platform tier, an
external system's names, formats, or limits — is never written as a literal at a use
site. Each such fact is either asked of the system that owns it or
read from its ONE configured home, through one shared function that every caller uses
(this is DRY, rule 1, applied to environment facts). The failure mode this prevents: the
assumption gets fixed at one call site and survives at seven others, so the "fixed" bug
keeps returning. Origin: `origin/main` was hardcoded across eight files in Coast; the
repo's real default branch was different; nothing could build.

Enforcement: the rules scanner's `env-literal` signature (`Scripts/checks/check_rules.py`,
installed by `enforcement/adopt.py`) refuses a known environment literal — a branch name
like "main"/"master", an absolute path, a hardcoded host or port — on any added line, at
commit and at push, the same way `ui-string-literal` and `styling-literal` refuse inlined
copy and styling; the shipped per-platform rules files carry it as a checkable rule
(C-5 / ARCH-8), so it holds in customer projects too. [check: scan:env-literal]

## 3. OWASP rules are followed

Every project complies with the security rules in `03-security-owasp.md`, which are sourced
from OWASP ASVS, OWASP MASVS, and the OWASP Cheat Sheet Series. Any change touching auth,
payments, user input, or data access gets a security review pass before it ships.
[check: process]

## 4. Customer/user data never enters version control

The git repo holds code (and deliberate reference data only). Customer data, operational
data, user content, and credentials never get committed. (Binding since 2026-08-18.)
[check: scan:secret-literal]

## 5. Never invent domain logic behind a safety or business decision

If a formula, threshold, or rule is owned by the client or undefined, it stays a labeled
stub. Surface gaps explicitly — nulls, placeholders, and unvalidated data get flagged in the
UI and the code, never silently resolved or faked. [check: review]

## 6. Tests are mandatory and honest

Write the failing test first. Never weaken a test to make it pass. Never mark a failing task
complete. A test must fail when the behavior it names is broken — assertions so weak that
any implementation passes don't count as coverage. Full rules in `06-testing.md`.
[check: scan:test-weakened, review]

## 7. Every commit gets pushed — same session, no exceptions

(Standing since 2026-07-25: never commit without pushing.) If the push is refused,
fetch, reconcile, and push — never leave work only on one machine. Commit per task, not per
session. [check: session:unpushed-at-stop]

## 8. Native/platform-standard first

If the platform provides the feature, the feature is used. Never chase an unexplained
failure with escalating non-native workarounds — pause, confirm the failure is real, and
ask. (Coast decision: always use the native feature unless approved to do differently.)
[check: scan:native-pattern]

## 9. The owner is the final QA gate on every release

Nothing is submitted or published until the owner's manual QA pass is done. Every launch
plan includes that as an explicit ordered step, with a testable build and a
feature-by-feature checklist delivered to the owner. [check: process]

## 10. Standing decisions (never re-open)

- One subscription layer for every app, decided once and never reopened per project —
  there is never an open "which billing layer" decision.
- Marketing and content: draft freely, publish only on the owner's explicit go, each
  time.
- Verify factual claims about external products/APIs/policies against PRIMARY sources
  before answering; third-party coverage is a lead, never the answer.
[check: process]


## Definition of done: a rule without its guard is not done (2026-09-01)

Every rule in this corpus that CAN be checked mechanically ships with the
check that fails the build when it is broken — a source-scan test, a lint
rule, a CI step. A rule that lives only in a document is a request, and
requests lose to whatever is cheapest for the session in front of the code.
Verified on Coast on 2026-09-01: every defect class with a guard test stayed
fixed; every class without one recurred, repeatedly, across sessions that
had all read the rule.

So a task is DONE only when both hold:

1. The guard exists and is named — the test or check that makes the rule
   unbreakable from that commit on.
2. A reviewer who is not the builder confirms it from the code, never from
   the builder's report.

Anything marked built without both is not built. "Verified" without a test
name or an on-screen walk is not a word to use. [check: process]
