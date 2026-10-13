# Data pipelines, scoring engines, and models

Read this when working on type C, with `backend-service.md`.

## Correctness you can prove

- **Every transformation and scoring rule has a test with known inputs and expected outputs.** Cover missing, malformed, out-of-range and duplicate rows and real units.
- **A rule the client owns is never invented.** It stays a stub shown as unknown.
- **Unknown is a value, not a zero.**
- **A derived value is computed in one place.**

## Reproducibility

- **A result can be reproduced from recorded inputs.** Record data, code version and parameters per output.
- **Randomness is seeded and recorded.**
- **Data transformations are deterministic and idempotent.** No double counting on re-run.
- **Ingestion is idempotent.** Dedupe on a stable key.

## Data quality as a gate, not a hope

- **Incoming data is validated against an explicit schema at the boundary.** Set failures aside with a reason, never drop or guess.
- **Quality checks run as part of the pipeline**: counts, null rates, ranges, references; a breach fails the run.
- **Schema changes at the source are detected** at once.

## Models and scoring

- **A model or scoring version is recorded with every output it produces.**
- **Evaluation is defined before tuning**: metric, holdout, "good enough".
- **Training data and evaluation data never overlap**, and the split is reproducible.
- **Drift is monitored** on inputs and outputs.
- **A score that will drive a decision carries its confidence and its inputs.** Unexplained numbers never drive safety or money decisions.

## Presenting results honestly

- **Nulls, placeholders, stubs, and unvalidated data are visibly flagged** in every output; a dash never looks like a zero.
- **Precision is not invented.** No false decimals; estimates are not measurements.
- **Sample size and coverage travel with the number.**

## Null handling is a correctness rule, not a style choice

- **Use the data library's own null test, never language identity comparison**,: `pd.isna()`, not `is None`.
- **Establish the grain before writing the ingest path**: event or lifecycle episode per row. Triggers fire on inserts only.

---

[← All rules](../README.md) · [Documentation](../../docs/README.md)
