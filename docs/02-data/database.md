# Database Design — PostgreSQL

## 1. Ownership

PostgreSQL is the permanent source of truth. Redis values must be reconstructible from committed PostgreSQL data.

## 2. Initial product entity

The project brief provides the following sample fields:

| Column | Suggested PostgreSQL type | Rules / notes |
|---|---|---|
| `id` | `INTEGER` generated primary key | Matches the sample identifier; confirm before migration |
| `name` | `VARCHAR(200)` | Suggested maximum; required and non-empty after trimming |
| `price` | `NUMERIC(12, 2)` | Suggested precision; non-negative; API serializes as decimal string |
| `category` | `VARCHAR(100)` | Suggested maximum; normalize consistently for filters |
| `stock` | `INTEGER` | Non-negative quantity |

The lengths and numeric precision above are sensible starting proposals, not values supplied as fixed requirements. Confirm them before creating the first production migration. Do not use `FLOAT`, `REAL`, or Python `float` for currency values.

## 3. Constraints and indexes

Suggested initial constraints:

- Primary key on `id`.
- `CHECK (price >= 0)`.
- `CHECK (stock >= 0)`.
- `NOT NULL` on required fields.
- Add an index on `category` if category filtering is supported and query plans justify it.
- Add indexes for actual sort/filter patterns based on `EXPLAIN (ANALYZE, BUFFERS)` rather than guessing many indexes.

The product name does not need to be unique unless a business requirement is added.

## 4. Timestamps

`created_at` and `updated_at` are recommended operational fields but were not included in the supplied sample. Decide whether to add them before schema creation. Store timezone-aware timestamps in UTC.

## 5. Relationships and tenancy

No user, tenant, order, or category tables are currently specified. Do not invent foreign keys or `tenant_id` columns without an approved tenancy/data-ownership design. If multi-tenancy is introduced, every relevant query, unique constraint, index, cache key, and authorization check must be tenant-scoped and tested for cross-tenant leakage.

## 6. SQLAlchemy async usage

- Define declarative ORM models separately from Pydantic API schemas.
- Use an async engine and `async_sessionmaker`.
- Create a request-scoped `AsyncSession` dependency.
- Use explicit transaction boundaries for writes.
- Do not run concurrent independent operations through one shared `AsyncSession`.
- Use parameterized ORM/Core operations; never concatenate untrusted strings into SQL.

## 7. Migrations

A migration tool has not been selected. Alembic is recommended for SQLAlchemy projects. Once selected:

- Commit migration scripts to version control.
- Never rely on `create_all()` as the production schema migration process.
- Review generated migrations before applying them.
- Back up production data before risky schema changes.
- Test both fresh database creation and upgrade from the previous migration.

## 8. Dashboard calculations

Proposed aggregate definitions:

- `total_products`: count of product rows.
- `total_inventory_value`: `SUM(price * stock)`.
- `average_product_price`: average of product unit price.
- `products_by_category`: count of products grouped by category.

Confirm whether average price includes all products and how empty datasets are represented. Use decimal-safe serialization for monetary aggregates. Do not label `SUM(price * stock)` as an accounting valuation until the business meaning is approved.

## 9. Data lifecycle and integrity

- PostgreSQL transactions determine whether a write succeeded.
- Cache invalidation occurs only after commit.
- Database constraints protect invariants even if a request path has a bug.
- Define backup, retention, restore, and disaster-recovery policies before production launch.
