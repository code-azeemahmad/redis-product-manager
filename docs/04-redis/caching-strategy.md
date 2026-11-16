# Redis Caching Strategy

## 1. Purpose and constraints

Redis 8 is an optimization layer for disposable read data. PostgreSQL remains authoritative. Cache loss, eviction, flush, or restart must not cause permanent data loss.

Use the asynchronous Python client `redis.asyncio` and a reusable bounded connection pool created during FastAPI lifespan.

## 2. Cache-aside flow

1. Build a deterministic, versioned key.
2. Attempt a Redis read with a finite timeout.
3. If a valid value exists, validate/decode it and return it (hit).
4. If missing or invalid, query PostgreSQL (miss/rebuild).
5. Attempt a Redis write with the appropriate TTL.
6. Return the database result even if the Redis write fails.

Malformed JSON, unsupported cache schema versions, or invalid cached payloads are cache misses. Delete the bad entry when possible and rebuild from PostgreSQL.

## 3. Cache catalog

| Data | Key family | Starting TTL |
|---|---|---:|
| Product detail | `v1:product:{product_id}` | 300 seconds |
| Product listing | `v1:products:list:...` | 120 seconds |
| Dashboard statistics | `v1:dashboard:stats` | 120 seconds |

These are initial project values, not universal production recommendations. Make TTLs configurable or centralized in cache policy rather than scattering constants through routes.

## 4. Key construction

Centralize key construction in `backend/app/cache/keys.py`.

A product list key must encode every result-affecting parameter: normalized category, page/offset, limit, sort field, sort direction, and tenant identifier if tenancy is implemented. Normalize category consistently (including case/whitespace rules) and use a stable serialization or hash for complex filter sets.

Example readable key:

```text
v1:products:list:category:electronics:page:1:limit:20
```

Recommended invalidation-friendly form:

```text
v1:products:list:g{list_generation}:{query_signature}
v1:dashboard:stats:g{dashboard_generation}
```

A product write increments the relevant generation key after commit. New reads then use a new namespace, making old entries unreachable until TTL expiry. This avoids blocking `KEYS` or broad `SCAN` deletion in request handlers. Generation initialization and increment behavior must be race-safe and covered by tests.

## 5. Invalidation matrix

| Mutation | Detail key | List generation | Dashboard generation |
|---|---|---|---|
| Create | N/A | Increment | Increment |
| Update | Delete `v1:product:{id}` | Increment | Increment |
| Delete | Delete `v1:product:{id}` | Increment | Increment |

Only invalidate after the PostgreSQL transaction commits. A Redis invalidation error must be logged/metricized and must not reverse a committed database result. The remaining TTL bounds stale cache exposure when invalidation fails.

## 6. Serialization

- Serialize only the fields required by the response.
- Represent monetary values as decimal strings, not JSON floating-point numbers.
- Include a schema/version marker if payload shape may evolve independently of key version.
- Validate data after deserialization; never assume cache content is trustworthy.
- Keep payload size reasonable. Avoid caching unbounded result sets.

## 7. Timeouts, pools, and failure handling

- Set finite connect/socket/command timeouts.
- Bound pool size based on expected application concurrency and Redis capacity.
- On Redis read timeout/error, log a structured event, increment an error metric, and query PostgreSQL.
- On Redis write timeout/error, log/measure it and return the database result.
- Avoid retry storms. Do not add long synchronous sleeps or unbounded retries inside request handlers.
- Monitor the percentage of requests bypassing Redis; elevated bypass rates increase PostgreSQL load.

## 8. Stampede and stale-fill considerations

The initial implementation can accept duplicate database reads on simultaneous misses if load is small. Do not add distributed locks prematurely. If measured load requires single-flight or locking, define lock TTL, ownership token, release safety, and timeout behavior.

Cache-aside plus post-commit invalidation is not a strict distributed consistency protocol. A concurrent in-flight miss can theoretically repopulate stale data around a write. Document this limitation and test the implemented mitigation. If stronger consistency is required, introduce versioned entity reads or an outbox/event strategy as a separately reviewed design.

## 9. Metrics

At minimum, track cache hits, misses, read/write errors, invalidation errors, cache command latency, and Redis memory/evictions. Use bounded labels; never label metrics with raw IDs or arbitrary user input.
