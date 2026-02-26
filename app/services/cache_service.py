import redis.asyncio as redis

from app.config import settings
from app.exceptions import CacheConnectionException, CacheMissException
from app.log import get_logger
from app.schemas.coin import CoinType

logger = get_logger(__name__)


class CacheService:
    """Service to interact with the Redis cache."""

    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        self._is_up = True

    @property
    def is_up(self) -> bool:
        """Keeps track of the latest connection status to Redis."""
        return self._is_up

    async def _exec(self, func, *args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            self._is_up = True
            return result
        except redis.RedisError as e:
            self._is_up = False
            raise CacheConnectionException("Failed to connect to Redis cache.") from e

    async def _get_rate(self, coin: CoinType) -> float:
        rate = await self._exec(self.client.get, f"rate:{coin.value}")
        if rate:
            logger.debug(f"Cache hit for {coin.value}: {rate}")
            return float(rate)

        raise CacheMissException(f"Coin not found in the cache: {coin.value}")

    async def _set_rate(self, coin: CoinType, rate: float) -> None:
        await self._exec(
            self.client.setex,
            f"rate:{coin.value}",
            settings.REDIS_CACHE_EXPIRE,
            str(rate),
        )
        logger.debug(f"Cache updated for {coin.value}: {rate}")

    async def set_rate(self, coin: CoinType, rate: float) -> None:
        """Attempts to update the exchange rate in the cache."""
        try:
            await self._set_rate(coin, rate)
        except CacheConnectionException as e:
            logger.error(f"Error updating cache for coin: {coin.value}: {e}")

    async def get_rate(self, coin: CoinType) -> float | None:
        """Attempts to get the exchange rate from the cache."""
        try:
            rate = await self._get_rate(coin)
            return rate
        except CacheMissException as e:
            logger.debug(f"Cache miss: {e}")
            return None
        except CacheConnectionException as e:
            logger.error(f"Cache connection error: {e}")
            return None
