# Project Roadmap

Build the application in the following sequence. Each phase should be reviewed and tested before starting the next. Do not implement every phase in one unreviewed agent run.

## Phase 1 — Project initialization and infrastructure

**Deliverables**
- Repository skeleton and agreed dependency versions.
- Docker Compose services/networks/volumes for PostgreSQL and Redis 8, plus backend/frontend/Nginx placeholders as the phase requires.
- Environment configuration and `.env.example`.
- PostgreSQL and Redis health checks.
- Private internal network for database/cache.

**Exit criteria**
- Services start and health checks work.
- Redis/PostgreSQL are not publicly exposed in production configuration.
- Secrets are not committed.

## Phase 2 — FastAPI and PostgreSQL integration

**Deliverables**
- FastAPI application and lifespan.
- Async SQLAlchemy engine/session factory.
- Product ORM model and Pydantic schemas.
- Product create/list/get/update/delete endpoints.
- Database migration strategy selected and initial schema migration created.

**Exit criteria**
- CRUD behavior and constraints are covered by tests.
- Price uses Decimal/Numeric end to end.
- API contract is documented and stable enough for frontend integration.

## Phase 3 — Redis integration foundation

**Deliverables**
- Reusable `redis.asyncio` client and bounded pool.
- Startup/shutdown lifecycle and finite timeouts.
- Centralized Redis service/dependency and cache key helpers.
- Safe behavior when Redis is unavailable.

**Exit criteria**
- Redis operations are asynchronous and use the shared client/pool.
- Product reads still work when Redis is stopped.

## Phase 4 — Production-minded caching

**Deliverables**
- Product detail cache (300-second starting TTL).
- Product list cache (120-second starting TTL).
- Dashboard stats cache (120-second starting TTL).
- Deterministic versioned keys and invalidation strategy.
- Cache metrics/logging and malformed payload handling.

**Exit criteria**
- Cache hit/miss/population/invalidation tests pass.
- Every query dimension affecting a list response is represented in its cache identity.
- No `KEYS` command is used in request-path invalidation.

## Phase 5 — Rate limiting and reliability

**Deliverables**
- Selected endpoint policies and configurable thresholds.
- Atomic Redis counter/expiry implementation.
- Trusted proxy/client identity handling.
- HTTP 429 and `Retry-After` response.
- Redis outage bypass behavior and observability.

**Exit criteria**
- Concurrency, reset/expiry, limit crossing, and Redis outage tests pass.
- Best-effort limitations are documented.

## Phase 6 — Redis security and monitoring

**Deliverables**
- Redis ACL user and least-privilege command/key access.
- Private networking and no public Redis port.
- Memory limit and reviewed eviction policy.
- Health checks and cache/Redis metrics.
- Operational logging and basic alerts/runbooks.

**Exit criteria**
- Unauthorized access is rejected.
- Application works with intended restricted Redis ACL.
- Eviction implications for counters are understood and documented.

## Phase 7 — React and Nginx integration

**Deliverables**
- React screens for catalogue, detail, and dashboard.
- Chosen frontend tooling and design system documented.
- Nginx static hosting and `/api` reverse proxy.
- Loading, empty, error, and responsive states.

**Exit criteria**
- Browser can use the application through Nginx same-origin routing.
- UI data matches API contracts and displays prices safely.

## Phase 8 — Ubuntu production deployment

**Deliverables**
- Ubuntu host preparation and Docker Compose production configuration.
- HTTPS/domain and firewall setup.
- Secure secrets/configuration.
- PostgreSQL backup and restore process.
- Deployment smoke tests, logs, monitoring, and runbooks.

**Exit criteria**
- Public access is HTTPS-only through the intended entry point.
- Database/cache ports are private.
- Authentication/authorization and tenant scope are resolved before real customer access.
- Restore and operational checks are tested.
