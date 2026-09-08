# Backend services — the reasoning layer

For project types B (backend service) and C (data/ML pipeline). This is the
counterpart to what `02-architecture-and-code.md`, `04-localization.md`, and
`05-design-and-ui.md` are for apps with a screen: the reasoning behind the
checkable rules. The checkable versions live in
`platform/domain-rules-python.md` (add a Node/Go file when a project needs one).

Read `PROJECT-TYPES.md` first — it says which universal rules still apply and
which app rules do not.

## Layering, without a UI

The app rule is "screens display, view models prepare, services hold business
rules, repositories do data access." The backend shape of the same idea:

- **Transport is a thin edge.** A request handler parses, validates, and
  authorizes — then calls a function that a worker, a test, or a script could
  call identically. Business logic that only works when reached through HTTP
  is business logic in the wrong place.
- **Data access is confined to one layer**, exactly as in an app. Handlers,
  business logic, and analytics scripts call that layer; ORM sessions and raw
  queries do not spread through feature code.
- **Modules depend one way, no cycles.** Feature modules depend on shared
  domain abstractions, never on each other. Import cycles are a build failure.
- **The domain layer knows nothing about the wire.** Request and response
  models are transport types; they do not become the types business rules
  pass around.

## Contracts are the product

An app's contract is its screens; a backend's contract is its API, and it is
consumed by code that cannot ask questions.

- Request and response shapes are declared as schemas and the generated
  documentation reflects the real contract.
- Breaking a published shape is a versioned change, not an edit.
- Status codes carry the real outcome — not everything is 200 with a body
  field.
- Endpoints that cost money, send messages, or mutate state are rate-limited
  and idempotent where a client may retry.
- Outbound calls have explicit timeouts and a defined failure behaviour.

## Messages have one home (this is rule 2 for backends)

A backend has little user-facing text, so a localization catalog is usually
ceremony. What is **not** optional: every string a person will eventually
read — API error text, emails, notifications, CLI output — lives in one
place, not scattered as literals through handlers, so wording changes without
hunting through code. If the product does serve multiple languages from the
backend, then `04-localization.md` applies in full to that text.

## Async, workers, and time

The app rules about not blocking the UI generalize to not blocking the loop:

- Blocking work does not run inside an async event loop; it goes to a thread
  pool, a process pool, or a worker.
- Long-running work triggered by a request runs in a queue, not in the
  request.
- Shared mutable state across threads, tasks, or processes is protected, or
  the design avoids the sharing. A module-level mutable global is not a cache.
- Every scheduled job and worker reports success and failure somewhere a
  human sees. **A job that dies silently is a defect** — this is the backend
  version of a screen that renders nothing.

## Operability is a feature

An app that crashes tells its user immediately; a service can fail quietly for
days.

- Logs are structured, leveled, and free of secrets and personal data.
- Health and readiness are observable, and startup fails loudly on missing or
  invalid configuration rather than serving broken.
- Configuration comes from environment or a validated config object loaded at
  startup — never constants edited per deployment, never `os.environ` read
  deep inside feature code.
- Errors are caught where they can be handled meaningfully. A swallowed
  exception is worse than a crash, because it removes the evidence.

## Data safety

- Every schema change ships as a migration in version control. A migration
  identifier, once it can have run anywhere, never changes.
- Writes that must happen together happen in one transaction.
- Queries that can return unbounded rows are paginated. A loop issuing one
  query per row is a defect, not a performance note.
- Money is decimal-safe and carries its currency; timestamps are stored
  timezone-aware in UTC.
- Customer data never enters version control — fixtures are synthetic or
  explicitly cleared.
