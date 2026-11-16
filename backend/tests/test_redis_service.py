"""Integration tests for RedisService and graceful error handling."""

from unittest.mock import AsyncMock
import pytest
from redis.exceptions import ConnectionError, TimeoutError

from app.services.redis_service import RedisService, get_redis_client


@pytest.mark.asyncio
async def test_redis_service_live_operations():
    service = RedisService(get_redis_client())

    # 1. Ping
    assert await service.ping() is True

    # 2. Set, Get, Delete (using standard versioned v1: prefix)
    key = "v1:test:live:item"
    assert await service.set(key, "hello_world", expire=60) is True
    val = await service.get(key)
    assert val == "hello_world"
    assert await service.delete(key) is True
    assert await service.get(key) is None

    # 3. Increment
    counter_key = "v1:test:live:counter"
    await service.delete(counter_key)
    assert await service.incr(counter_key) == 1
    assert await service.incr(counter_key) == 2
    await service.delete(counter_key)

    # 4. Generation handling
    gen_key = "v1:test:live:gen"
    await service.delete(gen_key)
    assert await service.get_generation(gen_key) == 1
    new_gen = await service.increment_generation(gen_key)
    assert new_gen == 2
    assert await service.get_generation(gen_key) == 2
    await service.delete(gen_key)


@pytest.mark.asyncio
async def test_redis_service_graceful_error_handling():
    """Verify that RedisService methods do not raise exceptions on network/connection errors."""
    mock_client = AsyncMock()
    mock_client.ping.side_effect = ConnectionError("Connection refused")
    mock_client.get.side_effect = TimeoutError("Socket timeout")
    mock_client.set.side_effect = ConnectionError("Network down")
    mock_client.delete.side_effect = ConnectionError("Network down")
    mock_client.incr.side_effect = ConnectionError("Network down")

    failing_service = RedisService(mock_client)

    # All methods must catch exceptions and return safe fallback values
    assert await failing_service.ping() is False
    assert await failing_service.get("any_key") is None
    assert await failing_service.set("any_key", "val") is False
    assert await failing_service.delete("any_key") is False
    assert await failing_service.incr("any_key") is None
    assert await failing_service.get_generation("any_key") == 1
    assert await failing_service.increment_generation("any_key") == 1
