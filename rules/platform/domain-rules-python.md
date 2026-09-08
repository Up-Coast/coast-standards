# Project rules

This file ships with your project as a curated default, sourced from
established, widely used engineering and safety guides (listed under Sources
at the bottom). **It belongs to you.** Edit any rule, delete what doesn't
apply to your product, and add your own rules on top — you never have to
write a document like this from scratch. Automated reviewers check every
code change against exactly the rules in this file, so a rule you add here
is enforced on every change from then on.

How to read a rule: each one has an id (used in reviews, tickets, and
tests), a single checkable statement, and the guide it comes from in
brackets. Keep new rules checkable — a reviewer must be able to answer
"does this change break the rule — yes or no?"

This is the **Python backend / service** file: web APIs, data pipelines,
workers, and scripts. If the project also has a browser frontend, add the
web file's rules for that part.

## Structure and modules (ARCH)

- **ARCH-1** The project is organized into modules by feature or domain
  area, each with its own package directory and a clear public surface —
  not a flat pile of scripts. [Industry-wide practice; check: review]
- **ARCH-2** Module dependencies flow one way, with no cycles: feature
  modules depend on shared domain abstractions, never on each other, and
  never on concrete data-access code. Import cycles are a build failure,
  not a style note. The modules are the project package's subpackages
  (`src/<pkg>/<module>/` or `<pkg>/<module>/`, the package root being the
  app target that wires data access in) or, with no single project package,
  the top-level packages side by side; `domain` and `data` are the shared
  layers by name, and the state dir's `module-kinds.json` names any other
  module's kind. [Industry-wide practice; check: scan:import-matrix]
- **ARCH-3** Business logic is separated from transport: request handlers
  (FastAPI/Flask/Django views) parse and validate, then call a function
  that could be called just as well from a worker, a test, or a script.
  [Industry-wide practice; check: review]
- **ARCH-4** Database access is confined to a data-access layer. Handlers,
  business logic, and scripts call that layer; raw queries and ORM session
  handling do not spread through feature code. [Industry-wide practice; check:
  scan:layer-import, review]
- **ARCH-5** A module or function has one job. No speculative abstraction:
  the second real caller justifies the shared helper, not the first
  imagined one — module-boundary seams qualify by definition.
  [Industry-wide practice; check: advisory:type-size, review]
- **ARCH-6** Every derived value is computed in one place and reused —
  scores, totals, statuses, thresholds, and rounding are never
  reimplemented slightly differently in a second module. [Industry-wide practice;
  check: tool:jscpd, review]
- **ARCH-7** Configuration comes from environment or a config object loaded
  at startup and validated — never module-level constants edited per
  deployment, and never a value read straight out of `os.environ` deep
  inside feature code. [Twelve-Factor App; OWASP ASVS; check: scan:env-literal,
  review]

- **ARCH-8** No hardcoded facts about the world outside the code. A
  repository's default branch, a file path, a URL or port, a plan or
  platform tier, an external system's names or limits — every such fact
  is either asked of the system that owns it or read from its one
  configured home, through one shared function every caller uses. A
  literal assumption about external state (a branch named "main", a
  fixed path or URL) is a review failure wherever the real answer can
  be asked for. [Twelve-Factor App, config; check: scan:env-literal]

## Security (SEC)

- **SEC-1** All outbound and inbound traffic uses TLS. Certificate
  verification is never disabled (`verify=False` and equivalents are a
  review failure). [OWASP ASVS; check: scan:plaintext-http]
- **SEC-2** Data arriving from outside — request bodies, query parameters,
  uploaded files, message-queue payloads, third-party API responses, CSV
  and log ingestion — is validated against an explicit schema (Pydantic,
  marshmallow, dataclass validation) before use. [OWASP ASVS; OWASP Cheat Sheet:
  Input Validation; check: review]
- **SEC-3** SQL is parameterized — bound parameters or the ORM's query
  API — never assembled by string formatting, f-strings, or
  concatenation, including in migrations and analytics scripts.
  [OWASP Cheat Sheet: Query Parameterization; check: scan:sql-string-assembly]
- **SEC-4** No shell injection: subprocesses are invoked with an argument
  list and never `shell=True` on a command built from external data.
  [OWASP ASVS; Python documentation: subprocess security considerations; check:
  scan:shell-injection]
- **SEC-5** Untrusted input is never passed to `eval`, `exec`, `pickle`,
  `yaml.load` (use `safe_load`), or any other construct that executes or
  instantiates arbitrary objects from data. [OWASP ASVS; Python documentation:
  pickle security; check: scan:dangerous-eval]
- **SEC-6** Every endpoint checks that the caller is allowed to reach the
  specific record it returns — authorization by ownership or role, not by
  the id being hard to guess. [OWASP Top 10: Broken Access Control; check: review]
- **SEC-7** No home-made cryptography. Encryption, hashing, tokens, and
  random values for security use standard libraries (`hashlib`, `secrets`,
  `cryptography`) — never `random` for anything security-related, and
  never a hand-rolled scheme. Passwords, when stored at all, use a
  purpose-built password hash (argon2, bcrypt, scrypt). [OWASP ASVS; OWASP Cheat
  Sheet: Password Storage; check: review]
- **SEC-8** Secrets — API keys, tokens, database URLs, credentials — come
  from the environment or a secret store, and never appear in source
  control, logs, error messages, tracebacks sent to clients, or test
  fixtures. [OWASP ASVS; OWASP Cheat Sheet: Secrets Management; check:
  scan:secret-literal]
- **SEC-9** Errors returned to a caller never expose internals — no stack
  traces, query text, file paths, or library versions in an API response
  or an HTML error page. Debug mode is off in every deployed environment.
  [OWASP Cheat Sheet: Error Handling; check: review]
- **SEC-10** Uploaded and ingested files are size-limited, type-checked by
  content rather than by filename, and written outside any directory the
  server will execute or serve directly. Paths built from external input
  are resolved and confirmed to stay inside the intended directory.
  [OWASP Cheat Sheets: File Upload, Path Traversal; check: review]
- **SEC-11** Dependencies are pinned by lockfile with hashes where the
  tooling supports it, installed from the official index, and audited for
  known vulnerabilities as part of the build. [OWASP ASVS; PyPA packaging
  guidance; check: review]

## Data and persistence (DATA)

- **DATA-1** Every schema change ships as a migration in version control
  (Alembic or the framework's migration system) — never a hand-run
  `ALTER TABLE` against a live database. [Industry-wide practice; check: review]
- **DATA-2** A migration identifier, once it can have run anywhere, never
  changes; migrations are additive and check before adding, so a
  mismatched history repairs itself rather than locking the service out.
  [Industry-wide practice; check: review]
- **DATA-3** Money is stored and calculated with decimal-safe types or
  whole minor units — `Decimal` and `NUMERIC`, never `float` arithmetic
  on fractional amounts. Every stored amount carries its currency.
  [Industry-wide practice; check: advisory:money-float, review]
- **DATA-4** Timestamps are stored timezone-aware in UTC and converted
  only at the edges for display. Naive `datetime.now()` does not enter
  stored data. [Industry-wide practice; check: review]
- **DATA-5** Writes that must happen together happen in one transaction,
  and a failed operation leaves no half-written state. [Industry-wide practice;
  check: review]
- **DATA-6** Queries that can return unbounded rows are paginated or
  limited; a list endpoint never loads a whole table into memory, and
  loops do not issue one query per row when a single query would do.
  [Industry-wide practice; check: review]
- **DATA-7** Customer data, fleet data, user content, and credentials
  never enter version control. Fixtures and sample data are synthetic or
  explicitly cleared for the repo. [OWASP ASVS; check: scan:secret-literal,
  review]

## APIs and contracts (API)

- **API-1** Request and response shapes are declared as schemas, and the
  API's generated documentation reflects the real contract. [Industry-wide
  practice; check: review]
- **API-2** Breaking a published response shape is a versioned change, not
  an edit — existing callers keep working or are migrated deliberately.
  [Industry-wide practice; check: review]
- **API-3** HTTP status codes carry the real outcome: not everything is
  200, and failures are distinguishable by code, not only by a body
  field. [Industry-wide practice; check: review]
- **API-4** Endpoints that cost money, send messages, or mutate state are
  rate-limited and, where a client may retry, idempotent. [OWASP ASVS; check:
  review]
- **API-5** Outbound calls to third-party services have explicit timeouts
  and a defined behaviour on failure — never an unbounded wait, never a
  silent swallow. [Industry-wide practice; check: review]

## Errors, logging, and observability (OBS)

- **OBS-1** Exceptions are caught where they can be handled meaningfully.
  A bare `except:` or an `except Exception: pass` that hides a failure is
  a review failure. [Python documentation: exception handling; industry-wide
  practice; check: review]
- **OBS-2** Logs are structured and leveled, and never contain secrets,
  credentials, tokens, or personal data. [OWASP Cheat Sheet: Logging; check:
  ratchet:pii-in-log, review]
- **OBS-3** Every background job, worker, and scheduled task reports
  success and failure somewhere a human will see — a job that dies
  silently is a defect. [Industry-wide practice; check: review]
- **OBS-4** User-facing messages (API error text, emails, notifications)
  live in one place, not scattered as literals through handlers — so
  wording can change without hunting through code. [Industry-wide practice; check:
  scan:ui-string-literal]

## Concurrency and async (ASYNC)

- **ASYNC-1** Blocking calls — file I/O, `requests`, CPU-heavy work — do
  not run inside an async event loop; they go to a thread pool, a
  process pool, or a worker. [Python documentation: asyncio; check:
  scan:blocking-call]
- **ASYNC-2** Shared mutable state accessed from more than one thread,
  task, or process is protected, or the design avoids the sharing. Module-
  level mutable globals are not a cache. [Industry-wide practice; check: review]
- **ASYNC-3** Long-running work triggered by a request runs in a queue or
  worker, not inside the request. [Industry-wide practice; check: review]

## Style, typing, and readability (STYLE)

- **STYLE-1** Code follows the project's formatter and linter with no
  per-file exemptions accumulating — formatting is not a review topic
  because a tool decides it (Black/Ruff or equivalent, run in CI).
  [PEP 8; tool documentation; check: ruff, mypy]
- **STYLE-2** Public functions, methods, and module boundaries carry type
  annotations, and the type checker runs in CI. New code does not add
  untyped public surface. [PEP 484; industry-wide practice; check: mypy:strict]
- **STYLE-3** Names say what the thing is, in the project's established
  vocabulary — one name per concept across the whole codebase, never a
  synonym for something already named. [PEP 8; industry-wide practice; check:
  review]
- **STYLE-4** Every public module, class, and function has a docstring
  stating what it does and anything a caller must know. Comments explain
  constraints the code cannot show — never restate the next line.
  [PEP 257; check: scan:doc-comments]
- **STYLE-5** Mutable default arguments are never used (`def f(x=[])` is a
  defect). [Python documentation: common gotchas; check: ruff:B006]

## Testing (TEST)

- **TEST-1** Every behaviour named in the requirements has a test that
  fails when the behaviour is broken. A test that passes regardless of the
  code under test is a defect, not coverage. [Industry-wide practice; check:
  scan:test-criterion-tag]
- **TEST-2** Tests are deterministic and independent: no dependence on
  execution order, wall-clock time, network access, or a developer's local
  database. External services are faked at a seam the code owns.
  [Industry-wide practice; check: scan:hermetic-test]
- **TEST-3** Bug fixes land with a test that reproduces the bug and fails
  before the fix. [Industry-wide practice; check: review]
- **TEST-4** Data-transformation and scoring logic is tested against known
  inputs and expected outputs, including the edge cases the domain cares
  about (missing fields, malformed rows, out-of-range values).
  [Industry-wide practice; check: review]

## Sources

- **OWASP Application Security Verification Standard (ASVS) 5.0** —
  <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** (Input Validation, Query Parameterization,
  Password Storage, Secrets Management, File Upload, Path Traversal,
  Logging, Error Handling) — <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **OWASP Top 10** — <https://owasp.org/www-project-top-ten/> (CC BY-SA 4.0)
- **Python documentation** (subprocess, pickle, asyncio, exceptions,
  programming FAQ) — <https://docs.python.org/3/> (PSF license — referenced only)
- **PEP 8** (style), **PEP 257** (docstrings), **PEP 484** (type hints) —
  <https://peps.python.org/> (referenced only)
- **PyPA packaging guidance** — <https://packaging.python.org/> (referenced only)
- **The Twelve-Factor App** — <https://12factor.net/> (referenced only)

No text from these guides is reproduced here — every rule is an original
plain-language statement citing its source — so editing or replacing this
file carries no license obligations for you.
