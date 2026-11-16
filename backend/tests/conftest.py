"""Pytest fixtures and configuration."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.database.connection import close_async_engine
from app.services.redis_service import close_redis_client
from app.main import app


@pytest.fixture(autouse=True)
async def cleanup_resources():
    """Ensure database engine and Redis pool are cleanly disposed at the end of each test."""
    yield
    await close_async_engine()
    await close_redis_client()


@pytest.fixture
async def client():
    """Async HTTP test client with isolated client IP to avoid cross-test rate limit collision."""
    unique_test_ip = f"198.51.100.{uuid.uuid4().hex[:6]}"
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-Forwarded-For": unique_test_ip},
    ) as ac:
        yield ac

