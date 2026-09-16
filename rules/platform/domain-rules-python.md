<!-- coast-standards-release: 1.6.0 -->
# Project rules

This file is a starting set of rules for your project. They come from well-known engineering and security guides, listed under Sources at the bottom.

**This file belongs to you.** Edit any rule, delete rules that don't apply, and add your own.

Automated reviewers check every code change against the rules in this file. A rule you add here applies to every change from then on.

How to read a rule:

- The id (for example `SEC-3`) is used in reviews, tickets and tests.
- The sentence after it is one checkable requirement.
- The brackets name the source guide and how the rule is checked.

Keep new rules checkable. A reviewer must be able to answer "does this change break the rule: yes or no?"

This file is for **Python backends and services**: web APIs, data pipelines, workers and scripts. If the project also has a browser frontend, add the web rules for that part.

## Structure and modules (ARCH)

- **ARCH-1** Organize the project into modules by feature or domain area. Each module has its own package directory and a clear public interface. The project is not a flat pile of scripts. [Industry-wide practice; check: review]
- **ARCH-2** Module dependencies go one way, with no cycles. Feature modules depend on shared domain abstractions, never on each other, and never on concrete data-access code. An import cycle fails the build; it is not a style note. What counts as a module: the subpackages of the project package (`src/<pkg>/<module>/` or `<pkg>/<module>/`), where the package root is the app entry point that wires in data access. If there is no single project package, the modules are the top-level packages. `domain` and `data` are the shared layers, by name. The state directory's `module-kinds.json` names the kind of any other module. [Industry-wide practice; check: scan:import-matrix]
- **ARCH-3** Keep business logic separate from transport. Request handlers (FastAPI, Flask or Django views) only parse and validate. They then call a function that a worker, a test or a script could call just as well. [Industry-wide practice; check: review]
- **ARCH-4** Only the data-access layer touches the database. Handlers, business logic and scripts call that layer. Raw queries and ORM session handling do not appear in feature code. [Industry-wide practice; check: scan:layer-import, review]
- **ARCH-5** A module or function has one job. Don't add abstractions for imagined needs: create a shared helper when a second real caller needs it, not for the first. A seam at a module boundary always counts as justified. [Industry-wide practice; check: advisory:type-size, review]
- **ARCH-6** Compute every derived value in one place and reuse it. Scores, totals, statuses, thresholds and rounding are never reimplemented, slightly differently, in a second module. [Industry-wide practice; check: tool:jscpd, review]
- **ARCH-7** Configuration comes from the environment or a config object that is loaded and validated at startup. Never use module-level constants that are edited per deployment. Never read `os.environ` directly deep inside feature code. [Twelve-Factor App; OWASP ASVS; check: scan:env-literal, review]
- **ARCH-8** Don't hardcode facts about the world outside the code. Examples: a repository's default branch, a file path, a URL or port, a plan or platform tier, an external system's names or limits. Ask the system that owns the fact, or read it from its single configured location. Either way, go through one shared function that every caller uses. Hardcoding an assumption about external state (a branch named "main", a fixed path or URL) fails review whenever the real answer can be looked up. [Twelve-Factor App, config; check: scan:env-literal]

## Security (SEC)

- **SEC-1** All inbound and outbound traffic uses TLS. Never turn off certificate verification: `verify=False` and its equivalents fail review. [OWASP ASVS; check: scan:plaintext-http]
- **SEC-2** Validate data from outside against an explicit schema (Pydantic, marshmallow, dataclass validation) before using it. This covers request bodies, query parameters, uploaded files, message-queue payloads, third-party API responses, and CSV and log ingestion. [OWASP ASVS; OWASP Cheat Sheet: Input Validation; check: review]
- **SEC-3** Parameterize all SQL, using bound parameters or the ORM's query API. Never build SQL with string formatting, f-strings or concatenation. This applies to migrations and analytics scripts too. [OWASP Cheat Sheet: Query Parameterization; check: scan:sql-string-assembly]
- **SEC-4** Prevent shell injection. Call subprocesses with an argument list. Never use `shell=True` on a command built from external data. [OWASP ASVS; Python documentation: subprocess security considerations; check: scan:shell-injection]
- **SEC-5** Never pass untrusted input to `eval`, `exec`, `pickle`, `yaml.load` (use `safe_load`), or anything else that runs code or creates arbitrary objects from data. [OWASP ASVS; Python documentation: pickle security; check: scan:dangerous-eval]
- **SEC-6** Every endpoint checks that the caller may access the specific record it returns. Authorize by ownership or role, never by the id being hard to guess. [OWASP Top 10: Broken Access Control; check: review]
- **SEC-7** Don't write your own cryptography. Use standard libraries (`hashlib`, `secrets`, `cryptography`) for encryption, hashing, tokens and security-related random values. Never use `random` for anything security-related, and never a hand-rolled scheme. If you store passwords at all, use a purpose-built password hash (argon2, bcrypt, scrypt). [OWASP ASVS; OWASP Cheat Sheet: Password Storage; check: review]
- **SEC-8** Secrets (API keys, tokens, database URLs, credentials) come from the environment or a secret store. They never appear in source control, logs, error messages, tracebacks sent to clients, or test fixtures. [OWASP ASVS; OWASP Cheat Sheet: Secrets Management; check: scan:secret-literal]
- **SEC-9** Errors returned to a caller never expose internals: no stack traces, query text, file paths or library versions in an API response or HTML error page. Debug mode is off in every deployed environment. [OWASP Cheat Sheet: Error Handling; check: review]
- **SEC-10** Uploaded and ingested files are size-limited and type-checked by their content, not their filename. Write them outside any directory the server executes or serves directly. Resolve any path built from external input and confirm it stays inside the intended directory. [OWASP Cheat Sheets: File Upload, Path Traversal; check: review]
- **SEC-11** Pin dependencies in a lockfile, with hashes where the tooling supports it. Install them from the official index. Audit them for known vulnerabilities as part of the build. [OWASP ASVS; PyPA packaging guidance; check: review]

## Data and persistence (DATA)

- **DATA-1** Ship every schema change as a migration in version control (Alembic or the framework's migration system). Never run `ALTER TABLE` by hand against a live database. [Industry-wide practice; check: review]
- **DATA-2** Once a migration could have run anywhere, never change its identifier. Migrations only add, and check before adding. That way a mismatched history repairs itself instead of locking the service out. [Industry-wide practice; check: review]
- **DATA-3** Store and calculate money with decimal-safe types or whole minor units: `Decimal` and `NUMERIC`. Never use `float` arithmetic on fractional amounts. Every stored amount carries its currency. [Industry-wide practice; check: advisory:money-float, review]
- **DATA-4** Store timestamps as timezone-aware UTC. Convert them only at the edges, for display. A naive `datetime.now()` never goes into stored data. [Industry-wide practice; check: review]
- **DATA-5** Writes that must happen together happen in one transaction. A failed operation leaves nothing half-written. [Industry-wide practice; check: review]
- **DATA-6** Paginate or limit any query that could return unbounded rows. A list endpoint never loads a whole table into memory. Don't run one query per row in a loop when a single query would do. [Industry-wide practice; check: review]
- **DATA-7** Customer data, fleet data, user content and credentials never go into version control. Fixtures and sample data are synthetic, or explicitly cleared for the repo. [OWASP ASVS; check: scan:secret-literal, review]

## APIs and contracts (API)

- **API-1** Declare request and response shapes as schemas. The API's generated documentation matches the real contract. [Industry-wide practice; check: review]
- **API-2** Changing a published response shape in a breaking way is a new version, not an edit. Existing callers keep working, or are migrated on purpose. [Industry-wide practice; check: review]
- **API-3** HTTP status codes reflect the real outcome. Not everything is 200. Callers can tell failures apart by status code, not only by a field in the body. [Industry-wide practice; check: review]
- **API-4** Endpoints that cost money, send messages or change state are rate-limited. Where a client may retry, they are also idempotent. [OWASP ASVS; check: review]
- **API-5** Calls to third-party services have explicit timeouts and a defined behaviour on failure. Never wait without limit, and never swallow a failure silently. [Industry-wide practice; check: review]

## Errors, logging, and observability (OBS)

- **OBS-1** Catch exceptions only where you can handle them meaningfully. A bare `except:`, or an `except Exception: pass` that hides a failure, fails review. [Python documentation: exception handling; industry-wide practice; check: review]
- **OBS-2** Logs are structured and have levels. They never contain secrets, credentials, tokens or personal data. [OWASP Cheat Sheet: Logging; check: ratchet:pii-in-log, review]
- **OBS-3** Every background job, worker and scheduled task reports success and failure somewhere a person will see it. A job that dies silently is a defect. [Industry-wide practice; check: review]
- **OBS-4** Keep user-facing messages (API error text, emails, notifications) in one place, not as literals scattered through handlers. Then wording can change without searching the code. [Industry-wide practice; check: scan:ui-string-literal]

## Concurrency and async (ASYNC)

- **ASYNC-1** Never run blocking calls (file I/O, `requests`, CPU-heavy work) inside an async event loop. Send them to a thread pool, a process pool or a worker. [Python documentation: asyncio; check: scan:blocking-call]
- **ASYNC-2** Protect shared mutable state that more than one thread, task or process uses, or design the sharing away. Module-level mutable globals are not a cache. [Industry-wide practice; check: review]
- **ASYNC-3** Long-running work started by a request runs in a queue or worker, not inside the request. [Industry-wide practice; check: review]

## Style, typing, and readability (STYLE)

- **STYLE-1** Code passes the project's formatter and linter (Black/Ruff or equivalent, run in CI). Per-file exemptions don't pile up. Formatting is never a review topic, because a tool decides it. [PEP 8; tool documentation; check: ruff, mypy]
- **STYLE-2** Public functions, methods and module boundaries have type annotations, and the type checker runs in CI. New code adds no untyped public interface. [PEP 484; industry-wide practice; check: mypy:strict]
- **STYLE-3** Names say what the thing is, using the project's established vocabulary. Use one name per concept across the whole codebase. Never add a synonym for something that already has a name. [PEP 8; industry-wide practice; check: review]
- **STYLE-4** Every public module, class and function has a docstring. It says what the code does and anything a caller must know. Comments explain constraints the code can't show; they never restate the next line. [PEP 257; check: scan:doc-comments]
- **STYLE-5** Never use mutable default arguments. `def f(x=[])` is a defect. [Python documentation: common gotchas; check: ruff:B006]

## Testing (TEST)

- **TEST-1** Every behaviour named in the requirements has a test that fails when that behaviour breaks. A test that passes no matter what the code does is a defect, not coverage. [Industry-wide practice; check: scan:test-criterion-tag]
- **TEST-2** Tests are deterministic and independent. They don't depend on run order, the current time, network access or a developer's local database. Fake external services at an interface the code owns. [Industry-wide practice; check: scan:hermetic-test]
- **TEST-3** Every bug fix includes a test that reproduces the bug and fails before the fix. [Industry-wide practice; check: review]
- **TEST-4** Test data-transformation and scoring logic against known inputs and expected outputs. Include the edge cases the domain cares about: missing fields, malformed rows, out-of-range values. [Industry-wide practice; check: review]
- **TEST-6** Test every failure path. A feature that calls a model, a network service or a file needs one test for each outcome the real thing can return: the answer, a refusal, a timeout, an empty reply, and an answer in the wrong shape. Each test checks two things: what the person sees, in the product's own words, and what they can do next. A flow tested only against a fake that always answers has not been tested. [Project rule; check: review]
- **TEST-7** A task is done only when it has been used. A screen or flow task closes only after its builder uses it in the built product as a person would: through the screens, buttons and links, not the code. The builder records what they saw: screen captures saved to disk, and the stored data read back after each action. A screenshot of the new pane alone doesn't count. The pane's window, title, settings, navigation and behaviour after relaunch are part of the flow. [Project rule; check: process, review]

## Sources

- **OWASP Application Security Verification Standard (ASVS) 5.0** — <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** (Input Validation, Query Parameterization, Password Storage, Secrets Management, File Upload, Path Traversal, Logging, Error Handling) — <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **OWASP Top 10** — <https://owasp.org/www-project-top-ten/> (CC BY-SA 4.0)
- **Python documentation** (subprocess, pickle, asyncio, exceptions, programming FAQ) — <https://docs.python.org/3/> (PSF license — referenced only)
- **PEP 8** (style), **PEP 257** (docstrings), **PEP 484** (type hints) — <https://peps.python.org/> (referenced only)
- **PyPA packaging guidance** — <https://packaging.python.org/> (referenced only)
- **The Twelve-Factor App** — <https://12factor.net/> (referenced only)

No text from these guides is copied here. Every rule is written in our own words and cites its source, so you can edit or replace this file with no license obligations.
