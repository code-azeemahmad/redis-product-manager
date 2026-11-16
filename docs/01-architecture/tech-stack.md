# Technology Stack

| Layer | Technology | Use | Notes |
|---|---|---|---|
| Frontend | React | Product catalogue, detail, dashboard UI | Build tool and router are not yet selected |
| Reverse proxy | Nginx | HTTP entry point, static files, API proxy | Public-facing service in Compose/deployment |
| Backend | FastAPI | API and business logic | Python async request path |
| Persistent database | PostgreSQL | Durable products and aggregates | Source of truth |
| Cache/counters | Redis 8 | Cache-aside and selected rate-limit counters | Disposable data only in initial design |
| ORM | SQLAlchemy async | Database models and sessions | One async session per request/unit of work |
| Validation | Pydantic | Request/response/config validation | Keep API schemas separate from ORM models |
| Redis client | `redis.asyncio` | Async Redis commands and pooling | Reuse client/pool through app lifespan |
| Containers | Docker Compose | Local integration and deployment orchestration | Avoid exposing internal ports publicly |
| Host OS | Ubuntu | Initial production host | Exact release and provisioning method TBD |

## Dependency/version policy

- Redis major version is specified as 8.
- Exact versions for Python, React, FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Nginx, Node, and Docker images are not specified yet.
- Before implementation, select supported versions and pin dependencies/image tags intentionally. Avoid floating `latest` tags for production.
- Keep frontend and backend dependency manifests authoritative; update this document when versions or major dependencies change.
- A database migration tool is not specified. **Alembic is the recommended SQLAlchemy migration tool**, but adoption must be confirmed before schema migrations are created.

## Recommended engineering choices (subject to approval)

- Use PostgreSQL `NUMERIC` with an explicit precision/scale for price and Python `Decimal`.
- Use Pydantic schemas for API contracts and separate SQLAlchemy models for persistence.
- Use a structured settings object loaded from environment variables.
- Use `pytest` for backend tests; add async test support and HTTP client dependencies as needed.
- Use a React test runner and browser-level E2E tool only after selecting the frontend build/test stack.

Do not add these recommendations as dependencies without documenting the selection and updating dependency files.
