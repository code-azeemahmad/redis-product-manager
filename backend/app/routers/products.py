"""HTTP API router for Product CRUD operations.

Following architectural rules:
- Route handlers focus strictly on HTTP concerns (status codes, query parsing, responses).
- Business operations delegated to `product_service`.
- Cache-aside for reads: product detail (300s TTL) and product list (120s TTL).
- Post-commit cache invalidation: deletes detail key and advances list/dashboard generations.
- Redis failures never block or fail database operations.
"""

from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import policies
from app.dependencies import get_db_session, get_redis_service
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services import product_service
from app.services.rate_limiter import rate_limit_mutations
from app.services.redis_service import RedisService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    dependencies=[Depends(rate_limit_mutations)],
)
async def create_product(
    product_in: ProductCreate,
    session: AsyncSession = Depends(get_db_session),
    redis_service: RedisService = Depends(get_redis_service),
) -> ProductResponse:
    """Create a new product record in PostgreSQL and invalidate list/dashboard caches."""
    product = await product_service.create_product(session, product_in)
    resp = ProductResponse.model_validate(product)

    # Invalidate cache namespaces post-commit
    await policies.invalidate_product_caches(redis_service)

    return resp


@router.get(
    "",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List products with filtering, pagination, and sorting",
)
async def list_products(
    category: Optional[str] = Query(
        None,
        max_length=100,
        description="Filter by category",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Literal["id", "name", "price", "category", "stock", "created_at"] = Query(
        "id",
        description="Allowlisted column to sort by",
    ),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort direction"),
    session: AsyncSession = Depends(get_db_session),
    redis_service: RedisService = Depends(get_redis_service),
) -> ProductListResponse:
    """Retrieve a paginated list of products with 120-second cache-aside."""
    # 1. Attempt cache read
    cached = await policies.get_cached_product_list(
        redis_service=redis_service,
        category=category,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    if cached is not None:
        return cached

    # 2. On miss, query PostgreSQL
    items, total, pages = await product_service.list_products(
        session=session,
        category=category,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    list_resp = ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in items],
        page=page,
        limit=limit,
        total=total,
        pages=pages,
    )

    # 3. Attempt cache write
    await policies.set_cached_product_list(
        redis_service=redis_service,
        list_response=list_resp,
        category=category,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return list_resp


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_db_session),
    redis_service: RedisService = Depends(get_redis_service),
) -> ProductResponse:
    """Retrieve a single product by primary key with 300-second cache-aside."""
    # 1. Attempt cache read
    cached = await policies.get_cached_product(redis_service, product_id)
    if cached is not None:
        return cached

    # 2. On miss, query PostgreSQL
    product = await product_service.get_product_by_id(session, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    resp = ProductResponse.model_validate(product)

    # 3. Attempt cache write
    await policies.set_cached_product(redis_service, resp)

    return resp


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product by ID",
    dependencies=[Depends(rate_limit_mutations)],
)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    session: AsyncSession = Depends(get_db_session),
    redis_service: RedisService = Depends(get_redis_service),
) -> ProductResponse:
    """Update an existing product and invalidate detail, list, and dashboard caches."""
    updated = await product_service.update_product(session, product_id, product_in)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    resp = ProductResponse.model_validate(updated)

    # Post-commit invalidation
    await policies.invalidate_product_caches(redis_service, product_id=product_id)

    return resp


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product by ID",
    dependencies=[Depends(rate_limit_mutations)],
)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db_session),
    redis_service: RedisService = Depends(get_redis_service),
) -> None:
    """Delete a product by primary key and invalidate detail, list, and dashboard caches."""
    deleted = await product_service.delete_product(session, product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    # Post-commit invalidation
    await policies.invalidate_product_caches(redis_service, product_id=product_id)
