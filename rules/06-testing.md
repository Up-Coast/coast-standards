# Testing

Read this when a task writes, changes or runs tests. The floor always applies; other types scale with risk. Never switch off a safety check.

## The floor (always required)

- **TDD:** failing test first, then code. Run relevant tests before and after each session; full suite green before any commit to shared files. [check: process]
- **Unit tests: every function has one.** [check: review]
- **Every acceptance criterion has ≥1 automated test, and each test states which criterion it verifies.** [check: scan:test-criterion-tag]
- **Never weaken a test to make it pass. Never mark a failing task complete. Never start the next task with the app broken.** [check: scan:test-weakened]
- **Merge-gating tests are hermetic**: no live services. Live-service tests sit behind an opt-in flag and never block a merge. [check: scan:hermetic-test]

## What counts as coverage

A test fails when its behaviour breaks. Reject tautologies (self or copied-constant checks), "no error" as sole assertion, testing a mock, assertions any code passes, cosmetic variants of a tested path. A non-author reviews tests for meaning, never editing them. [check: review]

## Test-first for existing code

Before a change, write missing tests for existing code it touches **or affects** downstream. [check: process]

## Required test types per feature (risk/cost dials)

- **Negative tests:** what should fail still fails; keep a visible list. [check: review]
- **Data-variation tests, exhaustive** on user text: ALL CAPS, leading, trailing and multiple spaces, punctuation, empty, very long. [check: review]
- **Domain-invariant tests** generated from the project's rules doc. [check: review]
- **Localization robustness:** long strings, pseudo-localization, right-to-left when in scope, locale-correct dates and numbers. [check: review]
- **Accessibility tests:** labels, large text without clipping, contrast, touch target size. [check: review]
- **Interaction tests**, including leaving mid-action and returning to check what was saved. [check: review]
- **Client-side performance** (launch time, scroll stutter, memory leaks) and low connectivity for anything networked. [check: review]
- **Security tests** on sensitive code: abuse and load, injection (prompt injection where a model reads external text), wrong tenant or role refused at every endpoint. [check: review]
- **Migration forward/backward tests** on every schema change. [check: review]

## Verification discipline

Verify live on the real data path, never in demo or fixture mode. A task is done only when its tracking record gives a verdict. Design screenshot comparison scales with risk; a full product walk is always required. [check: process]

## Every failure path gets a test

Anything calling a model, network service or file has one test per outcome: answer, refusal, timeout, empty, wrong shape. Each asserts what the person sees, in product words, and what they can do next. [check: review]

## Done means used

Close a screen or flow task only after its builder uses it through the built product's UI, never code or a debug route, saving captures and reading stored data after each action. Include window, title, settings, navigation, discard and relaunch. [check: process, review]

## The build result is the truth — never an agent's word for it

Require proof, from an unskippable step, that the build or tests ran and passed; never a claim. What must happen lives in a hook, script or CI, not a reminder. [check: process]

## Changing a test is a decision made before the work, not during it

Never contort code to avoid a needed test edit.

- **Decide test changes when planning the work, not while fighting a red run.** [check: scan:test-weakened]
- **Mid-implementation, a red test is a question, not a licence.** Stop and raise it; change it on purpose and record why. [check: process]
- **Every test change states the reason.** "It was failing" is not one. [check: scan:test-weakened]

## Three nets, each for what only it can catch

- **Structure → a deterministic script.** Schema diffs and symbol graphs fail anything unapproved. [check: context]
- **Behaviour → tests.** [check: context]
- **Quality and justification → review judgment.** [check: context]

## Red main stops everything

When main fails, nobody starts new work until it passes, whoever broke it. [check: process]

## Cadence — verify everything, waste nothing

- Streams run their own test target while working and the **full suite once** before their final commit; a serial merge step re-runs it after each merge.
- **Parallel work streams that build the same kind of thing do not run at once.** One lands first, or the shared pieces go in one small serial commit both cut from, named in each brief. Run the duplicate-code check on the merged tree before main. Any fan-out plan has a "shared pieces first" step. [check: process]
- **No more than two background agents run at once.** Check free memory before starting a second; below about 40% free, run one at a time. A type check and a full test run each use gigabytes, so the cap protects the machine every session shares. [check: process]
- **A background builder tests only what it changed.** It runs the tests of the files it touched, by path, and never the full suite or a whole-project type check. The coordinator runs one type check and one full suite on the merged work. [check: process]
- **One review pass per task, at the end**: not per file or commit. [check: process]
- Run the full suite once per batch, never on unchanged code.
- **After a failure, re-run only what failed.** Re-run the failures plus tests for code changed since. A push or merge gate records results per commit and runs fast checks, last failures and tests touched since the last pass; it never skips a last failure. The full suite runs once per integration, never per feature or push. [check: process]
- **Parallel sessions do not share one mutable test database without coordination.** Give each stream its own data or schema, or sequence full runs and record unmerged migrations on the shared one. [check: process]

## Never re-run a proven paid pipeline as routine verification

Re-verify with the free suite, a mock run or existing records. A paid run needs **both** a concrete reason (major subsystem change, new stage, live connection nothing else verifies) **and** explicit sign-off. A dead credential may be deliberate; do not chase it. [check: process]

## Long runs: watchdog, don't wait

- Know a healthy run's length before starting.
- **Never pipe a long run through `tail` alone.** `tee` output to a file and give the person its path. [check: process]
- Build first, then test under a **hard timeout** sized to a healthy run. If it fires, kill it, re-run without the hanging suite and **say in your report that you skipped it.** The pre-push test step kills the process tree at `tests_deadline_seconds` (default 900) and refuses the push, saying why. [check: tool:tests-deadline]
- A suite that can hang is a defect; find the root cause, never skip it permanently.
- Bitmap checks read a **fixed region or a fixed sample** placed by the layout, never a pattern slid pixel by pixel across a render. [check: review]

## Proving a background run is alive

Prove it by **recent file activity on disk**, never process count or launch confirmation; watchdog that. Relaunch a dead run to review and resume its saved work; **never restart blindly.** Re-check a challenged status claim against primary evidence. [check: process]

## Fixtures the size of the real thing, and pressure past it

Test data matches real size, shape and mess: overflowing lists, truncating names, industry wording. Also go beyond: far more items, values past limits, empty and huge inputs, slow and missing responses. Every data surface is tested at and beyond real size. Fix mocks, not data, when real data breaks something. [check: review]

## A stand-in must fail the way production fails

Every external-service stand-in can return the service's documented failures, not only success and a clean error: partial denial (a 403 even on listing), feature not on the plan, empty valid answer, malformed response. When a live defect hits an unreached handler, teach the stand-in that failure in the same fix. [check: review]

## Testing leaves no mess in anyone's inbox

- Send only to the project's listed test addresses, which a filter removes on arrival; never the owner's real address.
- Read test mail where the filter puts it; never change the filter. Add a new address to the filter before use.
- Trash anything that got past the filter when the pass ends.
- A scheduled job failing every run is a defect: fix it or switch it off with the owner's agreement, never hide its notices.
- Check the project's records (deploy state, test results) before calling an alert a live problem. [check: process]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
