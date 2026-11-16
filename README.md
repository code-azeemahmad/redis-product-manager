# Redis SaaS Platform

A SaaS-style product catalogue and management application demonstrating a React frontend, FastAPI backend, PostgreSQL as the authoritative data store, and Redis 8 for disposable caching and best-effort rate limiting.

## Project principles

1. **PostgreSQL is the source of truth.** Redis contains disposable data that can be rebuilt from PostgreSQL.
2. **Redis is an optimization, not a hard dependency for product reads.** If Redis is unavailable, product operations should continue against PostgreSQL within configured timeouts and capacity limits.
3. **Database writes commit before cache invalidation.** Cache invalidation is attempted after a successful PostgreSQL commit; a Redis failure must not pretend that a committed database write failed.
4. **No secrets in source control.** Runtime settings come from environment variables or deployment secrets.
5. **Build in verified stages.** Each roadmap phase must have working tests and updated documentation before the next phase begins.

## Planned technology stack

| Area | Technology | Responsibility |
|---|---|---|
| Frontend | React | Product catalogue, product details, dashboard UI |
| Reverse proxy | Nginx | HTTP entry point, static frontend delivery, API proxy |
| Backend | FastAPI | API routes and business logic |
| Database | PostgreSQL | Permanent application data |
| Cache / counters | Redis 8 | Cache-aside data caching and selected rate-limit counters |
| ORM | SQLAlchemy (async) | Asynchronous database access |
| Validation | Pydantic | Request, response, and settings validation |
| Containers | Docker Compose | Local and deployment service orchestration |
| Production host | Ubuntu | Initial production operating system |

Python Redis access uses `redis.asyncio`. SQLAlchemy uses asynchronous sessions.

## Scope at a glance

- Create, list, retrieve, update, and delete products.
- Cache product details, product listings, and dashboard aggregates.
- Apply Redis-backed best-effort rate limiting to selected endpoints.
- Expose liveness and readiness/health information.
- Run the services through Docker Compose and deploy to Ubuntu.

Authentication, user management, billing, order processing, and enforced multi-tenant isolation are **not currently specified**. Do not invent or implement them as part of the initial scope. Resolve these before exposing the application to multiple real customers.

## Documentation map

- `AGENTS.md`: shared coding-agent instructions; Antigravity can load it at workspace level.
- `GEMINI.md`: concise Antigravity workspace pointer.
- `CLAUDE.md`: Claude Code project instructions.
- `docs/00-product/`: product brief and requirements.
- `docs/01-architecture/`: architecture, stack, and repository layout.
- `docs/02-data/`: PostgreSQL data model.
- `docs/03-api/`: HTTP API contract.
- `docs/04-redis/`: caching and rate-limiting designs.
- `docs/05-security/`: security requirements.
- `docs/06-frontend/`: UI/UX direction and unresolved design choices.
- `docs/07-operations/`: deployment and observability.
- `docs/08-quality/`: testing strategy.
- `project-management/`: implementation sequence, task backlog, and progress.
- `.agents/rules/`: Antigravity workspace rules.
- `.agents/workflows/`: reusable Antigravity workflows.

## Getting started with implementation

This repository initially contains project documentation, not application code. Start with `project-management/roadmap.md` and `project-management/implementation-plan.md`. Implement one phase at a time and update `project-management/tasks.md` and `project-management/progress.md` as work is verified.

Before production use, resolve the open decisions listed in `docs/01-architecture/architecture-decisions.md`, especially authentication/tenant scope, database migration tooling, API pagination/sorting contract, rate-limit thresholds, Redis failure policy limits, and TLS/domain configuration.
