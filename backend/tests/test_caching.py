"""Comprehensive tests for cache-aside read-through, generation invalidation, and error recovery."""

import json
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.cache.keys import (
    dashboard_stats_generation_key,
    dashboard_stats_key,
    product_detail_key,
    product_list_generation_key,
    product_list_key,
)
from app.services.redis_service import get_redis_client


@pytest.mark.asyncio
async def test_product_detail_cache_hit_and_invalidation(client: AsyncClient):
    redis_client = get_redis_client()

    # 1. Create product
    create_resp = await client.post(
        "/api/products",
        json={"name": "Gaming Headset", "price": "149.99", "category": "Audio", "stock": 10},
    )
    product_id = create_resp.json()["id"]
    detail_key = product_detail_key(product_id)

    # 2. First read: Miss, populates Redis
    get_resp1 = await client.get(f"/api/products/{product_id}")
    assert get_resp1.status_code == 200

    # Verify key was created in Redis with TTL <= 300
    cached_val = await redis_client.get(detail_key)
    assert cached_val is not None
    cached_json = json.loads(cached_val)
    assert cached_json["id"] == product_id
    assert cached_json["name"] == "Gaming Headset"
    assert cached_json["price"] == "149.99"
    ttl = await redis_client.ttl(detail_key)
    assert 0 < ttl <= 300

    # 3. Second read: Hits cache
    get_resp2 = await client.get(f"/api/products/{product_id}")
    assert get_resp2.status_code == 200
    assert get_resp2.json()["name"] == "Gaming Headset"

    # 4. Update: Must invalidate (delete) detail key
    update_resp = await client.put(
        f"/api/products/{product_id}",
        json={"name": "Gaming Headset V2", "price": "179.99", "category": "Audio", "stock": 15},
    )
    assert update_resp.status_code == 200

    # Verify key was deleted immediately post-commit
    assert await redis_client.get(detail_key) is None

    # 5. Read after update: Re-populates with updated data
    get_resp3 = await client.get(f"/api/products/{product_id}")
    assert get_resp3.status_code == 200
    assert get_resp3.json()["name"] == "Gaming Headset V2"
    assert get_resp3.json()["price"] == "179.99"

    # 6. Delete: Must delete detail key
    del_resp = await client.delete(f"/api/products/{product_id}")
    assert del_resp.status_code == 204
    assert await redis_client.get(detail_key) is None


@pytest.mark.asyncio
async def test_product_list_cache_and_generation_invalidation(client: AsyncClient):
    redis_client = get_redis_client()
    import uuid
    cat = f"ListCat_{uuid.uuid4().hex[:6]}"

    # Seed 2 products
    await client.post(
        "/api/products",
        json={"name": "Prod A", "price": "10.00", "category": cat, "stock": 5},
    )
    await client.post(
        "/api/products",
        json={"name": "Prod B", "price": "20.00", "category": cat, "stock": 5},
    )

    # First list read
    list_resp1 = await client.get(f"/api/products?category={cat}&page=1&limit=10")
    assert list_resp1.status_code == 200
    assert list_resp1.json()["total"] == 2

    # Check generation and verify cached list key exists in Redis
    list_gen_raw = await redis_client.get(product_list_generation_key())
    list_gen = int(list_gen_raw) if list_gen_raw else 1
    cache_key = product_list_key(
        generation=list_gen,
        category=cat,
        page=1,
        limit=10,
        sort_by="id",
        sort_order="asc",
    )
    cached_list = await redis_client.get(cache_key)
    assert cached_list is not None
    ttl = await redis_client.ttl(cache_key)
    assert 0 < ttl <= 120

    # Add a third product: list generation must advance
    await client.post(
        "/api/products",
        json={"name": "Prod C", "price": "30.00", "category": cat, "stock": 5},
    )

    new_gen_raw = await redis_client.get(product_list_generation_key())
    new_gen = int(new_gen_raw)
    assert new_gen > list_gen

    # List read after mutation: reflects updated data
    list_resp2 = await client.get(f"/api/products?category={cat}&page=1&limit=10")
    assert list_resp2.status_code == 200
    assert list_resp2.json()["total"] == 3


@pytest.mark.asyncio
async def test_dashboard_stats_calculation_and_caching(client: AsyncClient):
    redis_client = get_redis_client()

    # Read dashboard stats
    dash_resp1 = await client.get("/api/dashboard/stats")
    assert dash_resp1.status_code == 200
    data = dash_resp1.json()
    assert "total_products" in data
    assert "total_inventory_value" in data
    assert "average_product_price" in data
    assert "products_by_category" in data
    assert isinstance(data["total_inventory_value"], str)
    assert isinstance(data["average_product_price"], str)

    # Check dashboard cache key in Redis
    dash_gen_raw = await redis_client.get(dashboard_stats_generation_key())
    dash_gen = int(dash_gen_raw) if dash_gen_raw else 1
    d_key = dashboard_stats_key(dash_gen)
    assert await redis_client.get(d_key) is not None
    ttl = await redis_client.ttl(d_key)
    assert 0 < ttl <= 120

    # Second read: served from cache
    dash_resp2 = await client.get("/api/dashboard/stats")
    assert dash_resp2.status_code == 200
    assert dash_resp2.json() == data


@pytest.mark.asyncio
async def test_malformed_cache_payload_recovery(client: AsyncClient):
    redis_client = get_redis_client()

    # Create a product
    create_resp = await client.post(
        "/api/products",
        json={"name": "Resilient Item", "price": "55.00", "category": "Recovery", "stock": 8},
    )
    product_id = create_resp.json()["id"]
    detail_key = product_detail_key(product_id)

    # Corrupt the cache key with non-JSON junk
    await redis_client.set(detail_key, "{not-valid-json!!")

    # Read product: must not crash; must discard corrupt key, query DB, and repopulate valid cache
    get_resp = await client.get(f"/api/products/{product_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Resilient Item"

    # Verify corrupt key was deleted and repopulated with valid JSON
    new_cached = await redis_client.get(detail_key)
    assert new_cached is not None
    assert json.loads(new_cached)["name"] == "Resilient Item"
