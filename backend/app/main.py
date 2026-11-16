"""FastAPI application entry point and lifespan lifecycle manager.

Following architectural rules:
- Asynchronous lifespan management for engine and pool disposal.
- Routers mounted under /api and /health.
- Generic, structured error handling without leaking secrets or raw traces.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.logging_config import setup_logging
from app.database.connection import close_async_engine
from app.middleware.correlation import RequestCorrelationMiddleware
from app.routers import dashboard, health, metrics, products
from app.services.redis_service import close_redis_client

settings = get_settings()

# Initialize structured logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    structured_json=(settings.ENVIRONMENT == "production"),
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    # Startup actions
    yield
    # Shutdown actions: cleanly close database and Redis connection pools
    await close_async_engine()
    await close_redis_client()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="SaaS Product Management platform with PostgreSQL source-of-truth and Redis 8 caching.",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount application routers
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(products.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# Add middleware (RequestCorrelationMiddleware outermost to capture full request lifecycle)
app.add_middleware(RequestCorrelationMiddleware)
