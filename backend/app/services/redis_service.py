"""Asynchronous Redis service layer.

Following architectural rules:
- Strictly asynchronous via `redis.asyncio`.
- Reusable bounded connection pool initialized during app lifespan.
- Finite socket and connection timeouts.
- Graceful degradation: errors and timeouts are caught, logged, and return safe fallback values
  so product correctness never depends on Redis availability.
"""

import logging
from typing import Optional
import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)

_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[aioredis.Redis] = None

# Atomic Lua script to increment generation counter.
# If key does not exist, sets to 2 (since absent is treated as generation 1);
# otherwise increments existing value.
INCR_GENERATION_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    return redis.call('INCR', KEYS[1])
else
    redis.call('SET', KEYS[1], 2)
    return 2
end
"""


def get_redis_client() -> aioredis.Redis:
    """Return or initialize the singleton Redis client with bounded connection pool."""
    global _redis_pool, _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_pool = ConnectionPool.from_url(
            settings.async_redis_url,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
            decode_responses=True,
        )
        _redis_client = aioredis.Redis.from_pool(_redis_pool)
    return _redis_client


async def close_redis_client() -> None:
    """Dispose of the Redis client and bounded connection pool."""
    global _redis_pool, _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception as exc:
            logger.warning("Error closing Redis client: %s", exc)
        _redis_client = None

    if _redis_pool is not None:
        try:
            await _redis_pool.aclose()
        except Exception as exc:
            logger.warning("Error closing Redis pool: %s", exc)
        _redis_pool = None


class RedisService:
    """Wrapper around redis.asyncio.Redis providing safe primitives with controlled fallbacks."""

    def __init__(self, client: Optional[aioredis.Redis] = None):
        self._client = client or get_redis_client()

    async def ping(self) -> bool:
        """Check Redis availability. Returns True if responsive, False otherwise."""
        try:
            return bool(await self._client.ping())
        except (RedisError, OSError) as exc:
            logger.warning("Redis ping failed: %s", exc)
            return False

    async def get(self, key: str) -> Optional[str]:
        """Retrieve a cached string value. Returns None on cache miss or Redis error."""
        try:
            return await self._client.get(key)
        except (RedisError, OSError) as exc:
            logger.warning("Redis GET failed for key '%s': %s", key, exc)
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Store a string value with optional TTL in seconds. Returns True on success, False on error."""
        try:
            await self._client.set(name=key, value=value, ex=expire)
            return True
        except (RedisError, OSError) as exc:
            logger.warning("Redis SET failed for key '%s': %s", key, exc)
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis. Returns True on success, False on error."""
        try:
            await self._client.delete(key)
            return True
        except (RedisError, OSError) as exc:
            logger.warning("Redis DELETE failed for key '%s': %s", key, exc)
            return False

    async def incr(self, key: str) -> Optional[int]:
        """Atomically increment an integer key. Returns the new integer value or None on error."""
        try:
            return await self._client.incr(key)
        except (RedisError, OSError) as exc:
            logger.warning("Redis INCR failed for key '%s': %s", key, exc)
            return None

    async def get_generation(self, key: str) -> int:
        """Fetch current generation integer counter. Returns 1 if absent or on Redis error."""
        val = await self.get(key)
        if val is None:
            return 1
        try:
            return int(val)
        except (ValueError, TypeError):
            return 1

    async def increment_generation(self, key: str) -> int:
        """Atomically increment generation key for invalidation. Returns updated generation or 1 on error."""
        try:
            return int(await self._client.eval(INCR_GENERATION_SCRIPT, 1, key))
        except (RedisError, OSError) as exc:
            logger.warning("Redis increment_generation failed for key '%s': %s", key, exc)
            return 1

    async def eval_script(self, script: str, keys: list[str], args: list[object]) -> Optional[int]:
        """Execute a Lua script atomically. Returns integer result or None on Redis error."""
        try:
            res = await self._client.eval(script, len(keys), *keys, *args)
            return int(res) if res is not None else None
        except (RedisError, OSError) as exc:
            logger.warning("Redis eval_script failed: %s", exc)
            return None
