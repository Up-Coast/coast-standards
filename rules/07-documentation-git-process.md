# Documentation, git, and process

## Git

- **Commit per task, not per session.** Each commit is one completed, tested task with a
  message that names it.
- **Every commit gets pushed — same session, no exceptions.** If the push is refused,
  fetch, reconcile, push. Never leave work only on one machine.
- **Repos are private in the Up-Coast org** unless decided otherwise; secret-scan before
  the first push of any repo.
- **One checkout per project, branch-switched — NOT worktrees.** (Abbey, 20 Aug 2026,
  reversing the earlier worktree guidance in this file.) Worktrees make a full extra copy
  per branch, and cleanup only ever covers the happy paths — paused, blocked, crashed, and
  walked-away work leaves copies behind, invisibly, until a disk fills. Use one checkout and
  switch branches. **When work has to be parked mid-stream, commit it to its own branch
  first**, then switch; resume by checking that branch back out. Her words: *"if we don't
  have a foolproof way of managing the space that these worktrees might eat up on someone's
  computer then we need to... remove worktree useage and enforce one at a time. If a ticket
  is paused, a commit will be made and the local environment will do a git branch and work
  on a new branch."* Reintroducing worktrees for parallel runs is a re-opening of this
  decision — ask her, don't assume it's an implementation detail. Keep `main` releasable.
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

## Commit and PR cadence for agent-built work

- **Commit at every step boundary**, not only at the end of a task — after the plan is
  agreed, after generated artifacts land, after tests, after implementation. (Abbey, on why:
  *"we know for certain what the plan is and can make that comparison"* and *"using PR
  merges like that will make it a very clean audit trail."*)
- **Two PRs per feature: the plan merges before the implementation opens.** The agreement is
  in the repository's history before any code exists, so the built result can be diffed
  against what was approved.
- **External working-tree drift gets its own commit.** Files moved or deleted between
  sessions are usually the human's own parallel work. Commit the drift on its own, describe
  it factually, mention it once, and **never auto-restore deleted files** — deletion is
  usually intentional.
- **Never run git against a network or FUSE-mounted working copy** (Cowork/sandbox mounts) —
  it corrupts index locks. Work against a local clone. Backup means *pull, merge, push* —
  never a clone-and-rsync scheme.
- **Secret-scan before a first push**, full history. Genuinely sensitive tracked material
  (server keys, `.p8`/`.p12`, `.env`) aborts the push and gets reported; documented
  client-safe public/anon SDK keys do not block a push to a private repo.

## Reviews are real reviews

- Review happens through the platform's own review machinery — comments on the PR, not a
  side channel. **The reviewer decides what is blocking**, not the author.
- The author addresses and resolves threads; **a blocking item clears only by the reviewer's
  re-approval.** Branch protection requires conversations resolved.
- **Everything a verdict cites is mechanically verified to exist** — files, components, and
  rule ids named in a review are checked programmatically, so a review cannot cite something
  imaginary. Reviewer outcomes are logged over time, so a reviewer that is consistently
  wrong can be found and adjusted.
- When only one model provider is available, a cross-provider double review falls back to a
  different model in the same family, **and the review record discloses the same-family
  bias.**

## Documentation is generated, not written, where it describes code

- **The API reference is generated from the code** — every public type and function with its
  signature, doc comment, and parameters — and regenerated on every check run, so it cannot
  drift. Class diagrams likewise.
- **Generated docs are a review input.** A reviewer who reads a generated doc and finds it
  doesn't describe something sensible files that as a code smell: the docs can't lie about
  the code, so a doc that reads wrong means the code is wrong.
- **Four documents every codebase keeps**, because agents and humans both fail without them:
  a **module map** (every module, its one-line responsibility, its allowed dependencies —
  the first thing to read before planning), a **glossary and naming conventions** file (so
  every contributor uses the same domain words), a **docs manifest** (which documents exist
  and when to read which — the cure for reading the wrong document), and a **feature-flag
  registry** (which flags exist, their state, owner, and expiry — *"or stale flags rot the
  code"*).
- **Documents are created only in defined types, and documents are never deleted.** Agents
  left to invent documents overproduce throwaway files, and a pile of near-duplicate
  documents makes the next reader skim headings and get it wrong. Edit the existing document
  for its subject. (Also: don't couple tooling to Markdown specifically — the format may be
  replaced.)
