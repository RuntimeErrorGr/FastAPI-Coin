import pytest
import redis.asyncio as redis

from app.config import settings
from app.schemas.coin import CoinType


class TestCacheService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "redis_value, expected",
        [
            # cache hit
            ("123.45", 123.45),
            # cache miss
            (None, None),
        ],
    )
    async def test_get_rate(
        self, cache_service, mock_redis_client, redis_value, expected
    ):
        mock_redis_client.get.return_value = redis_value

        rate = await cache_service.get_rate(CoinType.BTC)
        assert rate == expected
        mock_redis_client.get.assert_awaited_once_with("rate:btc")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "coin, value, side_effect",
        [
            (CoinType.ETH, 987.65, None),
            # BUG: redis timeout
            (CoinType.BTC, 123.45, redis.TimeoutError()),
        ],
    )
    async def test_set_rate(
        self,
        cache_service,
        mock_redis_client,
        coin,
        value,
        side_effect,
    ):
        mock_redis_client.setex.side_effect = side_effect

        await cache_service.set_rate(coin, value)
        mock_redis_client.setex.assert_awaited_once_with(
            f"rate:{coin.value.lower()}",
            settings.REDIS_CACHE_EXPIRE,
            str(value),
        )

        mock_redis_client.setex.reset_mock()

    @pytest.mark.asyncio
    async def test_get_rate_redis_connection_error(
        self, cache_service, mock_redis_client
    ):
        mock_redis_client.get.side_effect = redis.ConnectionError()

        rate = await cache_service.get_rate(CoinType.BTC)
        assert rate is None
