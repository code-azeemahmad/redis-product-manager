# Implementation Plan

## Working method

1. Select one small task from the current phase in `roadmap.md`.
2. Read the relevant architecture/API/data/security documentation.
3. Inspect current code before editing.
4. Propose a short plan and identify files likely to change.
5. Implement the smallest coherent increment.
6. Add or update tests.
7. Run tests and report exact results.
8. Update documentation, `tasks.md`, and `progress.md`.
9. Review the diff for accidental scope expansion, secrets, blocking I/O, and inconsistent contracts.

## Suggested implementation order

### Milestone 1 — Service skeleton

- Establish repository and dependency manifests.
- Add configuration/settings module.
- Add Dockerfiles and Compose service definitions.
- Add PostgreSQL and Redis health checks.
- Verify private networking and persistent PostgreSQL volume.

### Milestone 2 — PostgreSQL domain layer

- Confirm unresolved product data decisions.
- Select and configure migration tooling.
- Implement ORM model and Pydantic schemas.
- Implement async engine/session lifecycle.
- Add service-layer CRUD and route handlers.
- Test constraints, Decimal values, not-found behavior, and pagination.

### Milestone 3 — Redis foundation

- Add Redis settings, ACL and local configuration.
- Create one async Redis client/pool in app lifespan.
- Add finite timeouts and health reporting.
- Add cache service abstraction and key builder.
- Test graceful bypass with Redis stopped.

### Milestone 4 — Cache features

- Implement detail cache and invalidation.
- Implement list cache with normalized query identity and generation invalidation.
- Implement dashboard cache and invalidation.
- Add hit/miss/error/invalidation metrics.
- Test invalidation and concurrency edge cases.

### Milestone 5 — Rate limiting

- Agree endpoints and thresholds.
- Agree trusted client identity/proxy configuration.
- Implement atomic counter + expiry.
- Add 429/Retry-After behavior and outage bypass.
- Test concurrency and fixed-window boundaries.

### Milestone 6 — Frontend and deployment

- Select frontend build tool, router, component approach, and test stack.
- Implement catalogue, detail, and dashboard UI.
- Integrate Nginx and FastAPI.
- Add production TLS, secrets, firewall, backups, monitoring, and runbooks.

## Agent execution contract

An AI agent must not skip ahead to a later milestone because it appears easy. If an upcoming milestone requires a decision, add the question to `docs/01-architecture/architecture-decisions.md` and leave implementation blocked until it is answered. Agents may make reversible, low-risk implementation details consistent with this documentation, but must not decide auth, tenancy, money/currency semantics, production exposure, or strict rate-limit behavior independently.
