---
trigger: always_on
description: Core architectural invariants for the Redis SaaS Platform
---

- PostgreSQL is the authoritative source of truth; Redis contains disposable data only.
- Keep the application a modular monolith unless a documented, measured need justifies another architecture.
- Use `redis.asyncio` and asynchronous SQLAlchemy sessions in FastAPI request paths.
- Use `Decimal` and PostgreSQL `NUMERIC` for prices; never use binary floating point for money.
- Keep API routes thin; put business orchestration in services and cache-key/policy logic in the cache layer.
- Cache keys must include every input that changes the result and must be versioned.
- Invalidate caches only after a successful PostgreSQL commit.
- Never use Redis `KEYS` in request-path cache invalidation.
- Do not store authoritative sessions, payment state, or important background jobs in the initial Redis instance.
- Do not invent authentication, tenancy, currency, rate-limit thresholds, or production domain decisions.
