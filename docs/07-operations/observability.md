# Observability and Operational Signals

## 1. Goals

Operators should be able to distinguish application failures, PostgreSQL failures, and Redis degradation. Redis cache errors should be visible without making Redis a required dependency for core product availability.

## 2. Logs

Use structured logs. Include, where appropriate:

- Timestamp, severity, service/component, environment.
- Request/correlation ID.
- Route template and HTTP status (avoid raw high-cardinality paths where IDs appear).
- Request duration.
- Dependency operation and duration.
- Cache outcome (`hit`, `miss`, `read_error`, `write_error`, `invalidate_error`).
- Rate-limit decision (`allowed`, `blocked`, `bypassed_due_to_redis_error`).

Never log passwords, secret values, connection strings, authorization headers, or full sensitive request bodies.

## 3. Metrics

Recommended metrics:

- HTTP request count and latency distribution by route template/status.
- PostgreSQL connection pool usage, query latency, and errors.
- Redis command latency/errors and connection-pool usage.
- Cache hits, misses, write failures, invalidation failures, and bypass rate.
- Redis memory usage, evictions, key count, and rejected connections.
- Rate-limit allowed/blocked/bypassed counts by bounded policy name.
- Container CPU/memory/restarts and disk usage.

Avoid labels containing product IDs, raw IPs, arbitrary category values, or other unbounded user input.

## 4. Health endpoints

- `/health/live`: process liveness only.
- `/health/ready`: PostgreSQL readiness plus safe status for optional dependencies. Redis degraded status must be visible but should not alone make product operations unavailable.
- Keep health responses free of secrets, full connection strings, stack traces, and internal infrastructure details.

## 5. Alert candidates

Set thresholds based on observed baseline rather than guessing now. Consider alerts for:

- Sustained elevated 5xx rate or request latency.
- PostgreSQL unavailable, pool exhaustion, or disk pressure.
- High Redis error/bypass rate or sustained high memory/eviction rate.
- Cache invalidation failures.
- Repeated Redis authentication failures.
- Container restart loops or low host disk space.
- Backup failure or missed backup schedule.

## 6. Operational runbooks to add later

Create concise runbooks when deployment exists for: Redis unavailable, PostgreSQL unavailable, disk full, credential rotation, restore from backup, and rolling application update.
