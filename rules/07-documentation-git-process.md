# Documentation, git, and process

## Git

- **Commit per task, not per session.** Each commit is one finished, tested task, and its message names that task. [check: process]
- **Every commit gets pushed — same session, no exceptions.** If the push is refused, fetch, reconcile and push again. Never leave work only on one machine. [check: session:unpushed-at-stop]
- **Repos are private in the owner's organization** unless the owner decides otherwise. Scan for secrets before the first push of any repo. [check: process]
- **Worktrees: fine when a person or session manages them; not in shipped software.**
  - **A development session may use worktrees** for its own parallel work, whether that is an AI coding session or a person at the terminal. Whoever creates them is there to clean them up, so the disk use stays limited and visible.
  - **Software shipped to someone else must not leave worktrees on their machine.** A product that makes a full extra copy per branch must clean up after *every* ending, not only successful ones. Paused, blocked, crashed and abandoned work all leave hidden copies behind, until a non-technical user's disk fills with files they cannot find. Unless cleanup is fully reliable, use one checkout and switch branches.
  - **When work has to be parked mid-stream, commit it to its own branch first**, then switch branches. To resume, check that branch out again. Without a reliable way to manage the disk space worktrees use, shipped software works on one branch at a time: a paused ticket gets a commit, and the local checkout moves to a new branch.
  - Keep `main` releasable either way. [check: process]
- **Protected main where the platform allows it:** pull request required, review required, status checks required, no force-push, no deletion. [check: tool:gh-ruleset]
- **Versions and build numbers.** The version lives in one file and names a release. Raise it when a release is cut, never on an ordinary merge: patch for fixes, minor for new features, major for a change that breaks existing users. Each version has a dated section in the change log. Every build gets a new build number from one source, always increasing and never reused, and records the commit it was built from. A repository that other projects install straight from git (a library, a rules or tooling repository) is the exception: every merge to main is a release there, so every merge raises the version and is tagged. [check: review]

## Nothing is pushed unverified (2026-09-01)

- **The gate battery runs locally before every push, on what the push changed**: the pre-push hook runs the build, the tests, the linter, the formatter in check mode, and every deterministic check script that the repository's CI runs. A failure stays on the machine and is fixed before anything is pushed. The hook first looks at what changed:
  - A push of only documents and plans runs no build, tests, linter or formatter, because there is nothing for them to check.
  - A push that changed code runs the linter and formatter on the changed files, rebuilds the affected modules, and runs the tests that depend on them. (See rules/06: never re-run a suite when nothing it covers has changed.)
  - A push that changed the checks themselves, their configuration, or the package manifest runs everything.
  - To run every check regardless, set `SCOPE=all` with the project's environment prefix (for example `COAST_SCOPE=all`). CI does this. [check: session:no-verify]
- **CI confirms; it never discovers.** A CI failure on a pushed commit is a process defect, not a normal event. Pushing and waiting for CI to report a problem is slow and costly, because each push can cost a paid agent turn to learn what a local run would show in seconds. [check: process]
- **One implementation of each check, run in both places.** The script CI runs is the check, and the local pre-push hook calls that same script. Do not rewrite a CI check in another language (a "mirror"). A mirror is a second source of truth, and it lets a local check pass while CI refuses the same code. [check: process]
- The same checks are installed as the repository's commit hook, so a human contributor is refused in the same way an agent is.

## Pull requests

- The ticket or task content goes WITH the change, as a committed file with a predictable name, not only pasted into the pull request description. That way checks can find it reliably.
- Before requesting review, check the pull request yourself: Were the rules followed? Is UI code abstracted (no inline strings or styles)? Were the architecture approvals honored? Does each test state its criterion?
- Attach screenshots of designed features to the pull request. Flag changes to sensitive code; they get the heavier review.
- A rejection must say exactly what the problem is and what a compliant version looks like, so the fix does not change unrelated things. A bare approve or reject is not valid: a review lists what was checked, whether it passed or failed, and cites real files and rules.
- If you find work that no task covers, raise it and propose it as a task. Never build it silently. If a finding contradicts the task or spec, the spec wins; flag the disagreement.
- Work that skipped review or testing is unfinished. Nothing ships because "it compiles."
  [BuilderOS build-loop; check: process]

## Documentation

- **Docs ship WITH the feature, not after.** A customer's QA team may need to read the documentation before the product is released. [check: process]
- **Prefer diagrams over prose sprawl.** Agents write too much Markdown, and too many documents make agents read the wrong ones. Every significant new class or module gets a diagram. Update system and flow diagrams in place. You do not need permission to correct your own diagrams: do it in the same session and say that you did. [check: process]
- **One predictably-named document per subject.** Checking whether a document already exists must be a simple lookup by name, so that you edit it instead of creating a new one. No one-off throwaway documents. Edit documents; do not delete and recreate them. [check: process]
- **Decision log:** structured entries (decision, reason, date, scope) in two levels: global or architectural decisions (a small set, always loaded) and local, feature-level decisions. Only log trade-offs that would otherwise be argued again. [check: process]
- **Change log:** written for stakeholders, so release notes can be built from it. [check: process]
- **Plain-language product explanation grows as you build**: a "how it works" document plus candidate FAQ entries, so client-facing material never starts from nothing. [check: process]

## Pending-work hygiene

Each item lives in exactly one of three lists:

1. **Remaining work**: committed and in order.
2. **Deferred ideas**: may be built later.
3. **Out of scope**: decided against. Do not raise it again without a person's explicit approval.

When a decision defers or rejects something, file it in the same session. Tasks for people go in the project's tracker (one entry per project, with a list for the agent and a list for the owner). Never use a second tracker. [check: process]

## Commit and PR cadence for agent-built work

- **Commit at every step boundary**, not only at the end of a task: after the plan is agreed, after generated files are added, after the tests, and after the implementation. This fixes the plan in history so the result can be compared against it, and merging pull requests at each boundary leaves a clean audit trail. [check: process]
- **Two PRs per feature: the plan merges before the implementation opens.** The approved plan is in the repository's history before any code exists, so the result can be compared against what was approved. [check: process]
- **External working-tree drift gets its own commit.** Files moved or deleted between sessions are usually a person's own parallel work. Commit those changes on their own, describe them factually, and mention them once. **Never restore deleted files automatically**, because the deletion is usually intentional. [check: process]
- **Never run git against a network or FUSE-mounted working copy** (for example, a sandbox mount). It corrupts git's index locks. Work in a local clone. A backup means *pull, merge, push*, never a clone-and-rsync scheme. [check: process]
- **Secret-scan before a first push**, across the full history. Truly sensitive tracked files (server keys, `.p8`/`.p12` files, `.env`) stop the push and are reported. Public or anonymous SDK keys that are documented as safe for clients do not block a push to a private repo. [check: scan:secret-literal]

## Reviews are real reviews

- Reviews happen through the platform's own review tools, as comments on the pull request, not in a separate channel. **The reviewer decides what is blocking**, not the author.
- The author addresses and resolves each thread. **A blocking item is cleared only when the reviewer approves again.** Branch protection requires all conversations to be resolved.
- **Everything a verdict cites is mechanically verified to exist.** Files, components and rule ids named in a review are checked by code, so a review cannot cite something that does not exist. Reviewer outcomes are logged over time, so a reviewer that is often wrong can be found and adjusted. [check: process]
- When only one model provider is available, a double review that would use two providers uses a different model from the same family instead, **and the review record states that both models share the same family's bias.**

## Documentation is generated, not written, where it describes code

- **The API reference is generated from the code**: every public type and function, with its signature, doc comment and parameters. It is regenerated on every check run, so it cannot fall out of date. The same applies to class diagrams. [check: process]
- **Generated docs are a review input.** If a generated doc does not describe something sensible, the reviewer files it as a code smell. The generated docs reflect the code exactly, so a doc that reads wrong means the code is wrong. [check: process]
- **Four documents every codebase keeps**, because both agents and people fail without them:
  - a **module map**: every module, its one-line responsibility and its allowed dependencies. Read it first, before planning.
  - a **glossary and naming conventions** file, so every contributor uses the same domain words.
  - a **docs manifest**: which documents exist and when to read each one, so nobody reads the wrong document.
  - a **feature-flag registry**: which flags exist, their state, owner and expiry date. Stale flags make the code rot. [check: process]
- **Documents are created only in defined types, and documents are never deleted.** Agents left to invent documents create many throwaway files. A pile of near-duplicate documents makes the next reader skim headings and get things wrong. Edit the existing document for the subject. Also, do not tie tooling to Markdown specifically, because the format may change. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
