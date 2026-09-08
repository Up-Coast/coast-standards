# Documentation, git, and process

## Git

- **Commit per task, not per session.** Each commit is one completed, tested task with a
  message that names it. [check: process]
- **Every commit gets pushed — same session, no exceptions.** If the push is refused,
  fetch, reconcile, push. Never leave work only on one machine.
  [check: session:unpushed-at-stop]
- **Repos are private in the owner's organization** unless decided otherwise; secret-scan
  before the first push of any repo. [check: process]
- **Worktrees: fine when a person or session manages them; not in shipped software.**
  (20 Aug 2026, scoping the earlier blanket guidance in this file.)
  - **A development session may use worktrees** for its own parallel work — a Claude Code
    session, or you at the terminal. Whoever creates them is present to clean them up, so
    the disk risk is bounded and visible.
  - **Software shipped to someone else must not leave worktrees on their machine.** A
    product that creates a full extra copy per branch has to clean up on *every* ending, not
    just the happy ones — paused, blocked, crashed, and walked-away work all leave copies
    behind, invisibly, until a non-technical user's disk fills with something they can't
    find. Unless the cleanup story is airtight, use one checkout and switch branches.
  - **When work has to be parked mid-stream, commit it to its own branch first**, then
    switch; resume by checking that branch back out. The reasoning: without a foolproof
    way of managing the space worktrees might eat on someone's computer, worktree use is
    removed and one branch at a time is enforced; a paused ticket gets a commit, and the
    local environment moves to a new branch.
  - Keep `main` releasable either way. [check: process]
- **Protected main where the platform allows it:** PR required, review required, status
  checks required, no force-push, no deletion. [check: tool:gh-ruleset]

## Nothing is pushed unverified (2026-09-01)

- **The full gate battery runs locally before every push**: build, the
  complete test suite, the linter, the formatter in check mode, and every
  deterministic check script the repository's CI runs. A failure stays
  local and is fixed before anything leaves the machine.
  [check: session:no-verify]
- **CI confirms; it never discovers.** A CI failure on a pushed commit is a
  process defect, not a normal event. Origin: on one Coast walk a single
  feature was pushed 15 times against 21 CI check failures for the same
  seven files — each push a paid agent turn to learn what a local run
  would have said in seconds. Pushing and waiting for CI to say it is wrong
  is an inefficient and costly habit. [check: process]
- **One implementation of each check, run in both places.** The script CI
  runs IS the check; the local battery invokes that same script. A
  re-implementation of a CI check in another language (a "mirror") is a
  second source of truth and is forbidden — it is how a local check came
  to pass while CI refused the same tree. [check: process]
- The same battery is installed as the repository's commit hook so a human
  contributor meets the same refusal an agent does.

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
  [BuilderOS build-loop; check: process]

## Documentation

- **Docs ship WITH the feature, not after.** A customer's QA may need to see the
  documentation before the product is released. [check: process]
- **Prefer diagrams over prose sprawl.** Agents overproduce markdown; too many docs cause
  agents to read the wrong ones. Every new class/module of consequence gets its diagram;
  system/flow diagrams are updated in place. Keeping your own diagrams correct needs no
  permission — do it in the same session and say so. [check: process]
- **One predictably-named document per subject.** "Does it already exist?" must be a
  deterministic name lookup, forcing edit-not-create. No ad-hoc throwaway docs. Documents
  are edited, not deleted-and-recreated. [check: process]
- **Decision log:** structured entries (decision, rationale, date, scope), two tiers —
  global/architectural (small, always loaded) and local (feature-scoped). Bar for entry:
  only trade-offs that would otherwise be re-litigated. [check: process]
- **Change log:** stakeholder-facing, so release notes can be built from it.
  [check: process]
- **Plain-language product explanation grows as you build** (a "how it works" doc + FAQ
  candidates), so client-facing material never starts from zero.
  [check: process]

## Pending-work hygiene

Exactly one home per item, across three lists:

1. **Remaining work** — committed, ordered.
2. **Deferred ideas** — may build later.
3. **Out of scope** — decided never; do not re-raise without explicit human say-so.

When a decision defers or rejects something, file it the same session. Human-task capture
goes to the project's tracker (one node per project, with an agent list and an owner
list) — never a second tracker. [check: process]

## Commit and PR cadence for agent-built work

- **Commit at every step boundary**, not only at the end of a task — after the plan is
  agreed, after generated artifacts land, after tests, after implementation. (Why: the plan
  is then known for certain and the built result can be compared against it, and PR merges
  at each boundary make a clean audit trail.) [check: process]
- **Two PRs per feature: the plan merges before the implementation opens.** The agreement is
  in the repository's history before any code exists, so the built result can be diffed
  against what was approved. [check: process]
- **External working-tree drift gets its own commit.** Files moved or deleted between
  sessions are usually the human's own parallel work. Commit the drift on its own, describe
  it factually, mention it once, and **never auto-restore deleted files** — deletion is
  usually intentional. [check: process]
- **Never run git against a network or FUSE-mounted working copy** (Cowork/sandbox mounts) —
  it corrupts index locks. Work against a local clone. Backup means *pull, merge, push* —
  never a clone-and-rsync scheme. [check: process]
- **Secret-scan before a first push**, full history. Genuinely sensitive tracked material
  (server keys, `.p8`/`.p12`, `.env`) aborts the push and gets reported; documented
  client-safe public/anon SDK keys do not block a push to a private repo.
  [check: scan:secret-literal]

## Reviews are real reviews

- Review happens through the platform's own review machinery — comments on the PR, not a
  side channel. **The reviewer decides what is blocking**, not the author.
- The author addresses and resolves threads; **a blocking item clears only by the reviewer's
  re-approval.** Branch protection requires conversations resolved.
- **Everything a verdict cites is mechanically verified to exist** — files, components, and
  rule ids named in a review are checked programmatically, so a review cannot cite something
  imaginary. Reviewer outcomes are logged over time, so a reviewer that is consistently
  wrong can be found and adjusted. [check: process]
- When only one model provider is available, a cross-provider double review falls back to a
  different model in the same family, **and the review record discloses the same-family
  bias.**

## Documentation is generated, not written, where it describes code

- **The API reference is generated from the code** — every public type and function with its
  signature, doc comment, and parameters — and regenerated on every check run, so it cannot
  drift. Class diagrams likewise. [check: process]
- **Generated docs are a review input.** A reviewer who reads a generated doc and finds it
  doesn't describe something sensible files that as a code smell: the docs can't lie about
  the code, so a doc that reads wrong means the code is wrong. [check: process]
- **Four documents every codebase keeps**, because agents and humans both fail without them:
  a **module map** (every module, its one-line responsibility, its allowed dependencies —
  the first thing to read before planning), a **glossary and naming conventions** file (so
  every contributor uses the same domain words), a **docs manifest** (which documents exist
  and when to read which — the cure for reading the wrong document), and a **feature-flag
  registry** (which flags exist, their state, owner, and expiry — stale flags rot the
  code). [check: process]
- **Documents are created only in defined types, and documents are never deleted.** Agents
  left to invent documents overproduce throwaway files, and a pile of near-duplicate
  documents makes the next reader skim headings and get it wrong. Edit the existing document
  for its subject. (Also: don't couple tooling to Markdown specifically — the format may be
  replaced.) [check: process]
