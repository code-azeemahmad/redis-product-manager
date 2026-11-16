# Release Readiness Workflow

Use this before a deploy or release candidate.

1. Read `docs/07-operations/deployment.md`, `docs/05-security/security.md`, and `docs/08-quality/testing.md`.
2. Confirm supported dependency/image versions are pinned.
3. Confirm production secrets are injected securely and absent from Git.
4. Confirm Nginx is the intended public entry point, HTTPS is enabled, and database/Redis ports are private.
5. Confirm PostgreSQL backups exist and a restore has been tested.
6. Confirm Redis ACL, maxmemory, eviction policy, and rate-limit counter implications.
7. Confirm authentication/authorization and tenant scope are resolved before real customer access.
8. Run test suite and deployment smoke tests; record exact results.
9. Verify health endpoints, logs, metrics, alerting, and rollback procedure.
10. Record remaining risks; do not call the release production-ready while critical gates remain open.
