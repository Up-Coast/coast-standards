<!-- coast-standards-release: 1.12.1 -->
# Project rules

Your project's rules: edit, delete or add any; reviewers check every change against this file. Each rule ends with what checks it: `review` a reviewer, `scan:` the scanner refuses it, `ratchet:` a count that may only fall, `advisory:` reported only, `tool:`, `ruff` or `mypy` the pre-push hook, `process` the pipeline or a person. Write every rule so a reviewer can answer yes or no.

For Python backends and services (web APIs, data pipelines, workers, scripts); add the web rules for any browser frontend.

## Structure and modules (ARCH)

- **ARCH-1** Organize code as feature or domain packages with clear public interfaces, not a flat pile of scripts. [check: review]
- **ARCH-2** Dependencies go one way with no cycles (a cycle fails the build); features depend on domain abstractions, never on each other or concrete data code. Modules are the project package's subpackages (`src/<pkg>/<module>/` or `<pkg>/<module>/`; the root is the entry point wiring in data access), else the top-level packages; `domain` and `data` are the shared layers, and the state directory's `module-kinds.json` names other modules' kinds. [check: scan:import-matrix]
- **ARCH-3** Handlers (FastAPI, Flask, Django views) only parse and validate, then call business logic a worker, test or script could call. [check: review]
- **ARCH-4** Only the data-access layer touches the database; no raw queries or ORM sessions elsewhere. [check: scan:layer-import, review]
- **ARCH-5** One job per module or function; create a shared helper at its second real caller, not its first. A module-boundary seam is always justified. [check: advisory:type-size, review]
- **ARCH-6** Compute each derived value (score, total, status, threshold, rounding) in one place; never reimplement it in a second module. [check: tool:jscpd, review]
- **ARCH-7** Load and validate configuration from the environment or a config object at startup; no per-deployment module constants, no `os.environ` reads deep in feature code. [check: scan:env-literal, review]
- **ARCH-8** Never hardcode outside facts (branch, path, URL, port, tier, external names or limits); get them from their owner or their one configured place, through one shared function. [check: scan:env-literal]

## Security (SEC)

- **SEC-1** All inbound and outbound traffic uses TLS; never disable certificate verification (`verify=False` or equivalent). [check: scan:plaintext-http]
- **SEC-2** Validate all outside data (bodies, query parameters, uploads, queue payloads, third-party responses, CSV and log ingestion) against a schema (Pydantic, marshmallow, dataclasses). [check: review]
- **SEC-3** Parameterize all SQL with bound parameters or the ORM, never formatting, f-strings or concatenation, migrations and analytics scripts included. [check: scan:sql-string-assembly]
- **SEC-4** Call subprocesses with an argument list; never `shell=True` on a command built from external data. [check: scan:shell-injection]
- **SEC-5** Never pass untrusted input to `eval`, `exec`, `pickle`, `yaml.load` (use `safe_load`) or anything that runs code or builds arbitrary objects. [check: scan:dangerous-eval]
- **SEC-6** Every endpoint authorizes the specific record by ownership or role, never by a hard-to-guess id. [check: review]
- **SEC-7** Use standard libraries (`hashlib`, `secrets`, `cryptography`) for encryption, hashing, tokens and security randomness, never `random` or a hand-rolled scheme; any stored password uses argon2, bcrypt or scrypt. [check: review]
- **SEC-8** Secrets (keys, tokens, database URLs, credentials) come from the environment or a secret store, never source, logs, errors, client tracebacks or fixtures. [check: scan:secret-literal]
- **SEC-9** Errors returned to callers never show stack traces, query text, file paths or library versions; debug mode is off in every deployed environment. [check: review]
- **SEC-10** Limit uploaded and ingested files by size and check type by content, not filename; store them outside served or executed directories, and confirm any path built from input resolves inside its intended directory. [check: review]
- **SEC-11** Pin dependencies in a lockfile, with hashes where supported; install from the official index and audit for known vulnerabilities in the build. [check: review]

## Data and persistence (DATA)

- **DATA-1** Every schema change is a version-controlled migration (Alembic or the framework's); never `ALTER TABLE` by hand on a live database. [check: review]
- **DATA-2** Never change the identifier of a migration that could have run anywhere; migrations only add, and check before adding, so a mismatched history repairs itself. [check: review]
- **DATA-3** Store and compute money as `Decimal`/`NUMERIC` or whole minor units, never `float`; every stored amount carries its currency. [check: advisory:money-float, review]
- **DATA-4** Store timestamps as timezone-aware UTC, converting only for display; never store a naive `datetime.now()`. [check: review]
- **DATA-5** Writes that belong together run in one transaction; a failure leaves nothing half-written. [check: review]
- **DATA-6** Paginate or limit any query that could return unbounded rows; no whole-table loads, no query per row where one query would do. [check: review]
- **DATA-7** Customer data, operational data, user content and credentials never enter version control; fixtures are synthetic or explicitly cleared. [check: scan:secret-literal, review]

## APIs and contracts (API)

- **API-1** Declare request and response shapes as schemas; generated API docs match the real contract. [check: review]
- **API-2** A breaking change to a published response shape is a new version; existing callers keep working or are migrated on purpose. [check: review]
- **API-3** Status codes reflect the real outcome, so callers can tell failures apart without reading the body. [check: review]
- **API-4** Rate-limit endpoints that cost money, send messages or change state, and make them idempotent where clients may retry. [check: review]
- **API-5** Third-party calls have explicit timeouts and defined failure behaviour; never wait without limit or swallow a failure. [check: review]

## Errors, logging, and observability (OBS)

- **OBS-1** Catch exceptions only where you can handle them; a bare `except:` or a failure-hiding `except Exception: pass` fails review. [check: review]
- **OBS-2** Logs are structured and levelled, and never hold secrets, credentials, tokens or personal data. [check: ratchet:pii-in-log, review]
- **OBS-3** Every background job, worker and scheduled task reports success and failure where a person will see it; a silent death is a defect. [check: review]
- **OBS-4** Keep user-facing messages (API error text, emails, notifications) in one place, never as literals in handlers. [check: scan:ui-string-literal]

## Concurrency and async (ASYNC)

- **ASYNC-1** Never run blocking calls (file I/O, `requests`, CPU-heavy work) in an event loop; send them to a thread pool, process pool or worker. [check: scan:blocking-call]
- **ASYNC-2** Protect mutable state shared across threads, tasks or processes, or design the sharing away; module-level mutable globals are not a cache. [check: review]
- **ASYNC-3** Long work a request starts runs in a queue or worker, not in the request. [check: review]

## Style, typing, and readability (STYLE)

- **STYLE-1** Code passes the project's formatter and linter (Black/Ruff or equivalent) in CI; per-file exemptions do not pile up, and formatting is never a review topic. [check: ruff, mypy]
- **STYLE-2** Public functions, methods and module boundaries are type-annotated and the type checker runs in CI; new code adds no untyped public interface. [check: mypy:strict]
- **STYLE-3** One name per concept across the codebase, in the project's vocabulary; never add a synonym. [check: review]
- **STYLE-4** Every public module, class and function has a docstring saying what it does and what callers must know; comments explain constraints, never restate code. [check: scan:doc-comments]
- **STYLE-5** Never use mutable default arguments (`def f(x=[])`). [check: ruff:B006]

## Testing (TEST)

- **TEST-1** Every required behaviour has a test that fails when it breaks; a test that always passes is a defect, not coverage. [check: scan:test-criterion-tag]
- **TEST-2** Tests are deterministic and independent of run order, the clock, the network and local databases; fake outside services at an interface the code owns. [check: scan:hermetic-test]
- **TEST-3** Every bug fix adds a test that reproduces the bug and fails before the fix. [check: review]
- **TEST-4** Test transformation and scoring logic against known inputs and outputs, including missing fields, malformed rows and out-of-range values. [check: review]
- **TEST-6** Test each result a model, network service or file can return (answer, refusal, timeout, empty, wrong shape), checking what the person sees, in the product's words, and can do next; an always-answering fake is not enough. [check: review]
- **TEST-7** A flow is done only when its builder has used it in the built product through its screens, buttons and links (window, title, settings, navigation, relaunch), saving screen captures and reading stored data back after each action; a screenshot of the new pane alone does not count. [check: process, review]

---

## Sources

The rules are original statements drawn from OWASP, the Python documentation, PEP 8, PEP 257, PEP 484, PyPA packaging guidance and the Twelve-Factor App ([links](https://github.com/Up-Coast/coast-standards/blob/main/rules/README.md#sources)).
