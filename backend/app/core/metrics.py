"""In-memory Prometheus-compatible metrics registry and exposition formatter.

Following architectural rules:
- Strictly bounded cardinality: labels are static or controlled categories (method, route template, status class/code, policy, outcome).
- No arbitrary user inputs, database IDs, raw IPs, or unstructured paths in metric labels.
- Lightweight and dependency-free format matching Prometheus text specification (v0.0.4).
- Safe and graceful fallbacks when dependencies are degraded.
"""

from collections import defaultdict
import threading
from typing import Any, Dict, Tuple


class MetricsRegistry:
    """Thread-safe metrics registry for HTTP, database, Redis, and cache telemetry."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # (method, route, status) -> count
        self._http_requests: Dict[Tuple[str, str, int], int] = defaultdict(int)
        # (method, route) -> (count, sum_seconds)
        self._http_duration: Dict[Tuple[str, str], Tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        # (operation, outcome) -> count
        self._cache_events: Dict[Tuple[str, str], int] = defaultdict(int)
        # (policy, decision) -> count
        self._rate_limit_events: Dict[Tuple[str, str], int] = defaultdict(int)

    def record_http_request(
        self,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """Record an incoming HTTP request and its processing duration."""
        # Sanitize and bound route
        safe_route = route if route.startswith("/") else f"/{route}"
        with self._lock:
            self._http_requests[(method.upper(), safe_route, status_code)] += 1
            count, total_dur = self._http_duration[(method.upper(), safe_route)]
            self._http_duration[(method.upper(), safe_route)] = (
                count + 1,
                total_dur + duration_seconds,
            )

    def record_cache_event(self, operation: str, outcome: str) -> None:
        """Record cache event: hit, miss, written, invalidated, error."""
        with self._lock:
            self._cache_events[(operation, outcome)] += 1

    def record_rate_limit_event(self, policy: str, decision: str) -> None:
        """Record rate-limit evaluation: allowed, blocked, bypassed_error."""
        with self._lock:
            self._rate_limit_events[(policy, decision)] += 1

    def reset(self) -> None:
        """Reset all counters (primarily used for test isolation)."""
        with self._lock:
            self._http_requests.clear()
            self._http_duration.clear()
            self._cache_events.clear()
            self._rate_limit_events.clear()

    async def export_prometheus_text(
        self,
        db_engine: Any = None,
        redis_service: Any = None,
    ) -> str:
        """Format and return current metrics in Prometheus exposition text format."""
        lines = []

        with self._lock:
            # 1. HTTP Request Count
            lines.append("# HELP http_requests_total Total number of HTTP requests processed.")
            lines.append("# TYPE http_requests_total counter")
            for (method, route, status), count in sorted(self._http_requests.items()):
                lines.append(
                    f'http_requests_total{{method="{method}",route="{route}",status="{status}"}} {count}'
                )

            # 2. HTTP Request Duration
            lines.append("# HELP http_request_duration_seconds HTTP request duration summary.")
            lines.append("# TYPE http_request_duration_seconds summary")
            for (method, route), (count, total_dur) in sorted(self._http_duration.items()):
                lines.append(
                    f'http_request_duration_seconds_count{{method="{method}",route="{route}"}} {count}'
                )
                lines.append(
                    f'http_request_duration_seconds_sum{{method="{method}",route="{route}"}} {round(total_dur, 6)}'
                )

            # 3. Cache Events
            lines.append("# HELP cache_events_total Total number of cache operations and outcomes.")
            lines.append("# TYPE cache_events_total counter")
            for (operation, outcome), count in sorted(self._cache_events.items()):
                lines.append(
                    f'cache_events_total{{operation="{operation}",outcome="{outcome}"}} {count}'
                )

            # 4. Rate Limit Decisions
            lines.append("# HELP rate_limit_events_total Total number of rate limit decisions.")
            lines.append("# TYPE rate_limit_events_total counter")
            for (policy, decision), count in sorted(self._rate_limit_events.items()):
                lines.append(
                    f'rate_limit_events_total{{policy="{policy}",decision="{decision}"}} {count}'
                )

        # 5. Database Connection Pool Metrics (if engine provided)
        if db_engine is not None and hasattr(db_engine, "pool"):
            pool = db_engine.pool
            lines.append("# HELP postgres_pool_size Configured database connection pool size.")
            lines.append("# TYPE postgres_pool_size gauge")
            lines.append(f"postgres_pool_size {pool.size()}")

            lines.append("# HELP postgres_pool_checkedin_connections Database connections idle in pool.")
            lines.append("# TYPE postgres_pool_checkedin_connections gauge")
            lines.append(f"postgres_pool_checkedin_connections {pool.checkedin()}")

            lines.append("# HELP postgres_pool_checkedout_connections Database connections currently in use.")
            lines.append("# TYPE postgres_pool_checkedout_connections gauge")
            lines.append(f"postgres_pool_checkedout_connections {pool.checkedout()}")

            lines.append("# HELP postgres_pool_overflow_connections Connections opened above configured pool size.")
            lines.append("# TYPE postgres_pool_overflow_connections gauge")
            lines.append(f"postgres_pool_overflow_connections {pool.overflow()}")

        # 6. Redis Telemetry Metrics (if redis_service provided)
        if redis_service is not None:
            lines.append("# HELP redis_up Redis health and availability status (1 = up, 0 = degraded/down).")
            lines.append("# TYPE redis_up gauge")
            redis_client = getattr(redis_service, "_client", None)
            ping_ok = False
            if redis_client is not None:
                try:
                    ping_ok = await redis_service.ping()
                except Exception:
                    ping_ok = False

            lines.append(f"redis_up {1 if ping_ok else 0}")
            if ping_ok and redis_client is not None:
                try:
                    info_mem = await redis_client.info("memory")
                    info_stats = await redis_client.info("stats")
                    info_clients = await redis_client.info("clients")
                    info_keyspace = await redis_client.info("keyspace")

                    lines.append("# HELP redis_used_memory_bytes Memory allocated by Redis in bytes.")
                    lines.append("# TYPE redis_used_memory_bytes gauge")
                    lines.append(f"redis_used_memory_bytes {info_mem.get('used_memory', 0)}")

                    lines.append("# HELP redis_connected_clients Number of client connections to Redis.")
                    lines.append("# TYPE redis_connected_clients gauge")
                    lines.append(f"redis_connected_clients {info_clients.get('connected_clients', 0)}")

                    lines.append("# HELP redis_evicted_keys_total Total number of keys evicted due to maxmemory limit.")
                    lines.append("# TYPE redis_evicted_keys_total counter")
                    lines.append(f"redis_evicted_keys_total {info_stats.get('evicted_keys', 0)}")

                    # Total keys across DB 0
                    db0 = info_keyspace.get("db0", {})
                    total_keys = db0.get("keys", 0) if isinstance(db0, dict) else 0
                    lines.append("# HELP redis_db_keys Total number of keys stored in DB 0.")
                    lines.append("# TYPE redis_db_keys gauge")
                    lines.append(f"redis_db_keys {total_keys}")
                except Exception:
                    pass

        lines.append("")  # Prometheus requires trailing newline
        return "\n".join(lines)


# Singleton metrics registry
metrics = MetricsRegistry()
