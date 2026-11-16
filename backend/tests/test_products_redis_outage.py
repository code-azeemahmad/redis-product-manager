"""Integration tests verifying product operations continue to work when Redis is completely unavailable."""

from unittest.mock import AsyncMock
import pytest
from httpx import AsyncClient

from app.dependencies import get_redis_service
from app.main import app
from app.services.redis_service import RedisService


@pytest.fixture
def broken_redis_service():
    """Simulate complete Redis failure (connection refused / network outage)."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = False
    mock_client.get.return_value = None
    mock_client.set.return_value = False
    mock_client.delete.return_value = False
    mock_client.incr.return_value = None
    mock_client.eval.return_value = 1
    return RedisService(mock_client)


@pytest.mark.asyncio
async def test_product_crud_with_redis_outage(client: AsyncClient, broken_redis_service):
    """Architectural invariant check:

    Redis failure must not fail product operations.
    Authoritative operations must continue working against PostgreSQL.
    """
    app.dependency_overrides[get_redis_service] = lambda: broken_redis_service

    try:
        # 1. Readiness reports degraded Redis, but still returns 200 ready
        ready_resp = await client.get("/health/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["dependencies"]["redis"] == "degraded"
        assert ready_resp.json()["dependencies"]["postgres"] == "healthy"

        # 2. Product Create succeeds
        create_resp = await client.post(
            "/api/products",
            json={
                "name": "Outage Test Item",
                "price": "35.50",
                "category": "Resilience",
                "stock": 4,
            },
        )
        assert create_resp.status_code == 201
        product_id = create_resp.json()["id"]

        # 3. Product Get succeeds
        get_resp = await client.get(f"/api/products/{product_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Outage Test Item"
        assert get_resp.json()["price"] == "35.50"

        # 4. Product List succeeds
        list_resp = await client.get("/api/products?category=Resilience")
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        assert any(item["id"] == product_id for item in items)

        # 5. Product Update succeeds
        update_resp = await client.put(
            f"/api/products/{product_id}",
            json={
                "name": "Updated Outage Item",
                "price": "39.99",
                "category": "Resilience",
                "stock": 10,
            },
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated Outage Item"
        assert update_resp.json()["price"] == "39.99"

        # 6. Product Delete succeeds
        del_resp = await client.delete(f"/api/products/{product_id}")
        assert del_resp.status_code == 204

        # 7. Subsequent Get returns 404
        assert (await client.get(f"/api/products/{product_id}")).status_code == 404

    finally:
        app.dependency_overrides.pop(get_redis_service, None)
