---
trigger: glob
globs: "compose.yaml, compose.yml, docker-compose.yml, **/Dockerfile, nginx/**/*.conf, redis/**/*.conf, redis/**/*.acl"
description: Docker, Nginx, Redis, and deployment security rules
---

- Keep PostgreSQL and Redis on private networks and do not publish their ports publicly in production.
- Publish only intended web entry points through Nginx.
- Never place real credentials or secrets in Compose files, Dockerfiles, Redis ACL files, or committed environment files.
- Use least-privilege PostgreSQL and Redis application credentials.
- Do not expose the Docker socket to application containers.
- Pin production image tags/digests; avoid floating `latest` tags for production.
- Configure health checks, resource limits, Redis maxmemory, and an explicit eviction policy.
- Remember that eviction can remove best-effort rate-limit counters when counters share a cache instance.
- Configure HTTPS and trusted proxy headers deliberately before public deployment.
