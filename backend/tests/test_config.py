"""Unit tests for application configuration and settings validation."""

import pytest
from app.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.APP_NAME == "redis-product-manager"
    assert settings.ENVIRONMENT == "development"
    assert settings.POSTGRES_PORT == 5432
    assert settings.REDIS_PORT == 6379
    assert settings.CACHE_PRODUCT_DETAIL_TTL == 300
    assert settings.CACHE_PRODUCT_LIST_TTL == 120
    assert settings.CACHE_DASHBOARD_STATS_TTL == 120


def test_database_url_generation():
    settings = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_HOST="dbhost",
        POSTGRES_PORT=5433,
        POSTGRES_DB="testdb",
    )
    expected = "postgresql+asyncpg://testuser:testpassword@dbhost:5433/testdb"
    assert settings.async_database_url == expected


def test_redis_url_generation():
    settings = Settings(
        REDIS_USER="app",
        REDIS_PASSWORD="secretpassword",
        REDIS_HOST="redishost",
        REDIS_PORT=6380,
    )
    expected = "redis://app:secretpassword@redishost:6380/0"
    assert settings.async_redis_url == expected


def test_repr_masks_secrets():
    settings = Settings(
        POSTGRES_PASSWORD="supersecretpostgres",
        REDIS_PASSWORD="supersecretredis",
    )
    repr_str = repr(settings)
    assert "supersecretpostgres" not in repr_str
    assert "supersecretredis" not in repr_str
    assert "redis-product-manager" in repr_str or "Settings(" in repr_str


def test_proxy_and_cors_lists():
    settings = Settings(
        TRUSTED_PROXY_IPS="10.0.0.1, 192.168.1.1",
        CORS_ORIGINS="http://localhost:3000, https://myapp.example.com",
    )
    assert settings.trusted_proxies_list == ["10.0.0.1", "192.168.1.1"]
    assert settings.cors_origins_list == ["http://localhost:3000", "https://myapp.example.com"]
