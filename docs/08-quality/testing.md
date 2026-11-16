# Testing Strategy and Acceptance Matrix

## 1. Testing principles

- Test externally observable behavior, not only private implementation details.
- Use disposable test databases and Redis instances/containers for integration tests.
- Keep unit tests fast and deterministic.
- Test both normal operation and dependency failure.
- Do not claim completion without recording the tests and commands actually run.

## 2. Backend test layers

### Unit tests

- Pydantic validation and Decimal parsing/serialization.
- Cache key normalization and versioning.
- Rate-limit key construction and policy selection.
- Product service business rules.
- Dashboard aggregate calculations and empty-dataset behavior.

### Integration tests

- SQLAlchemy async session and transaction behavior against PostgreSQL.
- Product CRUD persistence and status codes.
- Redis cache hit/miss/population.
- Invalidation after committed writes.
- Malformed cache value recovery.
- Redis unavailable/timeouts during reads, writes, and invalidation.
- Atomic rate-limit increments and expiry behavior.

### API tests

- Valid and invalid request bodies.
- Missing product returns 404.
- Pagination and sorting bounds/allowlist.
- Consistent error responses.
- Rate limit returns 429 and `Retry-After` when exceeded.
- Health endpoint behavior with PostgreSQL/Redis healthy and unhealthy.

## 3. Required behavior matrix

| Scenario | Expected result |
|---|---|
| First product detail read | PostgreSQL lookup; Redis cache populated if Redis is available |
| Second equivalent detail read | Cache hit; response matches source data |
| Product listing repeated with same filters | Cache hit for same normalized query |
| Different page/filter/sort | Different cache identity; no cross-query cache contamination |
| Create product | PostgreSQL row created; list/dashboard cache generations invalidated after commit |
| Update product | PostgreSQL updated; detail/list/dashboard cache invalidated |
| Delete product | PostgreSQL row deleted; detail/list/dashboard cache invalidated |
| Redis read error | Core read continues using PostgreSQL |
| Redis write error | Database-backed response still succeeds |
| Redis invalidation error after commit | Write remains successful; failure is logged/metricized; TTL bounds stale entry lifetime |
| Malformed cache payload | Entry ignored/removed; PostgreSQL used to rebuild |
| Rate limit reached | HTTP 429 and correct `Retry-After` |
| Redis unavailable during limiter check | Best-effort check bypassed and degradation recorded |
| PostgreSQL unavailable | Controlled error; no fake success from Redis cache for authoritative write paths |
| Health check with Redis down | Liveness remains healthy; readiness reflects PostgreSQL availability and Redis degradation separately |

## 4. Frontend tests

After selecting the frontend test stack, cover:

- Catalogue loading/empty/error/success states.
- Category and pagination behavior.
- Product detail and 404 state.
- Dashboard metrics and decimal-safe display.
- Accessible labels, keyboard navigation, responsive layout, and mutation confirmation if management UI is included.

## 5. End-to-end and deployment tests

Use Docker Compose to validate the whole request path through Nginx. Verify that static assets load, `/api` is proxied correctly, CORS/routing is correct, and service health reflects real dependencies. Run a smoke test after deployment.

## 6. Performance and resilience checks

- Compare cache miss vs. hit latency under a controlled test dataset.
- Confirm connection pools are bounded.
- Test behavior during Redis restart/unavailability.
- Observe PostgreSQL load while cache is bypassed.
- Test large page limits and dashboard query behavior.
- Do not set performance targets until a target environment and expected load are defined.

## 7. Completion standard

A task is complete only when its acceptance criteria are met, automated tests pass (or known failures are recorded), documentation is updated, and the current task/progress files reflect the verified state.
