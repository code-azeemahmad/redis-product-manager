"""Dashboard aggregate calculation service layer.

Calculates catalogue statistics directly from PostgreSQL source of truth using Decimal precision.
"""

from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Product
from app.schemas.dashboard import DashboardStatsResponse

TWO_PLACES = Decimal("0.01")


async def calculate_dashboard_stats(session: AsyncSession) -> DashboardStatsResponse:
    """Calculate dashboard statistics from PostgreSQL.

    Ensures zero/empty values are handled consistently for empty catalogues.
    """
    # 1. Total products, inventory value, and average price in a single aggregate query
    stmt = select(
        func.count(Product.id),
        func.coalesce(func.sum(Product.price * Product.stock), 0),
        func.coalesce(func.avg(Product.price), 0),
    )
    result = await session.execute(stmt)
    total_products, raw_inv_value, raw_avg_price = result.one()

    # Ensure Decimal conversion and clean 2-decimal rounding
    total_inventory_value = Decimal(str(raw_inv_value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    average_product_price = Decimal(str(raw_avg_price)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    # 2. Product counts grouped by category
    cat_stmt = select(Product.category, func.count(Product.id)).group_by(Product.category)
    cat_result = await session.execute(cat_stmt)
    products_by_category = {cat: count for cat, count in cat_result.all()}

    return DashboardStatsResponse(
        total_products=total_products,
        total_inventory_value=total_inventory_value,
        average_product_price=average_product_price,
        products_by_category=products_by_category,
    )
