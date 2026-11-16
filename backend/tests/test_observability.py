"""Integration tests for observability, correlation IDs, health reporting, and Prometheus metrics.

Following architectural rules:
- Verify X-Request-ID propagation across requests.
- Verify /health/ready reports latency and dependency status.
- Verify /metrics returns Prometheus exposition format with bounded-cardinality labels.
- Verify database connection pool and Redis memory/keys metrics are present.
"""

import uuid
import pytest
from httpx import AsyncClient

from app.core.metrics import metrics


@pytest.mark.asyncio
async def test_request_id_generated_when_missing(client: AsyncClient):
    """When X-Request-ID is not provided, the middleware generates one."""
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) >= 16


@pytest.mark.asyncio
async def test_request_id_propagated_when_provided(client: AsyncClient):
    """When X-Request-ID is provided by caller, the same ID is reflected in response headers."""
    custom_id = f"test-corr-{uuid.uuid4().hex[:8]}"
    resp = await client.get("/health/live", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_id


@pytest.mark.asyncio
async def test_health_ready_detailed_reporting(client: AsyncClient):
    """Verify /health/ready reports dependency status, latencies, and timestamp."""
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "ready"
    assert "timestamp" in data
    assert data["dependencies"]["postgres"] == "healthy"
    assert data["dependencies"]["redis"] == "healthy"

    assert "latency_ms" in data
    assert isinstance(data["latency_ms"]["postgres"], (int, float))
    assert data["latency_ms"]["postgres"] >= 0.0
    assert isinstance(data["latency_ms"]["redis"], (int, float))
    assert data["latency_ms"]["redis"] >= 0.0


@pytest.mark.asyncio
async def test_metrics_endpoint_prometheus_format(client: AsyncClient):
    """Verify /metrics returns standard Prometheus text format with bounded labels."""
    # Execute a request to generate metrics
    await client.get("/health/live")

    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    text = resp.text

    # 1. Prometheus header declarations
    assert "# HELP http_requests_total" in text
    assert "# TYPE http_requests_total counter"
    assert "# HELP http_request_duration_seconds" in text
    assert "# HELP cache_events_total" in text
    assert "# HELP rate_limit_events_total" in text

    # 2. Database and Redis gauges
    assert "# HELP postgres_pool_size" in text
    assert "postgres_pool_size" in text
    assert "postgres_pool_checkedin_connections" in text
    assert "redis_up 1" in text
    assert "redis_used_memory_bytes" in text
    assert "redis_db_keys" in text

    # 3. HTTP request metrics with bounded route template
    assert 'route="/health/live"' in text
    assert 'method="GET"' in text
    assert 'status="200"' in text


@pytest.mark.asyncio
async def test_metrics_bounded_cardinality_route_templates(client: AsyncClient):
    """Verify that route templates rather than raw IDs appear in Prometheus labels."""
    # Create product to get a specific ID
    post_resp = await client.post(
        "/api/products",
        json={"name": "Cardinality Test", "price": "19.99", "category": "Testing", "stock": 5},
    )
    assert post_resp.status_code == 201
    prod_id = post_resp.json()["id"]

    # Fetch product by ID
    get_resp = await client.get(f"/api/products/{prod_id}")
    assert get_resp.status_code == 200

    # Fetch metrics
    metrics_resp = await client.get("/metrics")
    metrics_text = metrics_resp.text

    # The metric label must use the FastAPI route template /api/products/{product_id}
    # and NOT the raw integer ID /api/products/123
    assert 'route="/api/products/{product_id}"' in metrics_text
    assert f'route="/api/products/{prod_id}"' not in metrics_text
