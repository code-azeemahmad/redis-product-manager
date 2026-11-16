# System Architecture

## 1. Architecture overview

```text
                         Browser
                            |
                            v
                     React Frontend
                            |
                            v
                       Nginx :80
                      /          \
            static frontend      /api/* proxy
                                  |
                                  v
                            FastAPI Backend
                              /       \
                             /         \
                            v           v
                       PostgreSQL     Redis 8
                      source of       disposable cache
                         truth         + best-effort counters
```

Nginx is the public HTTP entry point. It serves the built React application and forwards API requests to FastAPI. FastAPI coordinates application logic and communicates asynchronously with PostgreSQL and Redis.

## 2. Responsibilities and trust boundaries

- **Browser:** renders UI and sends HTTP requests. It must not connect directly to PostgreSQL or Redis.
- **Nginx:** serves frontend assets, proxies `/api/` and health requests as configured, sets/forwards proxy headers, and applies appropriate request-size/time limits.
- **FastAPI:** validates requests, executes business logic, manages dependency lifetimes, and formats API responses.
- **PostgreSQL:** owns all durable product records and is the authoritative source for product/dashboard calculations.
- **Redis:** stores rebuildable cache entries and best-effort rate-limit counters. Redis contents must be safe to lose.
- **Docker Compose networks:** keep database/cache services on private application networks. Only intended entry points are published to the host.

## 3. Request flows

### 3.1 Cached product detail

1. Browser requests `GET /api/products/{id}` through Nginx.
2. FastAPI validates the identifier and derives the versioned cache key.
3. FastAPI attempts a bounded Redis `GET`.
4. On a valid cache hit, deserialize and validate the payload, then return it.
5. On miss, malformed payload, or Redis failure, fetch the product from PostgreSQL.
6. If the product exists, attempt to cache its serialized response with the detail TTL.
7. Return the response. Cache population failure must not fail the product read.

### 3.2 Product mutation

1. FastAPI validates the request.
2. SQLAlchemy writes the product inside a transaction.
3. Commit PostgreSQL successfully.
4. Attempt to invalidate the product detail key (where applicable), product list namespace, and dashboard namespace.
5. Log/measure invalidation failure. Do not report a committed database write as rolled back because Redis invalidation failed.
6. Return the database-backed result.

The bounded TTL limits how long stale entries may remain when invalidation fails. The initial design provides eventual consistency, not a distributed transaction between PostgreSQL and Redis.

### 3.3 Product list

The cache identity includes all result-affecting parameters: category, page/offset, limit, sort field, sort direction, and tenant identifier if tenancy is added later. Normalize equivalent inputs before constructing keys.

### 3.4 Dashboard

FastAPI computes aggregates from PostgreSQL on a cache miss, then caches the response for 120 seconds. The inventory value definition must be confirmed as `SUM(price * stock)` before it is treated as a business/accounting metric.

## 4. Asynchronous resource lifecycle

- Create one SQLAlchemy async engine and session factory for the application process.
- Create/reuse an asynchronous Redis client with a bounded connection pool.
- Initialize long-lived clients during FastAPI lifespan startup and close them during shutdown.
- Use one database session per request/unit of work; do not share an `AsyncSession` concurrently across unrelated tasks.
- Keep network timeouts finite. Do not allow Redis failures to hang API requests.
- Use application dependencies to provide sessions and service clients rather than constructing new pools inside routes.

## 5. Failure and consistency model

| Condition | Expected behavior |
|---|---|
| Redis unavailable on read | Bypass cache and query PostgreSQL; record degraded cache status |
| Redis unavailable on cache write | Return database result; record cache-write failure |
| Redis unavailable during invalidation | Keep committed database write successful; stale data may survive until TTL |
| PostgreSQL unavailable | Core product operations cannot be fulfilled; return controlled service error |
| Malformed cache value | Delete/ignore the entry and rebuild from PostgreSQL |
| Cache stampede | Initial implementation may allow duplicate misses; add per-key single-flight/lock only if measured need justifies complexity |

Do not use Redis as a fallback database. Do not return unverified stale cached data indefinitely.

## 6. Cache key strategy

Use a common prefix and explicit schema version, for example `v1:`. Keep key construction centralized in `backend/app/cache/keys.py`.

Recommended key families:

- `v1:product:{product_id}`
- `v1:products:list:g{generation}:{normalized_filter_signature}`
- `v1:dashboard:stats:g{generation}`
- `v1:cachegen:products:list`
- `v1:cachegen:dashboard:stats`

The supplied example `v1:products:list:category:electronics:page:1:limit:20` illustrates the query dimensions. A generation component is recommended so a write can invalidate a whole family by incrementing a small generation key instead of running `KEYS`/`SCAN` in a request path. If a simpler exact-key tracking strategy is selected instead, document it and test cleanup behavior. Generation keys need a well-defined initial value and safe handling if absent.

## 7. Observability

Capture request counts/latency, database failures/latency, cache hits/misses/errors, invalidation failures, rate-limit decisions, Redis pool/command errors, and service health. Avoid high-cardinality metric labels such as raw product IDs or raw IP addresses.

## 8. Architecture constraints

- Start as a modular monolith; do not split services without a measured reason.
- Do not allow frontend/browser access to Redis or PostgreSQL.
- Keep authoritative state in PostgreSQL.
- Keep cache policy and key creation out of route handlers where possible.
- Avoid blocking I/O inside async handlers.
- Keep deployment configuration explicit and reviewable.
