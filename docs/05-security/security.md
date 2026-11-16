# Security Requirements

## 1. Security posture and scope

This is an initial product catalogue application. The supplied scope does not define user authentication, roles, or tenant isolation. Do not invent an auth model. However, do not expose mutation endpoints publicly in production without an approved authentication/authorization design.

## 2. Secrets and configuration

- Commit `.env.example` with placeholder variable names and safe example values only.
- Keep `.env`, credentials, private keys, tokens, and production secrets out of Git.
- Use deployment secrets or protected environment injection in production.
- Never print full database/Redis URLs or secret values in logs or exception responses.
- Rotate credentials when exposure is suspected.

## 3. Network boundaries

- Publish Nginx as the intended public entry point.
- Keep PostgreSQL and Redis on private Docker networks; do not publish their ports to public interfaces in production.
- Restrict host firewall rules to required traffic (for example, HTTPS to the proxy and controlled administration access).
- Use HTTPS in production. Decide where TLS terminates and ensure internal proxy headers cannot be spoofed.
- Do not allow the browser to connect directly to PostgreSQL or Redis.

## 4. Redis security

- Require Redis authentication and configure ACL users with least privilege.
- Use a dedicated application user rather than the Redis default user for application access.
- Grant only the commands and key patterns needed by the application where practical.
- Keep `users.acl` free of plaintext production passwords; inject secrets at deployment time or use a protected secret file mechanism.
- Bind Redis to internal interfaces/private networks and avoid host port publication.
- Protect Redis configuration/ACL files with restrictive filesystem permissions.
- Disable or restrict dangerous administrative commands for the application user.
- Monitor authentication failures and unexpected command patterns.

## 5. PostgreSQL security

- Use a dedicated application database role with only required schema/table privileges.
- Do not use the PostgreSQL superuser from the application.
- Require credentials and network isolation.
- Use parameterized ORM/Core operations.
- Plan backups and test restores before production.

## 6. API and input security

- Validate path, query, and body inputs with Pydantic.
- Enforce domain constraints in both service logic and database constraints where possible.
- Allowlist sort fields/directions; never interpolate arbitrary query input into SQL.
- Apply request-size limits at Nginx and application layers.
- Configure CORS narrowly if cross-origin browser access is needed; same-origin Nginx routing is preferred for this deployment.
- Return generic server errors; do not leak stack traces, SQL, internal hostnames, or secret values.
- Consider CSRF only if cookie-based authentication is later introduced; authentication design determines the relevant controls.

## 7. Rate limiting

The initial Redis limiter is best-effort. Do not treat it as a substitute for authentication, authorization, abuse monitoring, or infrastructure controls. Trust client IP headers only from the configured proxy.

## 8. Logging and privacy

- Use structured logs with request correlation identifiers.
- Do not log passwords, tokens, Authorization headers, connection strings, or secret-bearing environment values.
- Avoid logging full request bodies for product endpoints unless there is a justified, privacy-reviewed need.
- Avoid raw IPs or product/customer data as metric labels.
- Restrict access to production logs and define retention.

## 9. Container and host hardening

- Pin image versions/digests for production.
- Run containers as non-root where supported and practical.
- Keep images minimal and patch base images/dependencies.
- Use read-only filesystems/capabilities restrictions where compatible.
- Do not mount the Docker socket into application containers.
- Configure resource limits and restart policies intentionally.
- Keep host OS and Docker Engine patched.

## 10. Production release gate

Before public release, resolve authentication and authorization, tenant isolation, TLS/domain, secrets management, backups/restores, dependency scanning, and operational alerting. Passing the initial functional tests is not sufficient for a production security sign-off.
