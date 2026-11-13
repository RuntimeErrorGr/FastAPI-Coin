from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import exchange_router
from app.config import settings
from app.db.session import engine
from app.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Closes the database connection pool when the app shuts down."""
    yield
    await engine.dispose()


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
