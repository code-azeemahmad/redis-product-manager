# Redis-Backed Rate Limiting

## 1. Scope

The initial rate limiter is best-effort protection for selected API endpoints. Redis counters are disposable. This mechanism is not the only security control and is not suitable as the sole enforcement mechanism for high-risk financial, authentication, or business-critical actions.

## 2. Algorithm

A fixed-window counter is a suitable initial implementation:

1. Derive a caller identifier from a trusted source (for example, client IP as observed through Nginx).
2. Build a namespaced key containing policy version, endpoint/policy name, and a privacy-safe identifier or keyed hash.
3. Atomically increment the counter and set its expiry on first increment.
4. Compare the count with the configured maximum.
5. Reject over-limit requests with HTTP 429 and `Retry-After`.

Use a Redis Lua script or another atomic operation to combine `INCR` and first-write `EXPIRE`; avoid a crash window that leaves a counter without expiry. Document that fixed windows can permit bursts around window boundaries. Use a sliding-window/token-bucket algorithm only if requirements justify the extra complexity.

## 3. Configuration

The following are configuration decisions, not fixed values in the supplied brief:

- Which endpoints are limited.
- Maximum requests per window for each endpoint.
- Window duration.
- Whether limits differ by trusted authenticated identity (only after auth is designed) or client IP.
- Whether local/development environments bypass or relax limits.

Keep policy values in validated application settings, not hard-coded inside route functions.

## 4. Client identity and proxy trust

- Nginx is the intended entry point.
- Only trust `X-Forwarded-For` / `X-Real-IP` values added by the known proxy path.
- Do not trust arbitrary forwarded headers from direct public clients.
- Configure FastAPI/Uvicorn proxy-header behavior and trusted proxy addresses deliberately.
- If the backend port is reachable directly from outside the private network, forwarded-IP spoofing may become possible; prevent direct public access.
- Avoid storing raw IP addresses in logs/metrics longer than needed. Consider hashing identifiers for Redis keys while preserving enough operational value for abuse investigation.

## 5. Redis failure mode

The project brief selects best-effort behavior: if Redis is unavailable, the rate-limit check is bypassed and a structured degradation event is emitted. This means abuse controls are weaker during Redis outages. Apply other protections at Nginx/host/network layers as appropriate.

If strict rate-limit guarantees become necessary, isolate rate-limit state from disposable cache data and configure its durability/eviction policy separately. A shared Redis instance with an eviction policy intended for cache keys can evict rate-limit counters and silently weaken enforcement.

## 6. Memory and eviction considerations

- Counter keys must always have expiry.
- Set Redis maxmemory and an explicit eviction policy.
- Do not assume a cache eviction policy preserves rate-limit state.
- Prefer a separate Redis instance/cluster or an independently protected workload for strict counters.

## 7. Response behavior

When a caller exceeds a policy:

- Return `429 Too Many Requests`.
- Include `Retry-After` when the reset time is known.
- Do not reveal internal Redis keys, raw identity data, or policy internals.
- Include tests for allowed requests, threshold crossing, expiry/reset, concurrent increments, and Redis outage behavior.
