# Product and System Requirements

## 1. Functional requirements

| ID | Requirement | Initial behavior | Redis involvement |
|---|---|---|---|
| FR-01 | Create product | `POST /api/products`; validate and persist product in PostgreSQL | Invalidate product-list and dashboard cache namespaces after commit |
| FR-02 | List products | `GET /api/products`; support defined filtering, pagination, and sorting | Cache each distinct query result |
| FR-03 | Get product | `GET /api/products/{id}` | Cache product detail |
| FR-04 | Update product | `PUT /api/products/{id}`; persist changes | Invalidate detail, list, and dashboard caches after commit |
| FR-05 | Delete product | `DELETE /api/products/{id}` | Invalidate detail, list, and dashboard caches after commit |
| FR-06 | Dashboard statistics | `GET /api/dashboard/stats` | Cache aggregate response |
| FR-07 | Rate limiting | Apply configured limits to selected endpoints | Redis counters; best-effort in initial scope |
| FR-08 | Health checks | Expose liveness and readiness/dependency health | Report Redis status without making Redis mandatory for product availability |

## 2. Product data requirements

Initial product fields:

| Field | Type/meaning | Rules |
|---|---|---|
| `id` | Generated product identifier | Integer is suggested by the supplied example; confirm before migration |
| `name` | Product name | Required; trim whitespace; define maximum length in schema |
| `price` | Unit price | Decimal value; non-negative; serialize as a decimal string |
| `category` | Category label | Required unless product requirements later allow uncategorized items; normalize consistently for filtering/cache keys |
| `stock` | Available quantity | Integer; non-negative |

The example product is:

```json
{
  "id": 101,
  "name": "Mechanical Keyboard",
  "price": "85.00",
  "category": "Electronics",
  "stock": 25
}
```

## 3. Non-functional requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-01 | Performance | Reuse a bounded Redis connection pool and a SQLAlchemy async engine/session factory |
| NFR-02 | Reliability | Redis failure must not unnecessarily stop product operations; use bounded timeouts and controlled fallback |
| NFR-03 | Consistency | Invalidate relevant cache entries after successful database commits |
| NFR-04 | Security | Redis is private, authenticated, and configured with least-privilege ACLs |
| NFR-05 | Resource management | Configure Redis memory limits and an explicit eviction policy; document implications for rate-limit counters |
| NFR-06 | Monitoring | Track cache hits, misses, errors, latency, Redis memory, and application health |
| NFR-07 | Health | Separate liveness from readiness and expose dependency status safely |
| NFR-08 | Deployment | Orchestrate services using Docker Compose; target Ubuntu for initial production hosting |
| NFR-09 | Configuration | Use environment variables and separate development/production configuration |
| NFR-10 | Logging | Record useful operational events without secrets or unnecessary personal/customer data |
| NFR-11 | Data correctness | Use `Decimal` and PostgreSQL `NUMERIC` for money |
| NFR-12 | Maintainability | Keep routes, schemas, models, services, cache policy, and infrastructure configuration separated |

## 4. API behavior requirements

- Use JSON for request and response bodies unless an endpoint explicitly documents otherwise.
- Use appropriate HTTP status codes and a consistent error response shape.
- Validate path, query, and body inputs before business logic executes.
- Return 404 for a product identifier that does not exist.
- Return 201 for successful product creation, 200 for successful reads/updates, and 204 for successful deletion (unless a documented response body is needed).
- Do not expose SQL, stack traces, secrets, or internal connection details in API errors.
- Exact pagination limits, sort fields, and rate-limit thresholds must be finalized in the API contract before implementation.

## 5. Cache behavior requirements

- Use cache-aside: read cache first; on miss, query PostgreSQL and populate Redis.
- Detail TTL starts at 300 seconds.
- List TTL starts at 120 seconds.
- Dashboard TTL starts at 120 seconds.
- Cache keys must be versioned and include every result-affecting query parameter.
- Invalidate all relevant cache views after a successful write.
- Treat cache values as untrusted, disposable data; malformed cache payloads are evicted and rebuilt from PostgreSQL.
- Redis timeouts/errors lead to a controlled cache bypass, not an unbounded retry loop.

## 6. Rate-limit requirements

- Apply limits only to selected endpoints, not blindly to every request.
- Store counters in Redis using a documented, atomic increment/expiry approach.
- Identify callers using a trustworthy client identifier. Only trust forwarded-IP headers from the known Nginx proxy path.
- Return HTTP 429 and a suitable `Retry-After` value when a limit is exceeded.
- Initial mode is best-effort: Redis unavailability bypasses the Redis rate-limit check and is recorded as a degraded state. This is not suitable as the sole control for high-risk or business-critical abuse prevention.
- Per-endpoint limits and windows remain configuration decisions until agreed.

## 7. Acceptance criteria by feature

See `docs/08-quality/testing.md` for the test matrix. A feature is not complete merely because the endpoint returns a successful response once: persistence, cache behavior, error cases, and tests must also be verified.
