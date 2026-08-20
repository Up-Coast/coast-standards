# Documentation, git, and process

## Git

- **Commit per task, not per session.** Each commit is one completed, tested task with a
  message that names it.
- **Every commit gets pushed — same session, no exceptions.** If the push is refused,
  fetch, reconcile, push. Never leave work only on one machine.
- **Repos are private in the Up-Coast org** unless decided otherwise; secret-scan before
  the first push of any repo.
- **Worktrees over long-lived branches** for parallel agent runs; keep `main` releasable.
- **Protected main where the platform allows it:** PR required, review required, status
  checks required, no force-push, no deletion.

## Pull requests

- The ticket/task content travels WITH the change (committed file with a predictable name,
  not just pasted into a PR body), so checks can find it deterministically.
- PR self-checklist before requesting review: rules followed? UI code abstracted (no inline
  strings/styles)? architecture approvals honored? tests state their criteria?
- Screenshots of designed features attach to the PR; sensitive-code changes are flagged and
  get the heavy review path.
- A rejection must state explicitly what the actual problem is and what a compliant version
  looks like — so the fix doesn't churn unrelated things. A bare approve/reject is invalid:
  reviews list what was checked, pass or fail alike, and cite real files/rules.
- Discovered work no task covers is surfaced and proposed as a task — never silently built.
  If a finding contradicts the task or spec, the spec wins; flag the disagreement.
- Skipped review or untested work = unfinished work. Nothing ships on "it compiles."
  [BuilderOS build-loop]

## Documentation

- **Docs ship WITH the feature, not after.** "What if their QA needs to see the
  documentation before the product is released?"
- **Prefer diagrams over prose sprawl.** Agents overproduce markdown; too many docs cause
  agents to read the wrong ones. Every new class/module of consequence gets its diagram;
  system/flow diagrams are updated in place. Keeping your own diagrams correct needs no
  permission — do it in the same session and say so.
- **One predictably-named document per subject.** "Does it already exist?" must be a
  deterministic name lookup, forcing edit-not-create. No ad-hoc throwaway docs. Documents
  are edited, not deleted-and-recreated.
- **Decision log:** structured entries (decision, rationale, date, scope), two tiers —
  global/architectural (small, always loaded) and local (feature-scoped). Bar for entry:
  only trade-offs that would otherwise be re-litigated.
- **Change log:** stakeholder-facing, so release notes can be built from it.
- **Plain-language product explanation grows as you build** (a "how it works" doc + FAQ
  candidates), so client-facing material never starts from zero.

## Pending-work hygiene

Exactly one home per item, across three lists:

1. **Remaining work** — committed, ordered.
2. **Deferred ideas** — may build later.
3. **Out of scope** — decided never; do not re-raise without explicit human say-so.

When a decision defers or rejects something, file it the same session. For Abbey's
portfolio, human-task capture goes to Workflowy (one node per project, For Claude / For
Abbey sublists) — never a second tracker.
