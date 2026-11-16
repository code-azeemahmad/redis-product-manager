"""Integration and unit tests for atomic fixed-window rate limiting and proxy trust."""

import time
import uuid
from unittest.mock import AsyncMock
from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient
import pytest
from redis.exceptions import ConnectionError

from app.config import get_settings
from app.dependencies import get_redis_service
from app.services.rate_limiter import (
    RateLimiter,
    get_client_identifier_hash,
    get_client_ip,
    is_ip_in_network,
)
from app.services.redis_service import RedisService, get_redis_client


def test_ip_network_evaluation():
    assert is_ip_in_network("127.0.0.1", "127.0.0.1") is True
    assert is_ip_in_network("172.18.0.2", "172.16.0.0/12") is True
    assert is_ip_in_network("10.0.1.5", "10.0.0.0/8") is True
    assert is_ip_in_network("8.8.8.8", "10.0.0.0/8") is False
    assert is_ip_in_network("invalid-ip", "10.0.0.0/8") is False


def test_client_ip_extraction_and_proxy_trust():
    trusted = ["127.0.0.1", "172.16.0.0/12"]

    # 1. From trusted proxy with X-Forwarded-For
    req_trusted = AsyncMock()
    req_trusted.client.host = "172.18.0.1"
    req_trusted.headers = {"X-Forwarded-For": "203.0.113.50, 172.18.0.1"}
    assert get_client_ip(req_trusted, trusted) == "203.0.113.50"

    # 2. From untrusted direct client with spoofed X-Forwarded-For
    req_untrusted = AsyncMock()
    req_untrusted.client.host = "198.51.100.99"
    req_untrusted.headers = {"X-Forwarded-For": "1.1.1.1"}
    assert get_client_ip(req_untrusted, trusted) == "198.51.100.99"


def test_client_identifier_hashing():
    hash1 = get_client_identifier_hash("192.168.1.1")
    hash2 = get_client_identifier_hash("192.168.1.1")
    hash3 = get_client_identifier_hash("192.168.1.2")
    assert len(hash1) == 16
    assert hash1 == hash2
    assert hash1 != hash3


@pytest.mark.asyncio
async def test_rate_limiter_enforcement_and_retry_after(client: AsyncClient):
    """Test that exceeding the rate limit returns 429 with Retry-After header."""
    # Create custom test limiter allowing only 2 requests per window
    strict_limiter = RateLimiter("test:strict", max_requests=2, window_seconds=30)

    test_app = FastAPI()

    @test_app.get("/test-limited", dependencies=[Depends(strict_limiter)])
    async def limited_route():
        return {"ok": True}

    test_ip = f"192.0.2.{uuid.uuid4().hex[:6]}"
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        # Request 1: OK
        r1 = await ac.get("/test-limited", headers={"X-Forwarded-For": test_ip})
        assert r1.status_code == 200

        # Request 2: OK
        r2 = await ac.get("/test-limited", headers={"X-Forwarded-For": test_ip})
        assert r2.status_code == 200

        # Request 3: Blocked with 429
        r3 = await ac.get("/test-limited", headers={"X-Forwarded-For": test_ip})
        assert r3.status_code == 429
        assert "Retry-After" in r3.headers
        retry_after = int(r3.headers["Retry-After"])
        assert 0 < retry_after <= 30
        assert r3.headers["X-RateLimit-Limit"] == "2"
        assert r3.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_rate_limiter_outage_bypass():
    """Verify rate limiter allows requests through if Redis fails (best-effort policy)."""
    failing_redis = AsyncMock()
    failing_redis.eval_script.side_effect = ConnectionError("Redis unreachable")

    limiter = RateLimiter("test:bypass", max_requests=1, window_seconds=60)
    fake_request = AsyncMock()
    fake_request.client.host = "127.0.0.1"
    fake_request.headers = {}

    # Must complete without raising HTTPException(429) or unhandled error
    await limiter(fake_request, failing_redis)
