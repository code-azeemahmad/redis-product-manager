# Architecture Decisions and Open Questions

This document records decisions already implied by the project brief and items that must be confirmed. Add dated entries when a decision is made.

## Accepted decisions

### AD-001 — PostgreSQL is authoritative

**Decision:** PostgreSQL stores durable product data. Redis stores disposable copies and best-effort counters only.

**Reason:** Cache loss or Redis outage must not destroy product data or stop core product operations.

### AD-002 — Cache-aside for read models

**Decision:** Read Redis first; on miss, read PostgreSQL and then attempt to populate Redis.

**Reason:** Simple lifecycle, lazy population, and easy rebuild after eviction/restart.

### AD-003 — Invalidate after successful commit

**Decision:** Commit PostgreSQL writes before attempting Redis invalidation.

**Reason:** Do not evict data for a transaction that later rolls back, and do not report a committed write as failed solely because Redis is unavailable.

### AD-004 — Async I/O

**Decision:** Use `redis.asyncio` and async SQLAlchemy sessions in FastAPI request paths.

**Reason:** Consistent asynchronous I/O model and bounded reusable connection pools.

### AD-005 — Redis scope is limited

**Decision:** Initial Redis use is disposable caching and best-effort rate limiting. Do not put authoritative sessions, payment state, or important jobs in this Redis instance.

**Reason:** The project has not designed persistence, recovery, or isolation guarantees for those workloads.

## Decisions required before production

| ID | Question | Suggested default / consideration | Status |
|---|---|---|---|
| OQ-01 | Is the app single-tenant or multi-tenant? | Keep initial schema single-tenant; do not claim SaaS tenant isolation until modeled and tested | Open |
| OQ-02 | Is authentication required? | Must be decided before public production use; not in initial endpoint list | Open |
| OQ-03 | Product primary key type? | Integer matches supplied sample; confirm before migration | Open |
| OQ-04 | Price precision and currency? | Choose `NUMERIC(p,2)` precision and an explicit currency/business rule; no currency is currently specified | Open |
| OQ-05 | Product field limits and nullability? | Define name/category maximum lengths and whether category is mandatory | Open |
| OQ-06 | Pagination and sorting contract? | Define default/max page size and allowlisted sort fields | Open |
| OQ-07 | List invalidation implementation? | Prefer generation-based namespace invalidation to avoid key scans | Proposed |
| OQ-08 | Dashboard inventory value meaning? | Confirm `SUM(price * stock)` is intended and not an accounting valuation | Open |
| OQ-09 | Rate-limit thresholds and identity? | Configure per endpoint/window; confirm client identity and proxy trust | Open |
| OQ-10 | Rate-limit strictness? | Best-effort only for initial scope; isolate strict counters if needed | Open |
| OQ-11 | Database migrations? | Alembic is recommended for SQLAlchemy | Proposed |
| OQ-12 | Redis outage capacity limits? | Define DB connection/concurrency limits and alerts for cache bypass mode | Open |
| OQ-13 | Production domain and TLS termination? | Use HTTPS; select certificate/renewal and termination approach | Open |
| OQ-14 | Backup/restore and retention? | Define PostgreSQL backup schedule, retention, and restore tests | Open |
| OQ-15 | Frontend build tool/router/design system? | Select before frontend implementation | Open |

## Decision log template

For each future decision, append:

```text
### AD-XXX — Short title
Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded
Context: What problem needs a decision?
Decision: What was selected?
Alternatives: What else was considered?
Consequences: Trade-offs and follow-up work.
```
