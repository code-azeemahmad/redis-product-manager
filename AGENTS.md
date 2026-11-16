# Shared Agent Instructions

These instructions apply to AI coding agents working in this repository.

## First steps

1. Read `README.md` and the relevant documents under `docs/` before changing code.
2. Read `project-management/roadmap.md`, `project-management/tasks.md`, and `project-management/progress.md` before choosing work.
3. Inspect the existing repository and current implementation. Do not assume a planned file or feature already exists.
4. If code conflicts with documentation, report the discrepancy and propose a correction; do not silently make broad architectural changes.

## Architectural invariants

- PostgreSQL is the authoritative source of truth for product data.
- Redis is disposable cache and best-effort rate-limit storage only in the initial scope.
- Product correctness must not depend on Redis being available.
- Use `redis.asyncio` and asynchronous SQLAlchemy sessions; do not introduce synchronous database or Redis calls into async request paths.
- Keep Redis private to the application network. Do not expose Redis publicly.
- Use environment-based configuration. Never commit real credentials, tokens, or production secrets.
- Use `Decimal` / PostgreSQL `NUMERIC` for money. Never use binary floating point for price calculations or serialization.
- Cache keys must include every input that can change a cached result.
- Invalidate affected cache entries only after a successful database commit.
- Do not use Redis `KEYS` in application request paths for cache invalidation.
- Do not store authoritative sessions, payment state, or business-critical background jobs in the initial Redis instance.

## Implementation discipline

- Implement only the agreed scope in `docs/00-product/PRD.md` and `docs/00-product/requirements.md`.
- Work in small, reviewable increments. Do not implement the entire roadmap in one change unless explicitly requested.
- Prefer clear, modular code over premature abstraction.
- Reuse the existing configuration, dependency-injection, logging, and error-handling patterns.
- Validate inputs at API boundaries with Pydantic and enforce domain constraints in the service/database layers as appropriate.
- Do not silently add dependencies. Explain why a dependency is needed and update the stack documentation and dependency manifests.
- Do not make up product requirements, business rules, credentials, rate limits, deployment domains, or provider-specific settings.

## Verification and documentation

- Add or update tests for every behavior change.
- Run the narrow relevant tests first, then the broader test suite when practical.
- Report commands run and their outcomes accurately. Never claim a test passed if it was not run.
- Update `project-management/tasks.md` and `project-management/progress.md` after completing verified work.
- Update the relevant architecture/API/security/operations documents when implementation changes a documented contract.
- Keep `README.md` setup and run instructions synchronized with the actual repository.

## Change safety

- Do not delete, overwrite, or restructure existing user work without explaining the impact and obtaining approval when the change is destructive or broad.
- Do not run destructive database commands against non-disposable environments.
- Do not log passwords, access tokens, connection strings, full authorization headers, or sensitive customer data.
- Treat cache data as untrusted input: validate deserialized payloads and handle malformed or old cache entries safely.
- If a requirement is ambiguous and the choice affects data ownership, security, public API compatibility, or deployment, stop and document the decision needed rather than guessing.
