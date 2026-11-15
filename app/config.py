from enum import Enum
from urllib.parse import quote

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

    CELERY_BROKER_DB: int = 1
    OUTBOX_DISPATCH_INTERVAL: float = 5.0
    EMAIL_RESEND_INTERVAL: float = 60.0
    EMAIL_RESEND_AFTER: int = 300

    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_STARTTLS: bool = False
    EMAIL_FROM: str = "Coin API <noreply@coinapi.local>"

    @property
    def CELERY_BROKER_URL(self) -> str:
        """Redis URL for Celery, on its own Redis database so it stays apart from the cache."""
        password = quote(self.REDIS_PASSWORD, safe="")
        return (
            f"redis://:{password}@{self.REDIS_HOST}:{self.REDIS_PORT}"
            f"/{self.CELERY_BROKER_DB}"
        )

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
