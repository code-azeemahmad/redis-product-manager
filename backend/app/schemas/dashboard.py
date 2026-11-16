"""Pydantic schemas for Dashboard statistics."""

from decimal import Decimal
from typing import Dict
from pydantic import BaseModel, ConfigDict, field_serializer


class DashboardStatsResponse(BaseModel):
    """Aggregate dashboard statistics model."""

    model_config = ConfigDict(from_attributes=True)

    total_products: int
    total_inventory_value: Decimal
    average_product_price: Decimal
    products_by_category: Dict[str, int]

    @field_serializer("total_inventory_value", "average_product_price")
    def serialize_decimal(self, val: Decimal, _info) -> str:
        """Format monetary amount as a decimal string with two decimal places."""
        return f"{val:.2f}"
