import uvicorn

from app.config import EnvType, settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.WEBSERVER_HOST,
        port=settings.WEBSERVER_PORT,
        reload=settings.ENV == EnvType.DEV,
        log_level="debug" if settings.ENV == EnvType.DEV else None,
    )
