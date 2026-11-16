# HTTP API Contract

Base path: `/api`

The routes below are the agreed initial route names. Exact schema limits, pagination defaults, sorting allowlist, and error envelope must be finalized before implementation.

## 1. Product endpoints

### `POST /api/products`

Create a product.

**Request example**

```json
{
  "name": "Mechanical Keyboard",
  "price": "85.00",
  "category": "Electronics",
  "stock": 25
}
```

**Expected behavior**

- Validate required fields and business constraints.
- Parse price into `Decimal` and persist as PostgreSQL `NUMERIC`.
- Commit PostgreSQL transaction.
- Invalidate product-list and dashboard cache generations after commit.
- Return `201 Created` with the created product representation.

### `GET /api/products`

List products.

Suggested query parameters (finalize names/defaults before implementation):

| Parameter | Purpose | Cache identity |
|---|---|---|
| `category` | Optional category filter | Include normalized category |
| `page` | Page number, suggested default 1 | Include page |
| `limit` | Page size, suggested default 20 | Include limit |
| `sort_by` | Allowlisted field | Include selected field |
| `sort_order` | `asc` or `desc` | Include direction |

- Validate page and limit; enforce a configured maximum limit.
- Whitelist sortable fields; never interpolate arbitrary user input into SQL ordering.
- Return a documented pagination envelope (items, page, limit, total or equivalent). Decide exact shape before frontend integration.
- Cache equivalent query results using a normalized key.

### `GET /api/products/{id}`

Get one product. Return `404 Not Found` if it does not exist. Read through Redis using a 300-second starting TTL. On cache failure/miss, query PostgreSQL and attempt to repopulate Redis.

### `PUT /api/products/{id}`

Update an existing product. The exact request semantics are full replacement (`PUT`) as named in the requirements; decide whether omitted fields are invalid. Commit PostgreSQL first, then invalidate product detail, list, and dashboard cache generations. Return `404` if the product does not exist.

### `DELETE /api/products/{id}`

Delete an existing product. Commit PostgreSQL first, then invalidate affected caches. Return `204 No Content` on success and `404` if the product does not exist.

## 2. Dashboard endpoint

### `GET /api/dashboard/stats`

Return the agreed statistics:

- Total products.
- Total inventory value (proposed formula: `SUM(price * stock)`, pending business confirmation).
- Average product price.
- Products grouped by category.

Cache for 120 seconds initially. Use PostgreSQL to calculate the response on a miss. Return zero/empty values consistently for an empty catalogue.

## 3. Health endpoints

Suggested contract:

- `GET /health/live`: process is running; should not require external dependency checks.
- `GET /health/ready`: check required dependencies (PostgreSQL is required); report Redis as optional/degraded in a safe, non-secret way.

The final readiness status policy should be documented. Since Redis is intentionally optional for core product operations, a Redis outage alone should not make a healthy database-backed application unavailable.

## 4. Rate limiting

Apply to selected endpoints only. Exact endpoint list, caller identity strategy, maximum requests, and window duration are pending decisions. When exceeded, return `429 Too Many Requests` with a `Retry-After` header. Do not expose the raw Redis key or internal policy implementation.

## 5. Response and error conventions

Adopt one consistent error envelope, for example:

```json
{
  "detail": "A human-readable error message"
}
```

Use framework-standard validation errors initially unless a project-wide error envelope is approved. Never return stack traces, SQL text, credentials, or internal network details.

Suggested status codes:

| Code | Meaning |
|---|---|
| 200 | Successful read/update |
| 201 | Product created |
| 204 | Product deleted |
| 400 | Invalid business request |
| 404 | Product not found |
| 422 | Request validation error (FastAPI default unless standardized otherwise) |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error |
| 503 | Required service unavailable (for example PostgreSQL) |

## 6. API compatibility

- Keep route behavior and response schemas documented.
- Treat breaking response changes as API changes; update frontend and tests together.
- Do not add authentication headers, tenant parameters, currency fields, or other unspecified contract elements without an approved decision.
