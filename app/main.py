from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import exchange_router
from app.config import settings
from app.db.session import create_engine, create_session_factory
from app.handlers import register_exception_handlers
from app.services.cache_service import create_redis_client
from app.services.coingecko_service import create_http_client


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Creates the objects shared by all requests on startup, closes them on shutdown."""
    db_engine = create_engine()
    application.state.session_factory = create_session_factory(db_engine)
    application.state.redis_client = create_redis_client()
    application.state.http_client = create_http_client()

    yield

    await application.state.http_client.aclose()
    await application.state.redis_client.aclose()
    await db_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Coin API!"}


app.include_router(exchange_router.router, tags=["exchange"])

register_exception_handlers(app)
