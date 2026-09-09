# Testing

The floor is non-negotiable; the depth dials scale with the project's risk tier. No safety
gate is ever toggleable.

## The floor (always required)

- **TDD:** write the failing test first, then the code. Run the relevant suite before and
  after every work session; keep the full suite green before every commit on shared files.
  [check: process]
- **Unit tests: every function has one.** [check: review]
- **Every acceptance criterion has ≥1 automated test, and each test states which criterion
  it verifies.** [check: scan:test-criterion-tag]
- **Never weaken a test to make it pass. Never mark a failing task complete. Never start
  the next task with the app broken.** [check: scan:test-weakened]
- **Merge-gating tests are hermetic** — they run without live external services; live-service
  tests run separately (opt-in flag) and never block a merge.
  [check: scan:hermetic-test]

## What counts as coverage

A test proves behavior: it fails when the behavior it names is broken. The worst outcome is
a false-passing test. Known false-passing patterns to reject in review:

- Tautologies — asserting a value against itself or a constant copied from the
  implementation.
- Asserting only that no error was thrown.
- Testing a stub or mock instead of the behavior.
- Assertions so weak any implementation passes.
- Redundant volume — cosmetic input variations on an already-pinned path add noise, not
  coverage.

Tests are reviewed by something that didn't write them — passing is not the question;
whether passing means anything is. Reviewers of tests never edit them.
[check: review]

## Test-first for existing code

Before changing code, check that tests exist for everything the change touches **or
affects** — including downstream code its data flows into. If they don't exist, write them
for the existing code first, then start the feature. [check: process]

## Required test types per feature (risk/cost dials)

- **Negative tests:** assert that things that should fail still fail. Keep a visible
  negative-coverage registry so "what we reject" is auditable. (Classic miss: nobody checked
  the phone field rejects letters.) [check: review]
- **Data-variation tests, exhaustive** where input is user text: ALL CAPS, leading/trailing/
  multiple spaces, punctuation, empty, very long. AI testing is cheap — catch every edge.
  [check: review]
- **Domain-invariant tests** generated from the project's rules doc: totals equal the sum of
  parts; a record can't be in two exclusive states; a tenant can never read another tenant's
  data. [check: review]
- **Localization robustness:** long strings, pseudo-loc, (RTL when in scope) — the UI must
  survive real translations. Locale-formatting correctness for dates/numbers.
  [check: review]
- **Accessibility tests:** labels present, large-type doesn't clip, contrast, target size.
  [check: review]
- **Interaction tests** including abandon-and-return flows (exit a screen mid-action, come
  back, observe what should and shouldn't have persisted). [check: review]
- **Client-side performance** (launch time, scroll jank, leaks) and **low-connectivity
  behavior** on everything network-touching. [check: review]
- **Security tests** on sensitive-flagged code: abuse/load, injection (including prompt
  injection where a model consumes external text), authorization (every endpoint rejects the
  wrong tenant/role). [check: review]
- **Migration forward/backward tests** whenever schema changes. [check: review]

## Verification discipline

- Verify in live mode against the real data path; demo/fixture modes make broken screens
  look finished.
- A task is not done until its tracking row/record says so with a verdict — a claim in a
  report is not the record.
- Screenshot-vs-design comparison is a quality dial; the honest walk of the whole product
  is the gate. [check: process]

## The build result is the truth — never an agent's word for it

An agent does not know whether its code compiles unless something actually ran the build.
Never accept "it compiles" or "tests pass" as a claim; require that a build/test step
*actually ran* and passed, verified by a step that cannot be skipped. **Build result =
truth; the author's word ≠ truth.** Anything that must happen lives in a hook, a script, or
CI — never in prose telling someone to remember. [check: process]

## Changing a test is a decision made before the work, not during it

**This rule protects the integrity of the codebase, not the sanctity of the tests.** Tests
absolutely do need to change sometimes — when the required behaviour genuinely changed, the
test asserting the old behaviour is now wrong, and changing it is the correct move.

What is being prevented is the specific failure of an implementer meeting a red test and
making it green by editing the test instead of the code — and its uglier twin, **contorting
the implementation into something convoluted purely to avoid touching a test.** Both damage
the codebase. Writing spaghetti to dodge a test edit is a worse outcome than the edit.

So the discipline is about *when and by whom* the decision gets made:

- **Decide test changes when planning the work, not while fighting a red run.** If the
  behaviour is changing, say so up front and change the test then — with the change visible
  and reviewable as part of the plan rather than buried in an implementation diff.
  [check: scan:test-weakened]
- **Mid-implementation, a red test is a question, not a licence.** If it turns out the test
  encodes an assumption the new behaviour invalidates, stop and raise it — then change the
  test deliberately, and record why. What is never acceptable is silently weakening or
  deleting a test so a run goes green. [check: process]
- **Every test change states the reason.** "The behaviour changed, here's how" is a good
  reason. "It was failing" is not a reason. [check: scan:test-weakened]
- The original concern: an agent doing work that touches tests must not simply change the
  tests so that they pass. Writing tests before the work starts is one of the best defences
  against this, and it also means any test that needs to change is changed before the work
  starts. The clarification (20 Aug 2026): if the function itself changed, the test changes
  with it; nobody writes spaghetti code to avoid modifying a test. The rules around tests
  are not about the tests themselves but about the integrity of the codebase, and sometimes
  a test does need to be modified.

## Three nets, each for what only it can catch

Spend the expensive net only where judgment is genuinely needed:

- **Structure → a deterministic script.** Schema diffs and symbol graphs: anything in the
  change that isn't on the approved item list fails mechanically.
  [check: context]
- **Behaviour → tests.** Locked by the rule above. [check: context]
- **Quality and justification → review judgment.** The only net that needs a mind.
  [check: context]

## Red main stops everything

Failing tests on the main branch halt the *start* of all new work — the fix is the only job
until it's green. This covers breakage that arrived from outside (a teammate's push), not
just your own merges. [check: process]

## Cadence — verify everything, waste nothing

Quality never drops; the goal is to stop paying for runs that prove nothing.

- Parallel lanes run their own target during the loop, and the **full suite once** before
  the lane's final commit. A serial merge step re-runs it after each merge.
- Sessions working on shared files keep the full suite green before every commit.
- **One review pass per task, at the end** — not per file, not per commit.
  [check: process]
- Bundle verification: one full-suite run over a batch, not one per merge, and never a
  re-run of a suite nothing has changed since.
- No extraneous test-suite runs, and nothing run separately that could be bundled and run
  later. Test your own work — quality never drops, for any reason — but do not be
  wasteful.

## Never re-run a proven paid pipeline as routine verification

Where a test path costs real money per run, a proven end-to-end path is not re-verified out
of habit. Verify with the free suite, a mock run, or records that already exist. A real
metered run needs **both** a concrete reason — a major change to that subsystem, a genuinely
new stage, or a live seam unverifiable any other way — **and** explicit sign-off. A
deliberately dead credential may be a spend guard; don't chase it as a bug.
[check: process]

## Long runs: watchdog, don't wait

- Know what a healthy run looks like for the project, in wall-clock terms, before you start
  one.
- **Never pipe a long run through `tail` alone** — it starves the log until exit, so nobody
  can tell stuck from slow. Stream through `tee` to a file and give the human the path.
  [check: process]
- Build the test target first, then run under a **hard timeout** sized to a healthy run. A
  fired timeout means a wedge: kill it, re-run with the known-hanging suite skipped, and
  **say in the report that you skipped it.**
- A suite that can wedge is a defect with a root cause. Find it; a permanent skip is not a
  fix.

## Proving a background run is alive

- The reliable signal is **recent file activity on disk** (a transcript or output file being
  written), not a process count — work may run in-process — and not a launch confirmation.
- Set a watchdog that polls for that activity after launching anything long-running.
- A dead run's partial work survives on disk: relaunch with instructions to review and
  resume, **never blind-restart**.
- When a status claim is challenged, re-verify from primary evidence rather than restating
  it more softly. (Origin: a status claim had to be challenged three times before it was
  checked against the evidence.)
[check: process]

## Fixtures the size of the real thing, and pressure past it

A fixture built to be convenient tests the fixture. Test data must be the
size, shape and messiness of the real thing: lists long enough to overflow
a container, names long enough to truncate, documents written in the
industry's words rather than the product's own vocabulary.

And push past it deliberately, as its own discipline: many more items than
anyone would have, values at and beyond the declared limits, empty and
enormous, slow and absent. Every surface that renders project data carries
at least one case at real size and one past it.

Origin (Coast, 2026-08-22, a walk of a real adopting app): the primary intake
screen overprinted itself on a real project, drawing a screen list over
the section beneath it — because every fixture project carried a handful
of screens and the real one carried thirteen. In the same evening: a
document checker that passed its own fixtures and refused a real 24 KB,
14-section PRD, because the fixtures were written in the product's
vocabulary by the same hand as the matcher; and a blueprint that showed
"1 module · 0 data models" where the real answer was 17 and 9.

The owner corrected the framing that real data breaks what fixtures
cannot: test mocks should use data similar to what would be used for
real, the mocks need improving, and pressure testing belongs alongside
realistic mocks. The first framing blames
the world; the second blames the tests, and only the second produces work.
[check: review]

## A stand-in must fail the way production fails

A test double that can only succeed or fail cleanly never exercises the
paths that break in production. Every stand-in for an external service
must be able to express that service's real refusal modes — the partial
denial ("403 — I won't even list them"), the plan-gated feature, the
empty-but-valid answer, the malformed response — not just success and a
clean thrown error.

Origin (Coast, 2026-08-22, the same walk): four chained defects
shipped behind a GitHub stand-in that could not say "403 — I won't tell
you". Each had correct handling code that was never reached (one read the
wrong account's plan; one turned an unreadable ruleset listing into a
hard failure before its own skip branch could run — ordering, not logic).
The walk found them all in one evening because production refused where
the stand-in never could.

Practice: when writing a stand-in, enumerate the real service's
documented failure responses first and make the double able to produce
each one; when a live defect is traced to an unreachable handler, teach
the stand-in that refusal in the same fix. [check: review]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
