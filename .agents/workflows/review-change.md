# Review Change Workflow

Review the current diff as a careful maintainer.

1. Compare the diff with the task and acceptance criteria.
2. Check PostgreSQL transaction correctness and Decimal-safe money handling.
3. Check Redis timeouts, failure fallback, cache-key completeness, serialization validation, and post-commit invalidation.
4. Check that no request-path `KEYS` command or unbounded retry loop was introduced.
5. Check rate-limit caller identity and trusted-proxy assumptions.
6. Check secrets, ACLs, public ports, logs, and error messages for leaks.
7. Check tests for normal paths and dependency failures.
8. Check docs and project-management files for synchronization.
9. Report findings by severity with file/line references; do not make changes unless asked to fix them.
