"""Pydantic schemas for Product validation and serialization.

Following architectural rules:
- Prices strictly parsed and serialized using Decimal (never binary float).
- Inputs validated at the API boundary with trimmed whitespace and strict bounds.
- Pagination envelope consistent with AD-008.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class ProductBase(BaseModel):
    """Base fields shared across product request schemas."""

    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    price: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        decimal_places=2,
        description="Non-negative unit price with up to 2 decimal places",
    )
    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category label for filtering",
    )
    stock: int = Field(default=0, ge=0, description="Available stock quantity")

    @field_validator("name", "category", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Value cannot be blank or only whitespace")
        return v

    @field_validator("price", mode="before")
    @classmethod
    def validate_price_input(cls, v: object) -> object:
        if isinstance(v, float):
            raise ValueError(
                "Floating-point prices are prohibited. Pass price as a string or Decimal."
            )
        return v


class ProductCreate(ProductBase):
    """Schema for product creation (POST /api/products)."""
    pass


class ProductUpdate(ProductBase):
    """Schema for product replacement (PUT /api/products/{id})."""
    pass


class ProductResponse(BaseModel):
    """Schema for product serialization in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    category: str
    stock: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("price")
    def serialize_price(self, price: Decimal, _info) -> str:
        """Format monetary amount as a decimal string with two decimal places."""
        return f"{price:.2f}"


class ProductListResponse(BaseModel):
    """Paginated product list response envelope (AD-008)."""

    items: List[ProductResponse]
    page: int
    limit: int
    total: int
    pages: int
