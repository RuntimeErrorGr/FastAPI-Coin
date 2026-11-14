import pytest
import redis.asyncio as redis
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.api.dependencies import (
    get_cache_service,
    get_coingecko_service,
    get_failover_service,
)
from app.config import settings
from app.db.session import create_session_factory, get_db_session
from app.main import app
from app.services.cache_service import CacheService, create_redis_client
from tests.users import ALICE, BOB


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
        factory = create_session_factory(connection)
        factory.configure(join_transaction_mode="create_savepoint")
        yield factory
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def db_session(session_factory):
    """The request-scoped session the app uses, inside the test transaction."""
    async with session_factory() as session:
        yield session


@pytest.fixture
async def redis_client():
    """A client for the test Redis instance."""
    client = create_redis_client()
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
def cache(redis_client):
    return CacheService(redis_client)


@pytest.fixture
async def redis_down(cache):
    """Makes Redis unreachable by pointing the cache at a port nothing listens on."""
    unreachable_client = redis.Redis(host="localhost", port=1)
    cache.client = unreachable_client
    yield
    await unreachable_client.aclose()


@pytest.fixture
async def http_client(db_session, cache, coingecko, failover):
    """HTTP client that calls the app in-process on the test's event loop."""
    app.dependency_overrides = {
        get_db_session: lambda: db_session,
        get_cache_service: lambda: cache,
        get_coingecko_service: lambda: coingecko,
        get_failover_service: lambda: failover,
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def alice(http_client):
    """Signs Alice up and returns her account as the API returned it."""
    response = await http_client.post("/users", json=ALICE)
    return response.json()


@pytest.fixture
async def alice_headers(http_client, alice):
    """Logs Alice in and returns the Authorization header for her requests."""
    form = {"username": ALICE["username"], "password": ALICE["password"]}
    response = await http_client.post("/auth/token", data=form)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def auth_client(http_client, alice_headers):
    """The HTTP client, logged in as Alice: every request carries her token."""
    http_client.headers.update(alice_headers)
    return http_client


@pytest.fixture
async def bob_headers(http_client):
    """Signs Bob up, logs him in and returns the Authorization header for him."""
    await http_client.post("/users", json=BOB)
    form = {"username": BOB["username"], "password": BOB["password"]}
    response = await http_client.post("/auth/token", data=form)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
