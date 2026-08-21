# Testing

The floor is non-negotiable; the depth dials scale with the project's risk tier. No safety
gate is ever toggleable.

## The floor (always required)

- **TDD:** write the failing test first, then the code. Run the relevant suite before and
  after every work session; keep the full suite green before every commit on shared files.
- **Unit tests: every function has one.**
- **Every acceptance criterion has ≥1 automated test, and each test states which criterion
  it verifies.**
- **Never weaken a test to make it pass. Never mark a failing task complete. Never start
  the next task with the app broken.**
- **Merge-gating tests are hermetic** — they run without live external services; live-service
  tests run separately (opt-in flag) and never block a merge.

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

Tests are reviewed by something that didn't write them ("passing is not the question;
whether passing MEANS anything is"). Reviewers of tests never edit them.

## Test-first for existing code

Before changing code, check that tests exist for everything the change touches **or
affects** — including downstream code its data flows into. If they don't exist, write them
for the existing code first, then start the feature.

## Required test types per feature (risk/cost dials)

- **Negative tests:** assert that things that should fail still fail. Keep a visible
  negative-coverage registry so "what we reject" is auditable. (Classic miss: nobody checked
  the phone field rejects letters.)
- **Data-variation tests, exhaustive** where input is user text: ALL CAPS, leading/trailing/
  multiple spaces, punctuation, empty, very long. AI testing is cheap — catch every edge.
- **Domain-invariant tests** generated from the project's rules doc: totals equal the sum of
  parts; a record can't be in two exclusive states; a tenant can never read another tenant's
  data.
- **Localization robustness:** long strings, pseudo-loc, (RTL when in scope) — the UI must
  survive real translations. Locale-formatting correctness for dates/numbers.
- **Accessibility tests:** labels present, large-type doesn't clip, contrast, target size.
- **Interaction tests** including abandon-and-return flows (exit a screen mid-action, come
  back, observe what should and shouldn't have persisted).
- **Client-side performance** (launch time, scroll jank, leaks) and **low-connectivity
  behavior** on everything network-touching.
- **Security tests** on sensitive-flagged code: abuse/load, injection (including prompt
  injection where a model consumes external text), authorization (every endpoint rejects the
  wrong tenant/role).
- **Migration forward/backward tests** whenever schema changes.

## Verification discipline

- Verify in live mode against the real data path; demo/fixture modes make broken screens
  look finished.
- A task is not done until its tracking row/record says so with a verdict — a claim in a
  report is not the record.
- Screenshot-vs-design comparison is a quality dial; the honest walk of the whole product
  is the gate.

## The build result is the truth — never an agent's word for it

An agent does not know whether its code compiles unless something actually ran the build.
Never accept "it compiles" or "tests pass" as a claim; require that a build/test step
*actually ran* and passed, verified by a step that cannot be skipped. **Build result =
truth; the author's word ≠ truth.** Anything that must happen lives in a hook, a script, or
CI — never in prose telling someone to remember.

## Tests are locked once written

- From the moment the tests-first commit exists, **existing tests may not be modified or
  deleted while implementing.** A failing test is fixed by fixing the code, or escalated as
  a question.
- The legitimate case — the required behaviour genuinely changed — is handled by changing
  the test **before the work starts**, never during it.
- After implementation begins, tests may only be **added**. "Implement to green" is not done
  if the diff touches existing tests.
- Abbey's words: *"we need to make sure that the agent doing work that touches test didn't
  just change the tests so that they pass … tests should be written before the work starts
  that's one of our best defences against this problem and this also means that any test
  that needs to be modified should be modified before the work starts."*

## Three nets, each for what only it can catch

Spend the expensive net only where judgment is genuinely needed:

- **Structure → a deterministic script.** Schema diffs and symbol graphs: anything in the
  change that isn't on the approved item list fails mechanically.
- **Behaviour → tests.** Locked by the rule above.
- **Quality and justification → review judgment.** The only net that needs a mind.

## Red main stops everything

Failing tests on the main branch halt the *start* of all new work — the fix is the only job
until it's green. This covers breakage that arrived from outside (a teammate's push), not
just your own merges.

## Cadence — verify everything, waste nothing

Quality never drops; the goal is to stop paying for runs that prove nothing.

- Parallel lanes run their own target during the loop, and the **full suite once** before
  the lane's final commit. A serial merge step re-runs it after each merge.
- Sessions working on shared files keep the full suite green before every commit.
- **One review pass per task, at the end** — not per file, not per commit.
- Bundle verification: one full-suite run over a batch, not one per merge, and never a
  re-run of a suite nothing has changed since.
- Abbey: *"please do not do extraneous test suite runs or things that you can bundle
  together later. We should of course test our own work, we don't want quality to drop at
  all, for any reason, I just saying don't be wasteful."*

## Never re-run a proven paid pipeline as routine verification

Where a test path costs real money per run, a proven end-to-end path is not re-verified out
of habit. Verify with the free suite, a mock run, or records that already exist. A real
metered run needs **both** a concrete reason — a major change to that subsystem, a genuinely
new stage, or a live seam unverifiable any other way — **and** explicit sign-off. A
deliberately dead credential may be a spend guard; don't chase it as a bug.

## Long runs: watchdog, don't wait

- Know what a healthy run looks like for the project, in wall-clock terms, before you start
  one.
- **Never pipe a long run through `tail` alone** — it starves the log until exit, so nobody
  can tell stuck from slow. Stream through `tee` to a file and give the human the path.
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
  it more softly. (Abbey, after this failed three times in a row: *"I should not have had to
  challenge you 3 times, please be more thorough and correct next time."*)
