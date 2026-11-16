"""Redis-backed atomic fixed-window rate limiter service.

Following architectural rules:
- Atomic increment and expiry via Redis Lua script (prevents orphan keys without TTL).
- Trusted proxy evaluation: only trusts forwarded headers from configured proxy CIDRs.
- Privacy-safe key construction using SHA-256 hashed client identities.
- HTTP 429 response with RFC-compliant Retry-After header.
- Best-effort failure model: Redis outages gracefully bypass enforcement with degradation logging.
"""

import hashlib
import ipaddress
import logging
import time
from typing import List, Optional
from fastapi import Depends, HTTPException, Request, status

from app.config import get_settings
from app.core.metrics import metrics
from app.dependencies import get_redis_service
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

# Atomic Lua script: increment and set TTL on first write
RATE_LIMIT_LUA_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


def is_ip_in_network(client_ip: str, network_or_ip: str) -> bool:
    """Check if client_ip belongs to network_or_ip CIDR block."""
    try:
        ip = ipaddress.ip_address(client_ip)
        net = ipaddress.ip_network(network_or_ip, strict=False)
        return ip in net
    except ValueError:
        return False


def get_client_ip(request: Request, trusted_proxies: List[str]) -> str:
    """Extract client IP, evaluating X-Forwarded-For only if direct client is a trusted proxy."""
    direct_ip = request.client.host if request.client else "127.0.0.1"

    # Only trust proxy headers if direct socket is from a trusted proxy
    is_trusted = any(is_ip_in_network(direct_ip, proxy) for proxy in trusted_proxies)
    if is_trusted:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # First IP in X-Forwarded-For is the originating client
            client_ip = forwarded.split(",")[0].strip()
            if client_ip:
                return client_ip
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    return direct_ip


def get_client_identifier_hash(client_ip: str) -> str:
    """Generate truncated SHA-256 hash for privacy-safe key construction."""
    return hashlib.sha256(client_ip.encode("utf-8")).hexdigest()[:16]


class RateLimiter:
    """Callable FastAPI dependency enforcing atomic fixed-window rate limits."""

    def __init__(
        self,
        policy: str,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        self.policy = policy
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(
        self,
        request: Request,
        redis_service: RedisService = Depends(get_redis_service),
    ) -> None:
        settings = get_settings()
        if not settings.RATE_LIMIT_ENABLED:
            return

        client_ip = get_client_ip(request, settings.trusted_proxies_list)
        ident_hash = get_client_identifier_hash(client_ip)

        now = int(time.time())
        bucket = now // self.window_seconds
        remaining_seconds = max(1, self.window_seconds - (now % self.window_seconds))

        key = (
            f"{settings.CACHE_KEY_PREFIX}:ratelimit:"
            f"{self.policy}:{ident_hash}:{bucket}"
        )

        try:
            # Execute atomic INCR + EXPIRE Lua script
            current_count = await redis_service.eval_script(
                RATE_LIMIT_LUA_SCRIPT,
                keys=[key],
                args=[self.window_seconds],
            )

            if current_count is not None and current_count > self.max_requests:
                metrics.record_rate_limit_event(self.policy, "blocked")
                logger.warning(
                    "Rate limit exceeded: policy=%s, client=%s, count=%d, limit=%d",
                    self.policy,
                    ident_hash,
                    current_count,
                    self.max_requests,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={
                        "Retry-After": str(remaining_seconds),
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(remaining_seconds),
                    },
                )

            # Request is within limit
            metrics.record_rate_limit_event(self.policy, "allowed")
        except HTTPException:
            raise
        except Exception as exc:
            # Best-effort policy: degrade gracefully during Redis failures
            metrics.record_rate_limit_event(self.policy, "bypassed_error")
            logger.warning(
                "Rate limiter bypassed due to Redis error (policy=%s): %s",
                self.policy,
                exc,
            )


# Preconfigured rate limiter dependencies for routes
rate_limit_mutations = RateLimiter("products:write", max_requests=20, window_seconds=60)
rate_limit_dashboard = RateLimiter("dashboard:read", max_requests=30, window_seconds=60)
