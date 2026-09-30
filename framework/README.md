# Framework

Shared building blocks for the Minimals Flask app: base classes, API
utilities, exceptions, and infrastructure helpers.

## Modules

- `base` — DTOBase, PresenterBase, ServiceBase, RepositoryBase
- `api` — response helpers, blueprint factory, error handlers, pagination
- `exceptions` — DomainException hierarchy
- `types` — type aliases
- `extensions` — Flask extension singletons
- `infra` — config, errors, SPA serving, health blueprint, migrations, UUIDv7
- `auth` — RBAC helpers (`require_role`, `require_owner_or_role`)
- `logging` — structured JSON logging, request middleware, metrics, alerting

`framework/` is service-agnostic and must not import from `app/`. App-specific
wiring lives in `app/infra/`.