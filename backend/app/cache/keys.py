"""Centralized Redis cache key builder functions.

Following architectural rules:
- All keys are versioned with an explicit prefix (e.g. 'v1').
- Query parameters are normalized (lowercase, trimmed whitespace, sorted).
- Invalidation uses generations to avoid blocking KEYS/SCAN commands.
"""

from typing import Optional
from app.config import get_settings


def get_prefix() -> str:
    """Return configured cache key prefix."""
    return get_settings().CACHE_KEY_PREFIX


def product_detail_key(product_id: int) -> str:
    """Build key for cached product detail: 'v1:product:{id}'."""
    return f"{get_prefix()}:product:{product_id}"


def product_list_generation_key() -> str:
    """Key holding the current generation counter for product listings."""
    return f"{get_prefix()}:cachegen:products:list"


def dashboard_stats_generation_key() -> str:
    """Key holding the current generation counter for dashboard statistics."""
    return f"{get_prefix()}:cachegen:dashboard:stats"


def product_list_key(
    generation: int,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "id",
    sort_order: str = "asc",
) -> str:
    """Build key for cached product list with normalized parameters.

    Example: 'v1:products:list:g1:cat:electronics:page:1:limit:20:sort:id:asc'
    """
    cat_str = category.strip().lower() if category and category.strip() else "all"
    sort_by_str = sort_by.strip().lower()
    sort_order_str = sort_order.strip().lower()
    return (
        f"{get_prefix()}:products:list:g{generation}:"
        f"cat:{cat_str}:page:{page}:limit:{limit}:sort:{sort_by_str}:{sort_order_str}"
    )


def dashboard_stats_key(generation: int) -> str:
    """Build key for cached dashboard statistics: 'v1:dashboard:stats:g{generation}'."""
    return f"{get_prefix()}:dashboard:stats:g{generation}"
