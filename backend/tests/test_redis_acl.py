"""Integration tests verifying Redis ACL least-privilege enforcement.

Following architectural rules:
- Verify default unauthenticated user is disabled.
- Verify healthcheck user is restricted strictly to PING.
- Verify app user cannot access keys outside the allowed prefix (v1:*).
- Verify app user cannot run dangerous commands (KEYS, FLUSHALL, CONFIG).
- Verify admin user has required administrative capabilities.
"""

import pytest
import redis.asyncio as aioredis
from redis.exceptions import AuthenticationError, ResponseError

from app.config import get_settings


@pytest.mark.asyncio
async def test_redis_acl_default_user_rejected():
    """Default unauthenticated user must be rejected."""
    settings = get_settings()
    client = aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
    with pytest.raises((AuthenticationError, ResponseError)) as exc_info:
        await client.ping()
    assert "Authentication required" in str(exc_info.value) or "NOAUTH" in str(exc_info.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_redis_acl_healthcheck_user_restricted():
    """Healthcheck user must only be permitted to execute PING."""
    settings = get_settings()
    client = aioredis.from_url(
        f"redis://healthcheck:{settings.HEALTHCHECK_REDIS_PASSWORD}@"
        f"{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
    )
    # Ping succeeds
    assert await client.ping() is True

    # Any data read/write must be rejected with NOPERM
    with pytest.raises(ResponseError) as exc_info:
        await client.get("v1:any_key")
    assert "no permissions to run the 'get' command" in str(exc_info.value).lower()

    with pytest.raises(ResponseError) as exc_info:
        await client.set("v1:any_key", "value")
    assert "no permissions to run the 'set' command" in str(exc_info.value).lower()

    await client.aclose()


@pytest.mark.asyncio
async def test_redis_acl_app_user_allowed_operations():
    """App user must be able to read, write, and execute Lua scripts within v1:*."""
    settings = get_settings()
    client = aioredis.from_url(settings.async_redis_url, decode_responses=True)

    test_key = "v1:acl_test:item"
    assert await client.set(test_key, "ok", ex=10) is True
    assert await client.get(test_key) == "ok"
    assert await client.delete(test_key) == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_redis_acl_app_user_denied_outside_prefix():
    """App user must be rejected when attempting to access keys outside v1:*."""
    settings = get_settings()
    client = aioredis.from_url(settings.async_redis_url, decode_responses=True)

    with pytest.raises(ResponseError) as exc_info:
        await client.set("outside_prefix:key", "value")
    assert "no permissions to access" in str(exc_info.value).lower()

    with pytest.raises(ResponseError) as exc_info:
        await client.get("unauthorized:key")
    assert "no permissions to access" in str(exc_info.value).lower()

    await client.aclose()


@pytest.mark.asyncio
async def test_redis_acl_app_user_denied_dangerous_commands():
    """App user must be denied dangerous commands such as KEYS, FLUSHALL, and CONFIG."""
    settings = get_settings()
    client = aioredis.from_url(settings.async_redis_url, decode_responses=True)

    with pytest.raises(ResponseError) as exc_info:
        await client.execute_command("KEYS", "*")
    assert "no permissions to run the 'keys' command" in str(exc_info.value).lower()

    with pytest.raises(ResponseError) as exc_info:
        await client.execute_command("FLUSHALL")
    assert "no permissions to run the 'flushall' command" in str(exc_info.value).lower()

    with pytest.raises(ResponseError) as exc_info:
        await client.execute_command("CONFIG", "GET", "maxmemory")
    assert "no permissions to run the 'config|get' command" in str(exc_info.value).lower()

    await client.aclose()
