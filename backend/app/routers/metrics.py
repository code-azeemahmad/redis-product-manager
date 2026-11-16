"""Prometheus metrics exposition endpoint.

Following architectural rules:
- Prometheus text format (v0.0.4).
- Reports HTTP request counts and durations with bounded route labels.
- Reports cache operations and hit/miss/invalidation counts.
- Reports rate-limit decisions (allowed, blocked, bypassed).
- Reports real-time PostgreSQL connection pool gauges.
- Reports real-time Redis status, memory, clients, and eviction counters.
- Strictly safe: no passwords, tokens, full connection strings, or unbounded user IDs.
"""

from fastapi import APIRouter, Depends, Response
from app.core.metrics import metrics
from app.database.connection import get_async_engine
from app.dependencies import get_redis_service
from app.services.redis_service import RedisService

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Prometheus-compatible operational metrics",
    response_class=Response,
)
async def get_metrics(
    redis_service: RedisService = Depends(get_redis_service),
) -> Response:
    """Export system, cache, rate limit, and operational metrics in Prometheus format."""
    engine = get_async_engine()
    content = await metrics.export_prometheus_text(
        db_engine=engine,
        redis_service=redis_service,
    )
    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
