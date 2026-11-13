import redis.asyncio as redis

from app.config import settings
from tests.coins import BTC, ETH


async def test_get_rate_returns_cached_value(cache_service, redis_client):
    redis_client.get.return_value = "123.45"

    rate = await cache_service.get_rate(BTC)

    assert rate == 123.45
    redis_client.get.assert_awaited_once_with("rate:btc")


async def test_get_rate_returns_none_on_miss(cache_service, redis_client):
    redis_client.get.return_value = None

    assert await cache_service.get_rate(BTC) is None


async def test_get_rate_returns_none_when_redis_is_unreachable(
    cache_service, redis_client
):
    redis_client.get.side_effect = redis.ConnectionError()

    assert await cache_service.get_rate(BTC) is None
    assert cache_service.is_up is False


async def test_set_rate_stores_value_with_expiry(cache_service, redis_client):
    await cache_service.set_rate(ETH, 987.65)

    redis_client.setex.assert_awaited_once_with(
        "rate:eth", settings.REDIS_CACHE_EXPIRE, "987.65"
    )


async def test_set_rate_ignores_redis_errors(cache_service, redis_client):
    redis_client.setex.side_effect = redis.TimeoutError()

    await cache_service.set_rate(ETH, 987.65)

    assert cache_service.is_up is False


async def test_is_up_recovers_after_successful_call(cache_service, redis_client):
    redis_client.get.side_effect = [redis.ConnectionError(), "1.0"]

    await cache_service.get_rate(BTC)
    assert cache_service.is_up is False

    await cache_service.get_rate(BTC)
    assert cache_service.is_up is True
