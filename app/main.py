from fastapi import FastAPI

from app.api import exchange_router
from app.config import settings
from app.handlers import register_exception_handlers

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Coin API!"}


app.include_router(exchange_router.router, tags=["exchange"])

register_exception_handlers(app)
