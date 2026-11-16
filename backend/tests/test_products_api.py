"""Integration tests for Product API endpoints and PostgreSQL persistence."""

from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient):
    # Liveness check
    live_resp = await client.get("/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json() == {"status": "alive"}

    # Readiness check (PostgreSQL connectivity)
    ready_resp = await client.get("/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"
    assert ready_resp.json()["dependencies"]["postgres"] == "healthy"


@pytest.mark.asyncio
async def test_create_product_success(client: AsyncClient):
    payload = {
        "name": "Wireless Mouse",
        "price": "49.99",
        "category": "Electronics",
        "stock": 100,
    }
    response = await client.post("/api/products", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Wireless Mouse"
    assert data["price"] == "49.99"
    assert data["category"] == "Electronics"
    assert data["stock"] == 100
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_product_float_rejected(client: AsyncClient):
    # Float prices must be strictly rejected per architectural invariant
    payload = {
        "name": "Invalid Float Item",
        "price": 19.99,  # Float instead of string/decimal
        "category": "Test",
        "stock": 10,
    }
    response = await client.post("/api/products", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_negative_values_rejected(client: AsyncClient):
    # Negative price
    response = await client.post(
        "/api/products",
        json={"name": "Bad Price", "price": "-5.00", "category": "Test", "stock": 10},
    )
    assert response.status_code == 422

    # Negative stock
    response = await client.post(
        "/api/products",
        json={"name": "Bad Stock", "price": "10.00", "category": "Test", "stock": -1},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_product_by_id(client: AsyncClient):
    # Create
    create_resp = await client.post(
        "/api/products",
        json={"name": "USB Cable", "price": "9.99", "category": "Accessories", "stock": 50},
    )
    product_id = create_resp.json()["id"]

    # Fetch
    get_resp = await client.get(f"/api/products/{product_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == product_id
    assert get_resp.json()["name"] == "USB Cable"

    # Non-existent ID
    not_found_resp = await client.get("/api/products/999999")
    assert not_found_resp.status_code == 404


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient):
    # Create
    create_resp = await client.post(
        "/api/products",
        json={"name": "Old Monitor", "price": "150.00", "category": "Electronics", "stock": 5},
    )
    product_id = create_resp.json()["id"]

    # Update
    update_resp = await client.put(
        f"/api/products/{product_id}",
        json={"name": "New 4K Monitor", "price": "299.99", "category": "Electronics", "stock": 12},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "New 4K Monitor"
    assert update_resp.json()["price"] == "299.99"
    assert update_resp.json()["stock"] == 12

    # Non-existent ID update
    nf_resp = await client.put(
        "/api/products/999999",
        json={"name": "Ghost", "price": "1.00", "category": "Ghost", "stock": 0},
    )
    assert nf_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient):
    # Create
    create_resp = await client.post(
        "/api/products",
        json={"name": "To Delete", "price": "1.00", "category": "Trash", "stock": 1},
    )
    product_id = create_resp.json()["id"]

    # Delete
    del_resp = await client.delete(f"/api/products/{product_id}")
    assert del_resp.status_code == 204

    # Verify 404 on subsequent get and delete
    assert (await client.get(f"/api/products/{product_id}")).status_code == 404
    assert (await client.delete(f"/api/products/{product_id}")).status_code == 404


@pytest.mark.asyncio
async def test_list_products_pagination_and_filter(client: AsyncClient):
    import uuid
    # Seed specific items with unique category for filtering and pagination
    cat = f"Books_{uuid.uuid4().hex[:8]}"
    for i in range(1, 6):
        await client.post(
            "/api/products",
            json={"name": f"Book {i}", "price": f"{i*10}.00", "category": cat, "stock": i},
            headers={"X-Forwarded-For": f"198.51.100.{i}"},
        )

    # Filter by category
    resp = await client.get(f"/api/products?category={cat}&page=1&limit=2&sort_by=price&sort_order=asc")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["pages"] == 3
    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Book 1"
    assert data["items"][1]["name"] == "Book 2"

    # Next page
    resp_p2 = await client.get(f"/api/products?category={cat}&page=2&limit=2&sort_by=price&sort_order=asc")
    data_p2 = resp_p2.json()
    assert data_p2["page"] == 2
    assert data_p2["items"][0]["name"] == "Book 3"
    assert data_p2["items"][1]["name"] == "Book 4"

    # Descending sort
    resp_desc = await client.get(f"/api/products?category={cat}&page=1&limit=2&sort_by=price&sort_order=desc")
    data_desc = resp_desc.json()
    assert data_desc["items"][0]["name"] == "Book 5"
    assert data_desc["items"][1]["name"] == "Book 4"
