"""Database bootstrap helpers for tests/local runs."""

from app.db.base import Base
from app.db.session import engine


async def create_all() -> None:
    """Create all tables."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
