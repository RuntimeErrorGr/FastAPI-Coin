from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


def create_engine() -> AsyncEngine:
    """Creates the database connection pool. Called once, on app startup."""
    return create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)


def create_session_factory(
    bind: AsyncEngine | AsyncConnection,
) -> async_sessionmaker[AsyncSession]:
    """Creates sessions with the settings shared by the app and the tests."""
    return async_sessionmaker(bind, expire_on_commit=False)
