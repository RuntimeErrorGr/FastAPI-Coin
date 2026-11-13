import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import get_db_session
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Builds the schema once per test run by applying every migration."""
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")
    yield
    command.downgrade(alembic_config, "base")


@pytest.fixture
async def db_session():
    """A session whose changes are rolled back after each test.

    The outer transaction is never committed; anything the code under test
    commits only releases a SAVEPOINT inside it.
    """
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        yield session
        await session.close()
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
def overrides(overrides, db_session):
    return {**overrides, get_db_session: lambda: db_session}


@pytest.fixture
async def async_client(override_dependencies):
    """HTTP client that runs the app in the test event loop."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
