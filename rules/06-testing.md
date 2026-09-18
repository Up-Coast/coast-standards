# Testing

The floor below always applies. The depth of the other test types scales with the project's risk tier. No safety check can ever be switched off.

## The floor (always required)

- **TDD:** write the failing test first, then the code. Run the relevant tests before and after every work session. Keep the full suite passing before every commit that touches shared files. [check: process]
- **Unit tests: every function has one.** [check: review]
- **Every acceptance criterion has ≥1 automated test, and each test states which criterion it verifies.** [check: scan:test-criterion-tag]
- **Never weaken a test to make it pass. Never mark a failing task complete. Never start the next task with the app broken.** [check: scan:test-weakened]
- **Merge-gating tests are hermetic** — they run without live external services. Tests that use live services run separately, behind an opt-in flag, and never block a merge. [check: scan:hermetic-test]

## What counts as coverage

A test proves behavior: it fails when the behavior it names is broken. The worst outcome is a test that passes when it should fail. Reject these patterns in review:

- Tautologies: asserting a value against itself, or against a constant copied from the implementation.
- Asserting only that no error was thrown.
- Testing a stub or mock instead of the behavior.
- Assertions so weak that any implementation passes.
- Redundant volume: cosmetic input variations on a path that is already tested add noise, not coverage.

Tests are reviewed by someone or something that did not write them. The question is not whether they pass, but whether passing means anything. A reviewer of tests never edits them.
[check: review]

## Test-first for existing code

Before changing code, check that tests exist for everything the change touches **or affects**, including downstream code that its data flows into. If they do not exist, write them for the existing code first. Then start the feature. [check: process]

## Required test types per feature (risk/cost dials)

- **Negative tests:** assert that things that should fail still fail. Keep a visible list of negative tests so anyone can audit what the product rejects. (Example of a miss: nobody checked that the phone field rejects letters.) [check: review]
- **Data-variation tests, exhaustive** wherever the input is user text: ALL CAPS, leading, trailing and multiple spaces, punctuation, empty, very long. AI-written tests are cheap, so cover every edge case. [check: review]
- **Domain-invariant tests** generated from the project's rules doc. Examples: totals equal the sum of their parts; a record cannot be in two exclusive states; a tenant can never read another tenant's data. [check: review]
- **Localization robustness:** long strings, pseudo-localization, and right-to-left layout when in scope. The UI must survive real translations. Dates and numbers are formatted correctly for each locale. [check: review]
- **Accessibility tests:** labels are present, large text does not clip, contrast is sufficient, touch targets are big enough. [check: review]
- **Interaction tests**, including abandon-and-return flows: leave a screen mid-action, come back, and check what should and should not have been saved. [check: review]
- **Client-side performance** (launch time, scroll stutter, memory leaks) and **low-connectivity behavior** for everything that uses the network. [check: review]
- **Security tests** on code flagged as sensitive: abuse and load, injection (including prompt injection wherever a model reads external text), and authorization (every endpoint rejects the wrong tenant or role). [check: review]
- **Migration forward/backward tests** whenever the schema changes. [check: review]

## Verification discipline

- Verify in live mode against the real data path. Demo and fixture modes make broken screens look finished.
- A task is not done until its tracking record says so, with a verdict. A claim in a report is not the record.
- Comparing screenshots against the design is a depth setting that scales with risk. A full, honest walk through the whole product is always required. [check: process]

## Every failure path gets a test

A feature that calls a model, a network service or a file needs one test for each outcome the real thing can return: the answer, the refusal, the timeout, the empty reply, and the answer in the wrong shape. Each test asserts two things: what the person sees, in the product's own words, and what they can do next.

A flow tested only against a stand-in that always answers has not been tested. The stand-in must be able to produce every outcome (see "A stand-in must fail the way production fails").

Why: error handlers that no test reaches can leave a person stuck in a loop with no way forward and no explanation on screen.
[check: review]

## Done means used

A screen or flow task is closed only after its builder has used it in the built product the way a person would. Use the screens, buttons and links, never the code or a debug route. Record what you saw: save captures to disk, and read the stored data after each action.

A screenshot of the pane you just built is not enough. The window around the pane, its title, its settings, navigating in and out, discarding, and relaunching are part of the flow, and you must use them too.

Why: defects often sit outside the pane that the tests and screenshots looked at, such as the wrong title, a relaunch that opens something else, or a discard that leaves the person inside deleted data. [check: process, review]

## The build result is the truth — never an agent's word for it

An agent does not know whether its code compiles unless something actually ran the build. Never accept "it compiles" or "tests pass" as a claim. Require proof that a build or test step *actually ran* and passed, checked by a step that cannot be skipped. **The build result is the truth; the author's word is not.** Anything that must happen lives in a hook, a script or CI, never in a written reminder. [check: process]

## Changing a test is a decision made before the work, not during it

**This rule protects the integrity of the codebase, not the tests themselves.** Tests do sometimes need to change. When the required behavior really changes, the test for the old behavior is wrong, and changing it is correct.

This rule prevents two failures. The first is making a failing test pass by editing the test instead of the code. The second is **twisting the implementation into something convoluted just to avoid touching a test.** Both damage the codebase. Convoluted code written to dodge a test edit is worse than the edit.

So the rule is about *when and by whom* the decision is made:

- **Decide test changes when planning the work, not while fighting a red run.** If the behavior is changing, say so up front and change the test then. The change is then visible and reviewable as part of the plan, not buried in the implementation diff. [check: scan:test-weakened]
- **Mid-implementation, a red test is a question, not a licence.** If the test encodes an assumption that the new behavior makes wrong, stop and raise it. Then change the test on purpose and record why. Never silently weaken or delete a test to make a run pass. [check: process]
- **Every test change states the reason.** "The behavior changed, and here is how" is a reason. "It was failing" is not. [check: scan:test-weakened]
- Writing tests before the work starts is one of the best protections here: any test that needs to change is changed before the work begins. If a function's behavior changes, its test changes with it. Nobody writes convoluted code to avoid editing a test.

## Three nets, each for what only it can catch

Use the expensive net (review) only where judgment is really needed:

- **Structure → a deterministic script.** Schema diffs and symbol graphs: anything in the change that is not on the approved item list fails automatically. [check: context]
- **Behaviour → tests.** Enforced by the rule above. [check: context]
- **Quality and justification → review judgment.** The only net that needs a person or model to judge. [check: context]

## Red main stops everything

When tests fail on the main branch, nobody *starts* new work. Fixing main is the only job until it passes. This applies to breakage from outside (for example, a teammate's push), not just your own merges. [check: process]

## Cadence — verify everything, waste nothing

Quality never drops. The goal is to stop paying for runs that prove nothing.

- Parallel work streams run their own test target while working, and the **full suite once** before their final commit. A serial merge step re-runs the full suite after each merge.
- **Parallel work streams that build the same kind of thing do not run at once.** Either one lands on main before the next is cut, or the pieces both would need are agreed and committed first, in one small serial commit both streams cut from, and each stream's brief names them as the pieces to use. Otherwise each stream writes its own copy, and the duplicate-code check cannot see it: it measures one branch against the baseline, so a copy that exists only on the other branch is invisible until the merge. So the merge of parallel streams is measured before it reaches main — the duplicate-code check runs over the merged tree, not over either branch — and any plan that fans out into parallel streams carries a named "shared pieces first" step. [check: process]
- Sessions working on shared files keep the full suite passing before every commit.
- **One review pass per task, at the end** — not per file, not per commit. [check: process]
- Batch verification: run the full suite once over a batch, not once per merge. Never re-run a suite when nothing has changed since its last run.
- Do not run the test suite when it is not needed, and do not run separately what could be batched and run later. Always test your own work, but do not waste runs.

## Never re-run a proven paid pipeline as routine verification

When a test path costs real money per run, do not re-verify a proven end-to-end path out of habit. Verify with the free suite, a mock run, or records that already exist. A real paid run needs **both** a concrete reason **and** explicit sign-off. A concrete reason is a major change to that subsystem, a new stage, or a live connection that cannot be verified any other way.

A credential that does not work may be deliberate, to prevent spending. Do not chase it as a bug.
[check: process]

## Long runs: watchdog, don't wait

- Before starting a run, know how long a healthy run takes for this project.
- **Never pipe a long run through `tail` alone.** `tail` shows nothing until the run exits, so nobody can tell stuck from slow. Stream output through `tee` to a file and give the person the file path. [check: process]
- Build the test target first. Then run the tests under a **hard timeout** sized to a healthy run. If the timeout fires, the run is hung: kill it, re-run with the hanging suite skipped, and **say in your report that you skipped it.** The pre-push hook enforces the same limit: its test step runs under the time limit in the config (`tests_deadline_seconds`, default 900). A run with no result at the limit is killed with its whole process tree, and the push is refused with an explanation. A push never waits on a hung run. [check: tool:tests-deadline]
- A suite that can hang is a defect with a root cause. Find it. A permanent skip is not a fix.
- A check that reads a rendered bitmap reads a **fixed region or a fixed sample** of it: a row, a band, or a grid of points whose position the layout decides. Never slide a pattern pixel by pixel across a whole render. That costs pixels × pattern size per screen and can take hours in a debug build. [check: review]

## Proving a background run is alive

- The reliable signal is **recent file activity on disk**, such as a transcript or output file being written. A process count is not reliable, because work may run in-process. A launch confirmation is not reliable either.
- After launching anything long-running, set a watchdog that checks for that file activity.
- A dead run's partial work survives on disk. Relaunch it with instructions to review and resume. **Never restart blindly.**
- When someone challenges a status claim, check it again against the primary evidence. Do not just restate it more softly.
[check: process]

## Fixtures the size of the real thing, and pressure past it

A fixture built for convenience only tests the fixture. Test data must match the size, shape and messiness of real data: lists long enough to overflow their container, names long enough to be truncated, and documents written in the industry's words, not the product's own vocabulary.

Also push past real size on purpose: far more items than anyone would have, values at and beyond the declared limits, empty and huge inputs, slow and missing responses. Every surface that shows project data has at least one test at real size and one beyond it.

Why: fixtures that are small, or written in the product's own words by the same person who wrote the code, pass while real data overflows layouts, gets rejected, or is miscounted. When real data breaks something, the fix is better mocks and pressure tests, not blaming the data.
[check: review]

## A stand-in must fail the way production fails

A test double that can only succeed, or fail with a clean error, never tests the paths that break in production. Every stand-in for an external service must be able to return that service's real failure responses, not just success and a clean thrown error. These include a partial denial (for example, a 403 that refuses even to list items), a feature not available on the current plan, an empty but valid answer, and a malformed response.

Why: handling code that exists but that no stand-in can reach ships broken, including bugs caused by the order of checks rather than their logic.

In practice: when writing a stand-in, first list the real service's documented failure responses, and make the double able to return each one. When a live defect is traced to a handler no test reached, teach the stand-in that failure in the same fix. [check: review]

## Testing leaves no mess in anyone's inbox

Work that sends email or triggers notifications cleans up after itself. This covers manual test passes, automated tests, CI jobs and one-off send checks. The owner's inbox is not a test sink, and every test message that lands there is a cost the owner pays.

- Send test mail only to addresses set aside for testing, which a mail filter removes on arrival (for example, fixed plus-addresses that are trashed automatically). The project's instructions list those addresses. Never send to the owner's real address, even once.
- To read a test message, such as a sign-in link, search the place where the filter puts it. Do not change the filter so the message stays visible.
- When a test pass ends, trash anything it sent that got past the filter.
- A test that needs a new address adds that address to the filter first.
- A scheduled job that fails on every run is a defect: fix it, or switch it off with the owner's agreement. Hiding its failure notices is not a fix.
- Before calling an alert or message a live problem, check the project's own records (deploy state, test results) to see whether testing produced it.

Why: a test message looks the same as a real one. A steady stream of them buries the messages that matter and costs the owner attention every time. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
