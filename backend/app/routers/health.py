"""Health and readiness probe router.

Following architectural rules:
- Process liveness check (/health/live) has zero external dependencies.
- Readiness check (/health/ready) verifies authoritative PostgreSQL (required).
- Redis status is reported as healthy or degraded without failing readiness for product reads.
- Response includes safe dependency latencies and timestamp without leaking internal credentials.
"""

from datetime import datetime, timezone
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, get_redis_service
from app.services.redis_service import RedisService

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK, summary="Process liveness check")
async def health_live() -> dict[str, str]:
    """Process liveness probe."""
    return {"status": "alive"}


@router.get("/ready", status_code=status.HTTP_200_OK, summary="Dependency readiness check")
async def health_ready(
    session: AsyncSession = Depends(get_db_session),
    redis_service: RedisService = Depends(get_redis_service),
) -> dict[str, object]:
    """Readiness probe.

    PostgreSQL is strictly required for core availability.
    Redis is disposable; a Redis outage degrades caching but does not take down the service.
    """
    # 1. Check PostgreSQL (Mandatory)
    pg_start = time.perf_counter()
    try:
        await session.execute(text("SELECT 1"))
        postgres_latency_ms = round((time.perf_counter() - pg_start) * 1000, 2)
        postgres_status = "healthy"
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unavailable",
                "dependencies": {
                    "postgres": "unhealthy",
                    "redis": "unknown",
                },
            },
        ) from exc

    # 2. Check Redis (Optional / Graceful degradation)
    redis_start = time.perf_counter()
    redis_healthy = await redis_service.ping()
    redis_latency_ms = (
        round((time.perf_counter() - redis_start) * 1000, 2) if redis_healthy else None
    )
    redis_status = "healthy" if redis_healthy else "degraded"

    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "postgres": postgres_status,
            "redis": redis_status,
        },
        "latency_ms": {
            "postgres": postgres_latency_ms,
            "redis": redis_latency_ms,
        },
    }

