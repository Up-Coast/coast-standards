# Data pipelines, scoring engines, and models

This file is for project type C. Read `types/backend-service.md` first; everything in it applies here too. This file adds rules for code whose output is a number, a score, a classification or a prediction, rather than a screen or a response.

Why this type needs its own rules: in an app, a bug usually shows as something visibly wrong. In a scoring pipeline, a bug shows as a **believable number that is quietly wrong**, and normal review does not catch it.

## Correctness you can prove

- **Every transformation and scoring rule has a test with known inputs and expected outputs.** Include the domain's real edge cases: missing fields, malformed rows, out-of-range values, duplicate records, and the units the source actually uses.
- **A rule the client owns is never invented.** If a formula, threshold or weighting is undefined, or belongs to the client, keep it as a labeled stub that shows as unknown. Never fill it with a believable guess. (This is priority rule 5, and it matters most in this project type.)
- **Unknown is a value, not a zero.** Represent missing data as missing, and keep it missing as it moves through the pipeline. Silently substituting a default turns a gap into a confident wrong answer.
- **A derived value is computed in one place.** The typical failure in this project type is a score computed slightly differently in the API and in a report.

## Reproducibility

- **A result can be reproduced from recorded inputs.** The pipeline records which data, which code version and which parameters produced each output. You must be able to answer "why did it score 0.82 last Tuesday?"
- **Randomness is seeded and recorded** wherever a result would otherwise change between runs.
- **Data transformations are deterministic and idempotent**: re-running a stage on the same input gives the same output and does not count anything twice.
- **Ingestion is idempotent.** Receiving the same source file or message again does not create duplicate records. Deduplication uses a stable key and can be audited.

## Data quality as a gate, not a hope

- **Incoming data is validated against an explicit schema at the boundary.** Rows that fail are set aside with the reason recorded. Never drop them silently, and never repair them by guessing.
- **Quality checks run as part of the pipeline**: row counts, null rates, range checks and referential checks. Their thresholds fail the run, instead of writing a warning nobody reads.
- **Schema changes at the source are detected** when they happen, not discovered later through wrong numbers.

## Models and scoring

- **A model or scoring version is recorded with every output it produces**, so any change in results can be traced to its cause.
- **Evaluation is defined before tuning.** Write down the metric, the holdout set and what "good enough" means first, so a model is not judged by whichever metric happens to look best afterwards.
- **Training data and evaluation data never overlap**, and the split can be reproduced.
- **Drift is monitored.** Watch input and output distributions over time, because a model that was right at launch gets worse quietly.
- **A score that will drive a decision carries its confidence and its inputs**, so a person can see why. A number that cannot be explained must not drive a safety or money decision.

## Presenting results honestly

- **Nulls, placeholders, stubs, and unvalidated data are visibly flagged** in every output a person reads, both in the code and in the interface. A dash and a zero must never look the same.
- **Precision is not invented.** Do not show more decimal places than the method supports. Do not present an estimate as a measurement.
- **Sample size and coverage travel with the number.** A rate computed from three records is labeled as such.

## Null handling is a correctness rule, not a style choice

- **Use the data library's own null test, never language identity comparison**, in boundary and threshold checks: `pd.isna()`, not `is None`. They are not the same. A missing value is often not `None`, so an `is None` check can silently mark a high-risk record as cleared. This is the checkable form of "unknown is a value, not a zero."
- **Establish the grain before writing the ingest path.** Before designing the upsert, decide whether a source row is one event or a whole lifecycle episode. Getting this wrong creates duplicate downstream alerts that look real. Downstream triggers fire only on real inserts, never on updates.

---

[← All rules](../README.md) · [Priority rules](../00-priority-rules.md) · [Project types](../PROJECT-TYPES.md) · [Documentation](../../docs/README.md)
