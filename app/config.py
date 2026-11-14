from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class EnvType(str, Enum):
    """Supported environment."""

    DEV = "dev"
    TEST = "test"


class Settings(BaseSettings):
    """Application settings. Loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str
    API_VERSION: str
    LOG_DIR: str = "logs"
    ENV: EnvType = EnvType.DEV

    WEBSERVER_HOST: str = "0.0.0.0"
    WEBSERVER_PORT: int = 8000

    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_CACHE_EXPIRE: int = 120
    REDIS_PASSWORD: str

    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    EXTERNAL_API_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXTERNAL_API_TIMEOUT: int = 5

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> URL:
        """SQLAlchemy URL for the async Postgres driver, built from POSTGRES_*."""
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )


settings = Settings()
