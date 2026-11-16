"""Unit tests for Pydantic product schema validation and serialization."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)


def test_product_create_valid():
    payload = ProductCreate(
        name="  Clean Mechanical Keyboard  ",
        price=Decimal("85.00"),
        category="  Electronics  ",
        stock=25,
    )
    # Whitespace must be stripped
    assert payload.name == "Clean Mechanical Keyboard"
    assert payload.category == "Electronics"
    assert payload.price == Decimal("85.00")
    assert payload.stock == 25


def test_product_create_zero_price_and_stock():
    payload = ProductCreate(
        name="Free Sample",
        price=Decimal("0.00"),
        category="Promotions",
        stock=0,
    )
    assert payload.price == Decimal("0.00")
    assert payload.stock == 0


def test_product_create_rejects_blank_strings():
    with pytest.raises(ValidationError):
        ProductCreate(name="   ", price=Decimal("10.00"), category="Cat", stock=1)

    with pytest.raises(ValidationError):
        ProductCreate(name="Item", price=Decimal("10.00"), category="   ", stock=1)


def test_product_create_rejects_excessive_decimal_places():
    with pytest.raises(ValidationError):
        ProductCreate(name="Item", price=Decimal("10.999"), category="Cat", stock=1)


def test_product_response_price_serialization():
    now = datetime.now(timezone.utc)
    resp = ProductResponse(
        id=1,
        name="Item",
        price=Decimal("49.9"),
        category="Cat",
        stock=10,
        created_at=now,
        updated_at=now,
    )
    dumped = resp.model_dump(mode="json")
    # Must serialize as 2-decimal place string "49.90"
    assert dumped["price"] == "49.90"
    assert isinstance(dumped["price"], str)
