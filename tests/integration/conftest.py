import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.api.dependencies import (
    get_cache_service,
    get_coin_repository,
    get_coingecko_service,
    get_failover_service,
)
from app.config import settings
from app.db.session import create_session_factory
from app.main import app
from app.repositories.coin_repository import CoinRepository


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Applies every migration once before the integration tests, reverts them after."""
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")


@pytest.fixture
async def session_factory():
    """Creates sessions that all run inside one transaction, rolled back after each test.

    Each test runs on its own event loop and asyncpg connections are tied to
    the loop that opened them, so every test opens its own connection.
    """
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        yield create_session_factory(connection)
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def http_client(session_factory, cache, coingecko, failover):
    """HTTP client that calls the app in-process on the test's event loop."""
    app.dependency_overrides = {
        get_coin_repository: lambda: CoinRepository(session_factory, cache),
        get_cache_service: lambda: cache,
        get_coingecko_service: lambda: coingecko,
        get_failover_service: lambda: failover,
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
