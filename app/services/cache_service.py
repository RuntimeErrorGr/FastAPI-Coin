import redis.asyncio as redis
from pydantic import TypeAdapter

from app.config import settings
from app.exceptions import CacheConnectionException
from app.log import get_logger
from app.schemas.coin import CoinRead

logger = get_logger(__name__)

COINS_KEY = "coins"
COIN_LIST = TypeAdapter(list[CoinRead])


def create_redis_client() -> redis.Redis:
    """Creates the Redis connection pool. Called once, on app startup."""
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


class CacheService:
    """Service to interact with the Redis cache."""

    def __init__(self, client: redis.Redis):
        self.client = client
        self._is_up = True

    @property
    def is_up(self) -> bool:
        """Keeps track of the latest connection status to Redis."""
        return self._is_up

    async def get_rate(self, coin: CoinRead) -> float | None:
        value = await self._get(f"rate:{coin.symbol}")
        return float(value) if value is not None else None

    async def set_rate(self, coin: CoinRead, rate: float) -> None:
        await self._set(f"rate:{coin.symbol}", str(rate), settings.REDIS_CACHE_EXPIRE)

    async def get_coins(self) -> list[CoinRead] | None:
        value = await self._get(COINS_KEY)
        return COIN_LIST.validate_json(value) if value is not None else None

    async def set_coins(self, coins: list[CoinRead]) -> None:
        value = COIN_LIST.dump_json(coins).decode()
        await self._set(COINS_KEY, value, settings.REDIS_CACHE_EXPIRE)

    async def _get(self, key: str) -> str | None:
        try:
            value = await self._exec(self.client.get, key)
        except CacheConnectionException as e:
            logger.error(f"Cache read failed for {key}: {e}")
            return None

        logger.debug(f"Cache {'hit' if value is not None else 'miss'} for {key}")
        return value

    async def _set(self, key: str, value: str, ttl: int) -> None:
        try:
            await self._exec(self.client.setex, key, ttl, value)
        except CacheConnectionException as e:
            logger.error(f"Cache write failed for {key}: {e}")
            return

        logger.debug(f"Cache updated for {key}")

    async def _exec(self, func, *args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            self._is_up = True
            return result
        except redis.RedisError as e:
            self._is_up = False
            raise CacheConnectionException("Failed to connect to Redis cache.") from e
