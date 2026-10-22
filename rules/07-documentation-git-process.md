# Documentation, git, and process

Read this when a task commits, pushes, reviews or writes docs.

## Git

- **Commit per task, not per session.** Each is one finished, tested task, named in its message. [check: process]
- **Every commit gets pushed — same session, no exceptions.** If refused, fetch, reconcile, retry. A background builder's commits are pushed by the integrator in that same session (next rules). [check: session:unpushed-at-stop]
- **Repos are private in the owner's organization** unless the owner says otherwise. Secret-scan all history before a first push: server keys, `.p8`/`.p12` and `.env` files block it and are reported; client-safe SDK keys do not. [check: process, scan:secret-literal]
- **Worktrees: fine when a person or session manages them; not in shipped software.** The creator cleans them up. Shipped software uses one checkout unless cleanup survives every ending (pause, block, crash, abandon). Park work as a commit on its branch; keep `main` releasable. [check: process]
- **Each background agent works in its own worktree on its own branch, commits locally and never pushes, deploys or migrates.** The owner may ask for the branches to stay local until the work is done. [check: process]
- **One integrator ships.** It merges every branch, runs one type check and one full test run on the merged work, then one deploy, one database migration, one merge to main and one push. Builders never ship; a failure goes back to the builder whose branch caused it. [check: process]
- **Remove a worktree as soon as its branch is merged.** The branch stays until main has it. Idle worktrees cost disk and memory on a shared machine. [check: process]
- **Protected main where the platform allows it:** pull request required, review required, status checks required, no force-push, no deletion. [check: tool:gh-ruleset]
- **Versions and build numbers.** One file holds the version, raised only per release (patch fix, minor feature, major breaking) with a dated change-log section. Builds get an increasing number from one source and record their commit. Git-installed repos raise and tag the version every merge to main. [check: review]

## Nothing is pushed unverified (2026-09-01)

- **The gate battery runs locally before every push, on what the push changed**: build, tests, linter, formatter check, every CI script; failures block the push. Docs-only pushes run none; code pushes cover changed files and affected modules; changed checks, config or manifest run all, as does prefixed `SCOPE=all` (e.g. `COAST_SCOPE=all`, set by CI). The commit hook runs them too. [check: session:no-verify]
- **CI confirms; it never discovers.** A CI failure on a pushed commit is a process defect. Hosted CI is optional, never the only check; the local hook is the gate. [check: process]
- **One implementation of each check, run in both places.** The hook calls the script CI runs; never write a local "mirror". [check: process]
- **Know what a hosted run costs before scheduling one.** Use the smallest runner, prefer Linux to macOS, cancel superseded runs, skip changes that cannot break the build. Install shipped workflows only on request. [check: process]

## Pull requests

- Commit the task text with the change, in a predictably named file.
- Self-check before review: rules followed, no inline UI strings or styles, architecture approvals honoured, each test states its criterion.
- Attach screenshots of designed features. Flag sensitive code for heavier review.
- A rejection names the problem and a compliant version. A review lists each check, pass or fail, citing real files and rules.
- Propose uncovered work as a task; never build it silently. When a finding contradicts the spec, the spec wins; flag it.
- Work that skipped review or testing is unfinished. [check: process]

## Documentation

- **Docs ship WITH the feature, not after.** When a behaviour, command, flag, setting, file location or message changes, update every doc describing it in the same change: README, guides, references, troubleshooting, diagrams, change log. [check: process, review]
- **Documents follow the project's writing instructions.** Use `write-developer-documentation` and `write-a-guide` in `.claude/skills/`, unless the project replaced them. [check: review]
- **Prefer diagrams over prose sprawl.** Diagram every significant new class or module. Update diagrams in place; fix your own unasked and say so. [check: process]
- **One predictably-named document per subject.** Create only defined types. Edit the subject's document, found by name; never make one-offs, delete or recreate. Never tie tooling to Markdown. [check: process]
- **Decision log:** decision, reason, date, scope; global (few, always loaded) and feature-level. Log only trade-offs that would be re-argued. [check: process]
- **Change log:** written for stakeholders, as the source of release notes. [check: process]
- **Plain-language product explanation grows as you build**: a "how it works" doc and candidate FAQ entries. [check: process]

## Pending-work hygiene

Each item is in exactly one list:

1. **Remaining work**: committed and in order.
2. **Deferred ideas**: may be built later.
3. **Out of scope**: decided against. Never re-raise without a person's explicit approval.

File a deferral or rejection in the deciding session. People's tasks go in the project's one tracker entry, with agent and owner lists. Never use a second tracker. [check: process]

## Commit and PR cadence for agent-built work

- **Commit at every step boundary**: plan agreed, generated files, tests, implementation. [check: process]
- **Two PRs per feature: the plan merges before the implementation opens.** [check: process]
- **External working-tree drift gets its own commit.** Describe it factually; mention it once. **Never restore deleted files automatically.** [check: process]
- **Never run git against a network or FUSE-mounted working copy**, such as a sandbox mount. Use a local clone; back up by pull, merge, push. [check: process]

## Reviews are real reviews

- Review in pull request comments; the reviewer, not the author, decides what blocks.
- The author resolves each thread; only the reviewer's re-approval clears a blocker. Branch protection requires resolved conversations.
- **Everything a verdict cites is mechanically verified to exist.** Code checks each cited file, component and rule id. Logged outcomes expose unreliable reviewers. [check: process]
- With one provider, a two-provider review uses another model of that family and records the shared bias.

## Documentation is generated, not written, where it describes code

- **The API reference is generated from the code**: public types and functions with signature, doc comment and parameters, plus class diagrams, regenerated each check run. [check: process]
- **Generated docs are a review input.** One that reads wrong is a code smell to file. [check: process]
- **Four documents every codebase keeps**: a **module map** (each module's job and allowed dependencies; read before planning), a **glossary and naming conventions** file, a **docs manifest** (each doc and when to read it), a **feature-flag registry** (state, owner, expiry). [check: process]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
