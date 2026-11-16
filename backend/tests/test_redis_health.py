"""Tests for health readiness reporting with Redis healthy and degraded."""

from unittest.mock import AsyncMock
import pytest
from httpx import AsyncClient

from app.dependencies import get_redis_service
from app.main import app
from app.services.redis_service import RedisService


@pytest.mark.asyncio
async def test_health_ready_both_healthy(client: AsyncClient):
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["dependencies"]["postgres"] == "healthy"
    assert data["dependencies"]["redis"] == "healthy"


@pytest.mark.asyncio
async def test_health_ready_redis_degraded(client: AsyncClient):
    """When Redis is unavailable, service readiness remains 200 with Redis marked as degraded."""
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = False
    degraded_service = RedisService(mock_redis)

    app.dependency_overrides[get_redis_service] = lambda: degraded_service
    try:
        resp = await client.get("/health/ready")
        # Readiness remains 200 because Redis is optional for product operations
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["dependencies"]["postgres"] == "healthy"
        assert data["dependencies"]["redis"] == "degraded"
    finally:
        app.dependency_overrides.pop(get_redis_service, None)
