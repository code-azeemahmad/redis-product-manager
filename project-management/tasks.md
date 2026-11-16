# Task Backlog

Status values: `todo`, `in_progress`, `blocked`, `done`. A task is `done` only after implementation and its acceptance tests have been verified.

## Phase 1 — Initialization and infrastructure

- [ ] P1-01 Confirm runtime versions and dependency management approach. (`todo`)
- [ ] P1-02 Create repository skeleton and ignore rules. (`todo`)
- [ ] P1-03 Add `.env.example` and validated settings design. (`todo`)
- [ ] P1-04 Create Docker Compose networks, volumes, and service definitions. (`todo`)
- [ ] P1-05 Configure PostgreSQL/Redis health checks and private networking. (`todo`)
- [ ] P1-06 Verify local startup and service connectivity. (`todo`)

## Phase 2 — FastAPI and PostgreSQL

- [ ] P2-01 Decide product ID, field lengths, price precision/currency, and timestamps. (`blocked` until decisions)
- [ ] P2-02 Select migration tooling (Alembic recommended). (`blocked` until decision)
- [ ] P2-03 Implement async SQLAlchemy engine/session lifecycle. (`todo`)
- [ ] P2-04 Implement product ORM model and database constraints. (`todo`)
- [ ] P2-05 Implement Pydantic product schemas with Decimal-safe price. (`todo`)
- [ ] P2-06 Implement create/list/get/update/delete services and routes. (`todo`)
- [ ] P2-07 Add API integration tests and pagination/sorting validation. (`todo`)

## Phase 3 — Redis integration

- [ ] P3-01 Configure Redis 8 and `redis.asyncio` client. (`todo`)
- [ ] P3-02 Add bounded connection pool and finite timeouts. (`todo`)
- [ ] P3-03 Add lifespan startup/shutdown and dependency injection. (`todo`)
- [ ] P3-04 Implement controlled cache bypass on Redis errors. (`todo`)
- [ ] P3-05 Test product endpoints with Redis unavailable. (`todo`)

## Phase 4 — Caching

- [ ] P4-01 Implement versioned product-detail cache (300s). (`todo`)
- [ ] P4-02 Implement normalized product-list cache (120s). (`todo`)
- [ ] P4-03 Implement list generation invalidation. (`todo`)
- [ ] P4-04 Confirm dashboard inventory-value definition. (`blocked` until decision)
- [ ] P4-05 Implement dashboard statistics cache (120s). (`todo`)
- [ ] P4-06 Add post-commit invalidation and cache metrics. (`todo`)
- [ ] P4-07 Test hit/miss, stale payload, invalidation, and failure cases. (`todo`)

## Phase 5 — Rate limiting and reliability

- [ ] P5-01 Select endpoints, thresholds, windows, and caller identity. (`blocked` until decision)
- [ ] P5-02 Configure trusted Nginx proxy headers. (`todo`)
- [ ] P5-03 Implement atomic fixed-window Redis counters. (`todo`)
- [ ] P5-04 Add HTTP 429 and `Retry-After`. (`todo`)
- [ ] P5-05 Implement and test best-effort Redis outage bypass. (`todo`)

## Phase 6 — Security and observability

- [ ] P6-01 Create Redis ACL user and least-privilege rules. (`todo`)
- [ ] P6-02 Set Redis memory/eviction policy and document counter implications. (`todo`)
- [ ] P6-03 Add liveness/readiness and dependency health reporting. (`todo`)
- [ ] P6-04 Add structured logs and bounded-cardinality metrics. (`todo`)
- [ ] P6-05 Resolve auth/tenant policy before public customer deployment. (`blocked` until decision)

## Phase 7 — Frontend and Nginx

- [ ] P7-01 Select frontend build tool/router/test stack/design system. (`todo`)
- [ ] P7-02 Implement product catalogue and UI states. (`todo`)
- [ ] P7-03 Implement product detail. (`todo`)
- [ ] P7-04 Implement dashboard and decimal-safe display. (`todo`)
- [ ] P7-05 Configure Nginx static hosting and API proxy. (`todo`)
- [ ] P7-06 Add frontend and E2E tests. (`todo`)

## Phase 8 — Production deployment

- [ ] P8-01 Confirm Ubuntu version, host, domain, and TLS approach. (`blocked` until decision)
- [ ] P8-02 Configure production secrets, firewall, and private services. (`todo`)
- [ ] P8-03 Configure PostgreSQL backup and test restore. (`todo`)
- [ ] P8-04 Add monitoring/alerts and operational runbooks. (`todo`)
- [ ] P8-05 Run deployment smoke and resilience tests. (`todo`)

## Rules for updating this file

- Keep task IDs stable; do not renumber completed work.
- Add a short note and date when a task is blocked or its scope changes.
- Move tasks to `done` only after verification; link or name the tests/commands in `progress.md`.
