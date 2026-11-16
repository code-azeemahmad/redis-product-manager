"""Integration tests for Nginx reverse proxy, static SPA hosting, and API routing.

Following architectural rules:
- Verify Nginx serves the React SPA static assets at root (/).
- Verify client-side SPA routes (/products/:id, /dashboard) fall back to index.html (200 OK).
- Verify Nginx correctly proxies /api/products, /api/dashboard/stats, and /health/ready to FastAPI backend.
- Verify security headers (X-Frame-Options, X-Content-Type-Options) are enforced by Nginx.
"""

import os
import httpx
import pytest

# When running inside backend container on gateway-net, nginx is reachable at http://nginx
NGINX_HOST = os.getenv("NGINX_HOST", "nginx")
NGINX_BASE_URL = f"http://{NGINX_HOST}:80"


@pytest.mark.asyncio
async def test_nginx_serves_spa_index():
    """Nginx serves the React single-page application index.html with security headers."""
    async with httpx.AsyncClient(base_url=NGINX_BASE_URL, timeout=5.0) as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "<div id=\"root\"></div>" in resp.text
        assert "<title>SaaS Product Manager</title>" in resp.text

        # Verify Nginx security headers
        assert resp.headers.get("x-frame-options") == "SAMEORIGIN"
        assert resp.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
async def test_nginx_spa_client_route_fallback():
    """Client-side routes (/products/1, /dashboard) return index.html via try_files."""
    async with httpx.AsyncClient(base_url=NGINX_BASE_URL, timeout=5.0) as client:
        # 1. Product detail route
        resp_detail = await client.get("/products/999")
        assert resp_detail.status_code == 200
        assert "text/html" in resp_detail.headers["content-type"]
        assert "<div id=\"root\"></div>" in resp_detail.text

        # 2. Dashboard route
        resp_dash = await client.get("/dashboard")
        assert resp_dash.status_code == 200
        assert "text/html" in resp_dash.headers["content-type"]
        assert "<div id=\"root\"></div>" in resp_dash.text


@pytest.mark.asyncio
async def test_nginx_proxies_api_products():
    """Nginx reverse-proxies /api/products to backend and returns valid JSON catalogue."""
    async with httpx.AsyncClient(base_url=NGINX_BASE_URL, timeout=5.0) as client:
        resp = await client.get("/api/products")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]

        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data


@pytest.mark.asyncio
async def test_nginx_proxies_dashboard_stats():
    """Nginx reverse-proxies /api/dashboard/stats to backend."""
    async with httpx.AsyncClient(base_url=NGINX_BASE_URL, timeout=5.0) as client:
        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]

        data = resp.json()
        assert "total_products" in data
        assert "total_inventory_value" in data
        assert "average_product_price" in data
        assert "products_by_category" in data


@pytest.mark.asyncio
async def test_nginx_proxies_health_ready():
    """Nginx reverse-proxies /health/ready to backend."""
    async with httpx.AsyncClient(base_url=NGINX_BASE_URL, timeout=5.0) as client:
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert "dependencies" in data
