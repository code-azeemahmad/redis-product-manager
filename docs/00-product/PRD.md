# Product Requirements Document (PRD)

## 1. Product summary

**Name:** `redis-saas-platform`

Build a small SaaS-style product management application. Users can browse a product catalogue, open product details, and view a dashboard with product and inventory statistics. The project demonstrates a production-minded application architecture in which PostgreSQL owns durable data and Redis improves read performance while providing selected best-effort rate-limit counters.

## 2. Problem and opportunity

The application provides a realistic, manageable system for learning and demonstrating:

- CRUD-oriented API design.
- Asynchronous Python database and cache access.
- Cache-aside behavior, TTLs, and invalidation.
- Graceful degradation when an optional cache is unavailable.
- Containerized frontend, reverse proxy, backend, database, and cache services.
- Operational concerns such as health checks, security, observability, and deployment.

## 3. Target users

The initial application is intended for a demonstration/development environment in which a user can browse and manage a sample product catalogue. The exact customer persona, account model, and authorization roles have not been specified.

## 4. Goals

1. Provide product create, read, update, and delete operations.
2. Provide product listing and product detail views.
3. Provide dashboard aggregates: total products, total inventory value, average product price, and product counts grouped by category.
4. Demonstrate Redis cache-aside for details, lists, and dashboard statistics.
5. Invalidate affected caches after successful product writes.
6. Demonstrate selected Redis-backed best-effort API rate limiting.
7. Keep product reads operational when Redis is unavailable, subject to database capacity and configured timeouts.
8. Run consistently through Docker Compose and support deployment to Ubuntu.

## 5. Non-goals for the initial version

Unless explicitly approved and documented later, do not implement:

- User registration, login, password reset, or role-based access control.
- Multi-tenant data isolation or tenant administration.
- Billing, subscriptions, payments, checkout, orders, or fulfilment.
- Product images/uploads, reviews, wishlists, or search-engine integration.
- Authoritative sessions, payment state, or critical background jobs in Redis.
- A distributed microservice architecture or Kubernetes deployment.

The product is described as SaaS-style, but production exposure to multiple customers requires an explicit decision on authentication and tenant isolation before release.

## 6. Main user journeys

1. **Browse catalogue:** user opens the product listing, optionally filters by category, and moves through paginated results.
2. **View detail:** user selects a product and sees its name, price, category, and stock quantity.
3. **Manage catalogue:** an operator/client sends create, update, or delete requests through the API. The frontend may expose these actions once the UX and access-control decision is made.
4. **View dashboard:** user sees aggregated product and inventory metrics.

## 7. Success criteria

- All specified product CRUD endpoints behave according to the API contract.
- First cacheable read populates Redis; a subsequent equivalent read can be served from Redis.
- Product create/update/delete operations invalidate all affected cache views after the database transaction commits.
- Redis downtime does not prevent core product reads/writes from using PostgreSQL.
- Rate-limited requests are rejected with HTTP 429 when Redis is available and the configured limit is exceeded.
- Database and Redis health are observable without exposing credentials or internal secrets.
- Automated tests cover success paths, invalid input, cache hits/misses, invalidation, and Redis outage behavior.
- Docker Compose starts the expected services and health checks reflect actual service readiness.

## 8. Assumptions and unresolved product decisions

- Product `id` is shown as an integer in the sample; confirm the primary-key type before database migration.
- `price` is represented as a decimal string in API examples and must use Python `Decimal` and PostgreSQL `NUMERIC`.
- Category is initially a text value rather than a separate managed taxonomy unless requirements change.
- The sample has no currency field. Do not infer a currency symbol or perform currency conversion.
- Product stock is a non-negative integer.
- The dashboard's inventory value is assumed to be `SUM(price * stock)`; confirm this business definition before presenting it as an accounting valuation.
- Authentication, authorization, and tenancy are unresolved and are not part of the first implementation slice.
