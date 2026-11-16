# Changelog

This file records notable project changes. It is not a substitute for Git history.

## Unreleased

- Established initial product and engineering documentation from the project brief.
- Recorded the initial architecture: React → Nginx → FastAPI → PostgreSQL/Redis.
- Documented cache-aside TTLs: product detail 300s; product lists 120s; dashboard statistics 120s.
- Documented Redis as disposable cache and best-effort rate-limit storage only.
- Added Antigravity rules/workflows and Claude Code project instructions.
