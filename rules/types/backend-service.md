# Backend services — the reasoning layer

This file is for project types B (backend service) and C (data/ML pipeline). It explains the reasoning behind the checkable rules, as `02-architecture-and-code.md`, `04-localization.md` and `05-design-and-ui.md` do for apps with a screen. The checkable rules are in `platform/domain-rules-python.md`. (Add a Node or Go file when a project needs one.)

Read `PROJECT-TYPES.md` first. It says which universal rules still apply and which app rules do not.

## Layering, without a UI

The app rule is: screens display, view models prepare, services hold business rules, and repositories access data. On a backend, the same idea looks like this:

- **Transport is a thin edge.** A request handler parses, validates and authorizes the request. Then it calls a function that a worker, a test or a script could call in exactly the same way. Business logic that only works when called through HTTP is in the wrong place.
- **Data access is confined to one layer**, just as in an app. Handlers, business logic and analytics scripts call that layer. ORM sessions and raw queries do not appear in feature code.
- **Modules depend one way, no cycles.** Feature modules depend on shared domain abstractions, never on each other. An import cycle fails the build.
- **The domain layer knows nothing about the wire.** Request and response models are transport types. Business rules do not pass them around.

## Contracts are the product

An app's contract is its screens. A backend's contract is its API, and the code that uses it cannot ask questions.

- Request and response shapes are declared as schemas, and the generated documentation matches the real contract.
- Breaking a published shape requires a new version, not an edit.
- Status codes report the real outcome. Do not return 200 for everything with the outcome in a body field.
- Endpoints that cost money, send messages or change state are rate-limited. They are also idempotent wherever a client may retry.
- Outbound calls have explicit timeouts and defined behavior on failure.

## Messages have one home (this is rule 2 for backends)

A backend has little user-facing text, so a localization catalog is usually unnecessary. What is **not** optional: every string a person will read (API error text, emails, notifications, CLI output) lives in one place, not as literals scattered through handlers. Then wording can change without searching the code. If the backend serves text in more than one language, `04-localization.md` applies in full to that text.

## Async, workers, and time

The app rule "don't block the UI" becomes "don't block the event loop":

- Blocking work never runs inside an async event loop. Send it to a thread pool, a process pool or a worker.
- Long-running work started by a request runs in a queue, not inside the request.
- Mutable state shared across threads, tasks or processes is protected, or the design avoids sharing it. A module-level mutable global is not a cache.
- Every scheduled job and worker reports success and failure somewhere a person will see it. **A job that dies silently is a defect**, just like a screen that renders nothing.

## Operability is a feature

When an app crashes, its user knows immediately. A service can fail quietly for days.

- Logs are structured, have levels, and contain no secrets or personal data.
- Health and readiness can be observed. On missing or invalid configuration, startup fails loudly instead of serving a broken service.
- Configuration comes from the environment or from a validated config object loaded at startup. Never edit constants per deployment, and never read `os.environ` deep inside feature code.
- Catch errors only where you can handle them properly. A swallowed exception is worse than a crash, because it destroys the evidence.

## Data safety

- Every schema change ships as a migration in version control. Once a migration could have run anywhere, its identifier never changes.
- Writes that must happen together run in one transaction.
- Queries that can return an unlimited number of rows are paginated. A loop that runs one query per row is a defect, not just a performance issue.
- Money uses a decimal-safe type and carries its currency. Timestamps are stored timezone-aware, in UTC.
- Customer data never goes into version control. Fixtures are synthetic or explicitly approved.

---

[← All rules](../README.md) · [Priority rules](../00-priority-rules.md) · [Project types](../PROJECT-TYPES.md) · [Documentation](../../docs/README.md)
