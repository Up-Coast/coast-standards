# Priority rules — the non-negotiables

These override convenience, speed, and any conflicting habit. Where two rules collide, the
one higher on this list wins.

## 1. DRY is the rule above all other rules

Every piece of knowledge has exactly ONE home, and everything else uses that home.
(Abbey, 2026-08-20: "The project MUST STAY DRY. This is a rule above all other rules.")

Concretely, on every project:

- **Design components are created ONE time and reused.** Before creating any component,
  check whether an existing one (or a composition of existing ones) covers the need.
  "Use the existing one" is a valid and expected outcome; creating a near-duplicate is a
  review failure. New helper/component/template creation must be justified — say why an
  existing one wasn't reused. (Coast D34)
- **Styling lives in ONE theme file.** All colors, fonts, sizes, weights, and spacing are
  tokens in a single theme file; a second theme file can never be created; styling is never
  written into a feature file. Never invent a value or a near-match — use the design's exact
  token, or request a new token; never inline a literal. (Coast D15, D35, D101)
- **Strings live in ONE catalog per locale** — see rule 2.
- **Error messages are abstracted** to one place, like strings.
- **Cross-cutting behavior (gestures, animations, formatting) has one home** and is used,
  never re-implemented locally. (Coast D15)
- **Every derived value is computed in one place and reused** — never recomputed slightly
  differently in two places (totals, scores, statuses, rounding). (Coast PAY-3, generalized)
- **One name per thing, everywhere.** Pick the vocabulary once; never introduce a synonym
  for something that already has a name. (Coast D107)

Enforcement: reviews grep the diff for inlined strings, styling literals, and duplicated
logic, and fail the change when they find them.

## 2. User-facing text is never hardcoded — always, from day one

**Projects with a user interface (type A):** no user-facing text is ever hardcoded in a
view, component, or template. Every string lives in the string catalog/locale files under a
named key, so the product is localizable without touching code. This applies to error
messages, empty states, accessibility labels, and text assembled from data. Full mechanics
in `04-localization.md`. (Coast D36)

**Backends, pipelines, and CLIs (types B, C, D):** a localization catalog is usually
ceremony, but every string a person will eventually read — API error text, emails,
notifications, CLI output — still has exactly ONE home rather than sitting as literals
scattered through handlers. Mechanics in `types/backend-service.md`.

## 2b. Simple means not over-engineered — never "least effort"

The goal is the simplest *complete, correct* solution: the boring construct, the obvious
name, no speculative layers, nothing clever. "Simple" describes the shape of the finished
code, not how little work it took. It is never a reason to ship a partial solution, a
shortcut, a workaround, or a hack that "sort of" meets the requirement. Test: a senior
engineer reading the result should think "of course, that's how you do it" — not "that's a
quick patch." If the full, standard pattern (rule 8) is more code than a hack, the standard
pattern is still the simple one. Complexity is the enemy; incompleteness is not simplicity.

Concretely: implement the standard pattern for the problem, in full, with the native element
or platform facility. When an established, well-supported library already solves it, use it
rather than building or hacking — its licence must be compatible and recorded. The same
standard applies to your own codebase: a helper that already exists is an already-solved
problem too.

Origin (Abbey, 20 Aug 2026: "the simplest code possible… complex stuff always causes
problems"; clarified 21 Aug after an agent read it as permission for shortcuts: "it is
intended to avoid complex over-engineering. It is not intended for coding agents to take
shortcuts.")

## 2c. A coding agent never changes infrastructure unless told to

(Abbey, 2026-08-21, hard rule.) Never create, modify, or destroy infrastructure — cloud
apps/machines/volumes, storage buckets, secrets and tokens, DNS, deployments, CI pipelines,
account settings — unless the user has told you, in the current conversation, to do that
specific thing. If a task appears to need it, finish every part that doesn't, then stop and
ask in one sentence. Read-only checks (status, logs, health) are fine. Setup work the user
assigns is still Claude's job; unprompted infrastructure changes never are. Origin: a
session asked for UI fixes created and destroyed a staging app, volume, bucket and secrets
on the user's account on its own initiative — "a huge breach of trust."

## 3. OWASP rules are followed

Every project complies with the security rules in `03-security-owasp.md`, which are sourced
from OWASP ASVS, OWASP MASVS, and the OWASP Cheat Sheet Series. Any change touching auth,
payments, user input, or data access gets a security review pass before it ships.

## 4. Customer/user data never enters version control

The git repo holds code (and deliberate reference data only). Customer data, fleet data,
user content, and credentials never get committed. (Abbey, 2026-08-18, binding.)

## 5. Never invent domain logic behind a safety or business decision

If a formula, threshold, or rule is owned by the client or undefined, it stays a labeled
stub. Surface gaps explicitly — nulls, placeholders, and unvalidated data get flagged in the
UI and the code, never silently resolved or faked.

## 6. Tests are mandatory and honest

Write the failing test first. Never weaken a test to make it pass. Never mark a failing task
complete. A test must fail when the behavior it names is broken — assertions so weak that
any implementation passes don't count as coverage. Full rules in `06-testing.md`.

## 7. Every commit gets pushed — same session, no exceptions

(Abbey, 2026-07-25: "we should never commit without pushing.") If the push is refused,
fetch, reconcile, and push — never leave work only on one machine. Commit per task, not per
session.

## 8. Native/platform-standard first

If the platform provides the feature, the feature is used. Never chase an unexplained
failure with escalating non-native workarounds — pause, confirm the failure is real, and
ask. (Coast D128/D135; Abbey: "We should ALWAYS use the native feature unless otherwise
approved to do differently.")

## 9. Abbey is the final QA gate on every release

Nothing is submitted or published until her manual QA pass is done. Every launch plan
includes that as an explicit ordered step, with a testable build and a feature-by-feature
checklist delivered to her.

## 10. Portfolio standing decisions (never re-open)

- RevenueCat is the subscription layer for ALL apps, always — there is never an open
  "RevenueCat vs StoreKit" decision.
- Marketing/content: draft freely, never post/send/publish/schedule without Abbey's
  explicit go, each time.
- Verify factual claims about external products/APIs/policies against PRIMARY sources
  before answering; third-party coverage is a lead, never the answer.
