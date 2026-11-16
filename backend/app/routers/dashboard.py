"""Dashboard HTTP API router.

Exposes aggregated product and inventory metrics with 120-second Redis cache-aside.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import policies
from app.dependencies import get_db_session, get_redis_service
from app.schemas.dashboard import DashboardStatsResponse
from app.services import dashboard_service
from app.services.rate_limiter import rate_limit_dashboard
from app.services.redis_service import RedisService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated catalogue and inventory statistics",
    dependencies=[Depends(rate_limit_dashboard)],
)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db_session),
    redis_service: RedisService = Depends(get_redis_service),
) -> DashboardStatsResponse:
    """Retrieve dashboard statistics with 120-second cache-aside caching."""
    # 1. Attempt cache read
    cached = await policies.get_cached_dashboard_stats(redis_service)
    if cached is not None:
        return cached

    # 2. On miss, calculate aggregates from PostgreSQL source of truth
    stats = await dashboard_service.calculate_dashboard_stats(session)

    # 3. Attempt to cache result (failure does not affect response)
    await policies.set_cached_dashboard_stats(redis_service, stats)

    return stats
