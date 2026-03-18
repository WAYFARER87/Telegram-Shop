"""Pytest configuration."""

import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


TEST_DB_PATH = Path("/tmp/fastapi_aiogram_test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["BASE_URL"] = "http://testserver"

from app.api.dependencies import get_redis, get_session  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import create_app  # noqa: E402


class FakeRedis:
    """Minimal async Redis stub for tests."""

    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> bool:
        if nx and key in self.storage:
            return False
        self.storage[key] = value
        return True

    async def close(self) -> None:
        return None


@pytest_asyncio.fixture()
async def session_factory() -> AsyncGenerator[async_sessionmaker, None]:
    """Create isolated DB session factory."""

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()


@pytest_asyncio.fixture()
async def client(session_factory: async_sessionmaker) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with dependency overrides."""

    app = create_app()
    fake_redis = FakeRedis()

    async def override_session() -> AsyncGenerator:
        async with session_factory() as session:
            yield session

    def override_redis() -> FakeRedis:
        return fake_redis

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_redis] = override_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
