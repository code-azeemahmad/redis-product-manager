"""Application dependencies for FastAPI route handlers."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_session_factory
from app.services.redis_service import RedisService, get_redis_client


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a request-scoped AsyncSession dependency.

    Ensures proper rollback on error and resource cleanup.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_redis_service() -> RedisService:
    """Provide the application Redis service dependency."""
    return RedisService(get_redis_client())
