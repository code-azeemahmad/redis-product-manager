"""Product domain service layer.

Encapsulates business operations, queries, and transactions against PostgreSQL.
"""

import math
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Product
from app.schemas.product import ProductCreate, ProductUpdate

# Allowlisted columns for sorting to prevent arbitrary SQL injection
SORT_COLUMNS = {
    "id": Product.id,
    "name": Product.name,
    "price": Product.price,
    "category": Product.category,
    "stock": Product.stock,
    "created_at": Product.created_at,
}


async def create_product(session: AsyncSession, data: ProductCreate) -> Product:
    """Create and persist a new product."""
    product = Product(
        name=data.name,
        price=data.price,
        category=data.category,
        stock=data.stock,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def get_product_by_id(session: AsyncSession, product_id: int) -> Optional[Product]:
    """Retrieve a single product by primary key."""
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_products(
    session: AsyncSession,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "id",
    sort_order: str = "asc",
) -> Tuple[List[Product], int, int]:
    """List products with filtering, pagination, and validated sorting.

    Returns:
        (items, total_count, total_pages)
    """
    # 1. Base filter
    filter_clauses = []
    if category:
        normalized_category = category.strip()
        filter_clauses.append(Product.category.ilike(normalized_category))

    # 2. Count total records
    count_stmt = select(func.count(Product.id))
    if filter_clauses:
        count_stmt = count_stmt.where(*filter_clauses)
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # 3. Apply sorting
    sort_col = SORT_COLUMNS.get(sort_by, Product.id)
    order_clause = sort_col.desc() if sort_order.lower() == "desc" else sort_col.asc()

    # 4. Paginated items query
    offset = (page - 1) * limit
    items_stmt = select(Product)
    if filter_clauses:
        items_stmt = items_stmt.where(*filter_clauses)
    items_stmt = items_stmt.order_by(order_clause).offset(offset).limit(limit)

    items_result = await session.execute(items_stmt)
    items = list(items_result.scalars().all())

    pages = math.ceil(total / limit) if total > 0 else 0
    return items, total, pages


async def update_product(
    session: AsyncSession,
    product_id: int,
    data: ProductUpdate,
) -> Optional[Product]:
    """Update an existing product with full replacement semantics."""
    product = await get_product_by_id(session, product_id)
    if product is None:
        return None

    product.name = data.name
    product.price = data.price
    product.category = data.category
    product.stock = data.stock

    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(session: AsyncSession, product_id: int) -> bool:
    """Delete a product by primary key.

    Returns True if product existed and was deleted, False if not found.
    """
    product = await get_product_by_id(session, product_id)
    if product is None:
        return False

    await session.delete(product)
    await session.commit()
    return True
