---
trigger: glob
globs: "backend/**/*.py"
description: Python, FastAPI, SQLAlchemy async, and Redis implementation rules
---

- Use type hints for public functions, service interfaces, and configuration objects.
- Keep FastAPI route handlers focused on HTTP concerns; delegate business logic to services.
- Use asynchronous SQLAlchemy sessions and `redis.asyncio`; do not block the event loop with synchronous network I/O.
- Reuse clients, engines, and bounded pools; do not create a new Redis pool or database engine per request.
- Use one request-scoped `AsyncSession`; do not share it concurrently across independent tasks.
- Parse and serialize monetary values using `Decimal`; never convert prices through `float`.
- Validate external input with Pydantic and enforce durable invariants in PostgreSQL constraints too.
- Use finite timeouts and controlled error handling for Redis operations.
- Do not log secrets, connection strings, authorization headers, or full sensitive payloads.
- Add tests for behavior changes, including dependency failures where applicable.
