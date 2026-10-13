# Backend services

Read this when working on a type B or C project.

## Layering, without a UI

- **Transport is a thin edge.** Handlers parse, validate and authorize, then call plain functions.
- **Data access is confined to one layer.** No ORM sessions or raw queries in feature code.
- **Modules depend one way, no cycles.** Features never import each other.
- **The domain layer knows nothing about the wire.**

## Contracts are the product

- Declare request and response schemas that match the docs.
- A breaking change to a published shape needs a new version.
- Status codes report the real outcome, never 200 for everything.
- Rate-limit endpoints that cost, send or change state; make them idempotent where clients retry.
- Every outbound call has a timeout and defined failure behaviour.

## Messages have one home (this is rule 2 for backends)

Every string a person reads (API errors, emails, notifications, CLI output) lives in one place. Multilingual text follows `../04-localization.md`.

## Async, workers, and time

- Never block an async event loop; use a thread pool, process pool or worker.
- Long work a request starts runs in a queue.
- Protect or avoid shared mutable state; a mutable global is not a cache.
- Every job and worker reports success and failure visibly. **A job that dies silently is a defect.**

## Operability is a feature

- Logs are structured and levelled, with no secrets or personal data.
- Health and readiness are observable; bad configuration fails startup loudly.
- Configuration is validated at startup from the environment; no per-deploy constants or `os.environ` in feature code.
- Catch errors only where you can handle them. Never swallow one.

## Data safety

- Every schema change is a versioned migration; its id never changes once it may have run.
- Writes that belong together share a transaction.
- Paginate unbounded queries. A query per row is a defect.
- Money is decimal-safe with its currency. Timestamps are timezone-aware UTC.
- No customer data in version control; fixtures are synthetic or approved.

---

[← All rules](../README.md) · [Documentation](../../docs/README.md)
