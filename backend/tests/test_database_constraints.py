"""Tests verifying that PostgreSQL database-level constraints are enforced."""

from decimal import Decimal
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session_factory
from app.database.models import Product


@pytest.mark.asyncio
async def test_db_check_constraint_negative_price():
    """Ensure PostgreSQL rejects negative price even if ORM validation was bypassed."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        bad_product = Product(
            name="Raw SQL Bad Price",
            price=Decimal("-10.00"),
            category="Test",
            stock=5,
        )
        session.add(bad_product)
        with pytest.raises(IntegrityError) as exc_info:
            await session.commit()
        assert "ck_product_price_non_negative" in str(exc_info.value).lower()
        await session.rollback()


@pytest.mark.asyncio
async def test_db_check_constraint_negative_stock():
    """Ensure PostgreSQL rejects negative stock even if ORM validation was bypassed."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        bad_product = Product(
            name="Raw SQL Bad Stock",
            price=Decimal("10.00"),
            category="Test",
            stock=-5,
        )
        session.add(bad_product)
        with pytest.raises(IntegrityError) as exc_info:
            await session.commit()
        assert "ck_product_stock_non_negative" in str(exc_info.value).lower()
        await session.rollback()
