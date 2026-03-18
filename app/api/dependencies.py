"""FastAPI dependencies."""

from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session


async def get_session(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[AsyncSession, None]:
    """Provide DB session dependency."""

    yield session


def get_redis(request: Request) -> Redis:
    """Return app-scoped Redis client."""

    return request.app.state.redis
