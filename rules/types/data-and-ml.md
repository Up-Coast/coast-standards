# Data pipelines, scoring engines, and models

For project type C. Read `types/backend-service.md` first — everything there
applies; this file adds what is specific to code whose output is a number, a
score, a classification, or a prediction rather than a screen or a response.

Why this needs its own rules: in an app, a bug shows up as something visibly
wrong. In a scoring pipeline, a bug shows up as a **plausible number that is
quietly incorrect**, and nothing in the ordinary review path catches that.

## Correctness you can prove

- **Every transformation and scoring rule has a test with known inputs and
  expected outputs**, including the domain's real edge cases: missing fields,
  malformed rows, out-of-range values, duplicate records, and the units the
  source actually uses.
- **A rule the client owns is never invented.** If a formula, threshold, or
  weighting is undefined or belongs to the client, it stays a labeled stub
  that surfaces as unknown — never a plausible guess. (Priority rule 5, and
  this is the project type where it matters most.)
- **Unknown is a value, not a zero.** Missing data is represented as missing
  and travels as missing. Silently substituting a default turns a gap into a
  confident wrong answer.
- **A derived value is computed in one place.** A score recomputed slightly
  differently in the API and in a report is the defining failure of this
  project type.

## Reproducibility

- **A result can be reproduced from recorded inputs.** The pipeline records
  which data, which code version, and which parameters produced an output.
  "It scored 0.82 last Tuesday" must be answerable.
- **Randomness is seeded and recorded** wherever a result would otherwise
  vary between runs.
- **Data transformations are deterministic and idempotent**: re-running a
  stage on the same input produces the same output and does not double-count.
- **Ingestion is idempotent.** Re-delivering the same source file or message
  does not create duplicate records; deduplication is by a stable key and is
  auditable.

## Data quality as a gate, not a hope

- **Incoming data is validated against an explicit schema at the boundary**,
  and rows that fail are quarantined with the reason recorded — never dropped
  silently, never repaired by guessing.
- **Quality checks run as part of the pipeline**: row counts, null rates,
  range checks, and referential checks, with thresholds that fail the run
  rather than writing a warning nobody reads.
- **Schema changes at the source are detected**, not discovered later through
  wrong numbers.

## Models and scoring

- **A model or scoring version is recorded with every output it produces**,
  so a change in results is attributable.
- **Evaluation is defined before tuning**: the metric, the holdout, and what
  "good enough" means are written down, so a model is not judged by whichever
  metric happens to look best afterwards.
- **Training data and evaluation data never overlap**, and the split is
  reproducible.
- **Drift is monitored** — input distributions and output distributions are
  watched over time, because a model that was right at launch degrades
  quietly.
- **A score that will drive a decision carries its confidence and its
  inputs**, so a person can see why. An unexplainable number driving a safety
  or money decision is not shippable.

## Presenting results honestly

- **Nulls, placeholders, stubs, and unvalidated data are visibly flagged** in
  any output a person reads — in the code and in the interface. A dash and a
  zero must never look the same.
- **Precision is not invented.** Do not render more decimal places than the
  method supports; do not present an estimate as a measurement.
- **Sample size and coverage travel with the number.** A rate computed from
  three records is labeled as such.

## Null handling is a correctness rule, not a style choice

- **Use the data library's own null test, never language identity comparison**, on boundary
  and threshold checks — `pd.isna()`, not `is None`. They are not equivalent: a real
  incident had an `is None` check silently misclassify high-risk vehicles as cleared,
  because the missing value wasn't `None`. This is the checkable form of "unknown is a value,
  not a zero."
- **Establish the grain before writing the ingest path.** Decide whether a source row is an
  event or a whole lifecycle episode *before* designing the upsert — getting it wrong
  produces duplicated downstream alerts that look like real ones. Downstream triggers fire
  on genuine inserts only, never on updates.

---

[← All rules](../README.md) · [Priority rules](../00-priority-rules.md) · [Project types](../PROJECT-TYPES.md) · [Documentation](../../docs/README.md)
