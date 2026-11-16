# Deployment and Runtime Operations

## 1. Deployment target

The initial production host is Ubuntu. Docker Compose orchestrates Nginx, frontend build/runtime assets, FastAPI, PostgreSQL, and Redis 8. Exact Ubuntu release, hosting provider, domain, and TLS approach are not yet specified.

## 2. Planned service topology

| Service | Purpose | Network exposure |
|---|---|---|
| `nginx` | Public HTTP(S) entry point; serves React and proxies API | Publish intended web ports only |
| `backend` | FastAPI application | Internal network; not directly public unless deliberately required |
| `postgres` | Durable database | Internal network; no public port in production |
| `redis` | Cache and best-effort counters | Internal network; no public port in production |

The React application may be built into static assets and copied into the Nginx image, or served through a separate frontend container in development. Select one Compose implementation and document it when code is created.

## 3. Environment configuration

- Keep safe variable names and placeholders in `.env.example`.
- Use separate development and production values.
- Do not commit `.env` or real credentials.
- Validate required settings at startup and fail fast on invalid mandatory configuration.
- Do not print secret values during configuration errors.

Configuration categories include PostgreSQL connection settings, Redis URL/ACL credentials, pool sizes/timeouts, cache TTLs, rate-limit policies, CORS/trusted proxy settings, logging level, and frontend/API origin settings.

## 4. Startup and health

- Configure container health checks for PostgreSQL and Redis.
- Configure backend health endpoints and process lifecycle.
- Compose startup ordering is not a substitute for application-level retry/readiness handling; the backend must handle a dependency becoming unavailable after startup.
- Liveness checks should verify the process is alive without requiring external services.
- Readiness should require PostgreSQL for core application readiness and report Redis degradation separately because Redis is optional for product operations.

## 5. Production networking and TLS

- Expose Nginx only on intended public ports.
- Use HTTPS for production. Decide whether TLS terminates at Nginx or an upstream load balancer and configure trusted proxy headers accordingly.
- Restrict SSH/admin access separately from application traffic.
- Do not bind PostgreSQL/Redis to `0.0.0.0` on the public host interface.
- Configure firewall rules and Docker network boundaries deliberately.

## 6. Persistence and recovery

- Persist PostgreSQL data using a named volume or an explicitly managed storage location.
- Redis persistence is not required for disposable cache values. Decide whether Redis should start empty after restart; the application must tolerate that.
- Back up PostgreSQL with a defined schedule, retention, encryption, and off-host storage.
- Test restore procedures, not just backup creation.
- Do not assume Docker volumes alone are backups.

## 7. Resource limits and restart policy

- Set CPU/memory expectations for services and configure container limits where supported by the deployment environment.
- Set Redis `maxmemory` and an explicit eviction policy.
- Understand that cache eviction can also evict best-effort rate-limit counters if both share an instance.
- Define PostgreSQL connection pool limits and total expected backend worker concurrency.
- Use restart policies deliberately; they do not replace monitoring or recovery procedures.

## 8. Release checklist

- [ ] Production dependency versions/image tags are pinned.
- [ ] `.env`/secrets are supplied securely and absent from Git.
- [ ] HTTPS and domain routing are configured.
- [ ] Only intended ports are publicly reachable.
- [ ] PostgreSQL role is least-privilege and backups are tested.
- [ ] Redis ACL, memory limit, and eviction policy are reviewed.
- [ ] Health checks and logs are accessible to operators.
- [ ] Authentication/authorization and tenant decisions are resolved before public customer access.
- [ ] Migrations are reviewed and applied safely.
- [ ] Smoke tests cover cache hit/miss, invalidation, and Redis outage.
