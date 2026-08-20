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
