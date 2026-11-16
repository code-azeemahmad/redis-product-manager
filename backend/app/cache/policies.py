"""Cache-aside policies, serialization, and generation invalidation.

Following architectural rules:
- Cache detail (300s TTL), list (120s TTL), and dashboard stats (120s TTL).
- Keys are deterministic and include all result-affecting query dimensions.
- Writes invalidate affected namespaces after database commit using generation increments.
- Malformed cache payloads are discarded and deleted; rebuilds occur from PostgreSQL.
- Redis failures degrade gracefully without failing user requests.
"""

import json
import logging
from typing import Optional
from pydantic import ValidationError

from app.cache.keys import (
    dashboard_stats_generation_key,
    dashboard_stats_key,
    product_detail_key,
    product_list_generation_key,
    product_list_key,
)
from app.config import get_settings
from app.core.metrics import metrics
from app.schemas.dashboard import DashboardStatsResponse
from app.schemas.product import ProductListResponse, ProductResponse
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Product Detail Cache
# ------------------------------------------------------------------------------
async def get_cached_product(
    redis_service: RedisService,
    product_id: int,
) -> Optional[ProductResponse]:
    """Retrieve product detail from cache-aside layer."""
    key = product_detail_key(product_id)
    raw = await redis_service.get(key)
    if not raw:
        logger.info("Cache miss for product detail: %s", key)
        metrics.record_cache_event("detail_read", "miss")
        return None

    try:
        product = ProductResponse.model_validate_json(raw)
        logger.info("Cache hit for product detail: %s", key)
        metrics.record_cache_event("detail_read", "hit")
        return product
    except (ValidationError, json.JSONDecodeError) as exc:
        logger.warning("Corrupt payload for %s; deleting cache entry: %s", key, exc)
        metrics.record_cache_event("detail_read", "corrupt_payload")
        await redis_service.delete(key)
        return None


async def set_cached_product(
    redis_service: RedisService,
    product: ProductResponse,
) -> bool:
    """Store product detail in cache with detail TTL."""
    key = product_detail_key(product.id)
    settings = get_settings()
    payload = product.model_dump_json()
    success = await redis_service.set(
        key=key,
        value=payload,
        expire=settings.CACHE_PRODUCT_DETAIL_TTL,
    )
    if success:
        logger.info("Cached product detail: %s (TTL: %ds)", key, settings.CACHE_PRODUCT_DETAIL_TTL)
        metrics.record_cache_event("detail_write", "written")
    else:
        logger.warning("Failed to cache product detail: %s", key)
        metrics.record_cache_event("detail_write", "error")
    return success


# ------------------------------------------------------------------------------
# Product Listing Cache (Generation-Based)
# ------------------------------------------------------------------------------
async def get_cached_product_list(
    redis_service: RedisService,
    category: Optional[str],
    page: int,
    limit: int,
    sort_by: str,
    sort_order: str,
) -> Optional[ProductListResponse]:
    """Retrieve paginated product list from cache."""
    gen = await redis_service.get_generation(product_list_generation_key())
    key = product_list_key(
        generation=gen,
        category=category,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    raw = await redis_service.get(key)
    if not raw:
        logger.info("Cache miss for product list: %s", key)
        metrics.record_cache_event("list_read", "miss")
        return None

    try:
        data = ProductListResponse.model_validate_json(raw)
        logger.info("Cache hit for product list: %s", key)
        metrics.record_cache_event("list_read", "hit")
        return data
    except (ValidationError, json.JSONDecodeError) as exc:
        logger.warning("Corrupt payload for %s; deleting cache entry: %s", key, exc)
        metrics.record_cache_event("list_read", "corrupt_payload")
        await redis_service.delete(key)
        return None


async def set_cached_product_list(
    redis_service: RedisService,
    list_response: ProductListResponse,
    category: Optional[str],
    page: int,
    limit: int,
    sort_by: str,
    sort_order: str,
) -> bool:
    """Store paginated product list in cache with list TTL."""
    gen = await redis_service.get_generation(product_list_generation_key())
    key = product_list_key(
        generation=gen,
        category=category,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    settings = get_settings()
    payload = list_response.model_dump_json()
    success = await redis_service.set(
        key=key,
        value=payload,
        expire=settings.CACHE_PRODUCT_LIST_TTL,
    )
    if success:
        logger.info("Cached product list: %s (TTL: %ds)", key, settings.CACHE_PRODUCT_LIST_TTL)
        metrics.record_cache_event("list_write", "written")
    else:
        logger.warning("Failed to cache product list: %s", key)
        metrics.record_cache_event("list_write", "error")
    return success


# ------------------------------------------------------------------------------
# Dashboard Statistics Cache (Generation-Based)
# ------------------------------------------------------------------------------
async def get_cached_dashboard_stats(
    redis_service: RedisService,
) -> Optional[DashboardStatsResponse]:
    """Retrieve dashboard statistics from cache."""
    gen = await redis_service.get_generation(dashboard_stats_generation_key())
    key = dashboard_stats_key(gen)
    raw = await redis_service.get(key)
    if not raw:
        logger.info("Cache miss for dashboard stats: %s", key)
        metrics.record_cache_event("dashboard_read", "miss")
        return None

    try:
        stats = DashboardStatsResponse.model_validate_json(raw)
        logger.info("Cache hit for dashboard stats: %s", key)
        metrics.record_cache_event("dashboard_read", "hit")
        return stats
    except (ValidationError, json.JSONDecodeError) as exc:
        logger.warning("Corrupt payload for %s; deleting cache entry: %s", key, exc)
        metrics.record_cache_event("dashboard_read", "corrupt_payload")
        await redis_service.delete(key)
        return None


async def set_cached_dashboard_stats(
    redis_service: RedisService,
    stats: DashboardStatsResponse,
) -> bool:
    """Store dashboard statistics in cache with dashboard TTL."""
    gen = await redis_service.get_generation(dashboard_stats_generation_key())
    key = dashboard_stats_key(gen)
    settings = get_settings()
    payload = stats.model_dump_json()
    success = await redis_service.set(
        key=key,
        value=payload,
        expire=settings.CACHE_DASHBOARD_STATS_TTL,
    )
    if success:
        logger.info("Cached dashboard stats: %s (TTL: %ds)", key, settings.CACHE_DASHBOARD_STATS_TTL)
        metrics.record_cache_event("dashboard_write", "written")
    else:
        logger.warning("Failed to cache dashboard stats: %s", key)
        metrics.record_cache_event("dashboard_write", "error")
    return success


# ------------------------------------------------------------------------------
# Post-Commit Invalidation Matrix
# ------------------------------------------------------------------------------
async def invalidate_product_caches(
    redis_service: RedisService,
    product_id: Optional[int] = None,
) -> None:
    """Apply post-commit cache invalidation according to the documented matrix:

    - Detail key deleted if product_id provided (for Update and Delete).
    - Product list generation incremented (for Create, Update, and Delete).
    - Dashboard generation incremented (for Create, Update, and Delete).
    Never uses blocking KEYS or SCAN commands in request paths.
    """
    try:
        if product_id is not None:
            detail_key = product_detail_key(product_id)
            await redis_service.delete(detail_key)
            logger.info("Invalidated product detail key: %s", detail_key)

        new_list_gen = await redis_service.increment_generation(product_list_generation_key())
        logger.info("Advanced product list generation to: %d", new_list_gen)

        new_dash_gen = await redis_service.increment_generation(dashboard_stats_generation_key())
        logger.info("Advanced dashboard generation to: %d", new_dash_gen)
        metrics.record_cache_event("invalidate", "invalidated")
    except Exception as exc:
        logger.warning("Error during post-commit cache invalidation: %s", exc)
        metrics.record_cache_event("invalidate", "error")
