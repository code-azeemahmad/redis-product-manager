"""Application configuration and validated settings using Pydantic Settings.

Following architectural rules:
- Configuration is loaded strictly from environment variables.
- Sensitive credentials (passwords, connection strings) are masked in string representations.
- All timeouts, pool sizes, and cache TTLs are explicitly bounded.
"""

from functools import lru_cache
from typing import List, Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --------------------------------------------------------------------------
    # Environment & Application
    # --------------------------------------------------------------------------
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    APP_NAME: str = "redis-product-manager"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = Field(default=8000, ge=1024, le=65535)

    # --------------------------------------------------------------------------
    # PostgreSQL Configuration (Authoritative Data Store)
    # --------------------------------------------------------------------------
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535)
    POSTGRES_DB: str = "saas_products"
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = Field(default="dev_postgres_password_change_me")

    POSTGRES_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    POSTGRES_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    POSTGRES_POOL_TIMEOUT: int = Field(default=30, ge=1, le=300)

    DATABASE_URL: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        """Construct or return the asyncpg PostgreSQL connection URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --------------------------------------------------------------------------
    # Redis 8 Configuration (Disposable Cache & Best-Effort Limiter)
    # --------------------------------------------------------------------------
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535)
    REDIS_USER: str = "app"
    REDIS_PASSWORD: str = Field(default="dev_redis_app_password_change_me")
    HEALTHCHECK_REDIS_PASSWORD: str = Field(default="dev_redis_healthcheck_password_change_me")

    REDIS_SOCKET_TIMEOUT: float = Field(default=2.0, ge=0.1, le=30.0)
    REDIS_CONNECT_TIMEOUT: float = Field(default=2.0, ge=0.1, le=30.0)
    REDIS_MAX_CONNECTIONS: int = Field(default=50, ge=1, le=500)

    REDIS_URL: Optional[str] = None

    @property
    def async_redis_url(self) -> str:
        """Construct or return the Redis connection URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        return (
            f"redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@"
            f"{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        )

    # --------------------------------------------------------------------------
    # Caching Policies & TTLs (in seconds)
    # --------------------------------------------------------------------------
    CACHE_KEY_PREFIX: str = "v1"
    CACHE_PRODUCT_DETAIL_TTL: int = Field(default=300, ge=1)
    CACHE_PRODUCT_LIST_TTL: int = Field(default=120, ge=1)
    CACHE_DASHBOARD_STATS_TTL: int = Field(default=120, ge=1)

    # --------------------------------------------------------------------------
    # Rate Limiting
    # --------------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_REQUESTS: int = Field(default=100, ge=1)
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = Field(default=60, ge=1)

    # --------------------------------------------------------------------------
    # Network, Proxy & Security
    # --------------------------------------------------------------------------
    TRUSTED_PROXY_IPS: str = "127.0.0.1,172.16.0.0/12,10.0.0.0/8"
    CORS_ORIGINS: str = "http://localhost,http://localhost:80,http://localhost:3000"

    @property
    def trusted_proxies_list(self) -> List[str]:
        return [p.strip() for p in self.TRUSTED_PROXY_IPS.split(",") if p.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def __repr__(self) -> str:
        """Safe representation without exposing secrets in logs."""
        return (
            f"Settings(ENVIRONMENT='{self.ENVIRONMENT}', "
            f"POSTGRES_HOST='{self.POSTGRES_HOST}:{self.POSTGRES_PORT}', "
            f"POSTGRES_DB='{self.POSTGRES_DB}', "
            f"REDIS_HOST='{self.REDIS_HOST}:{self.REDIS_PORT}', "
            f"REDIS_USER='{self.REDIS_USER}')"
        )


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton accessor for application settings."""
    return Settings()
