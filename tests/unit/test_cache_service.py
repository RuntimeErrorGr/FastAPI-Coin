import redis.asyncio as redis

from app.config import settings
from tests.coins import BTC, COINS, ETH


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


async def test_get_coins_returns_cached_list(cache_service, redis_client):
    coins = list(COINS.values())
    redis_client.get.return_value = (
        '[{"symbol": "btc", "coingecko_id": "bitcoin", "name": "Bitcoin"},'
        ' {"symbol": "eth", "coingecko_id": "ethereum", "name": "Ethereum"},'
        ' {"symbol": "xrp", "coingecko_id": "ripple", "name": "XRP"}]'
    )

    assert await cache_service.get_coins() == coins
    redis_client.get.assert_awaited_once_with("coins")


async def test_get_coins_returns_none_on_miss(cache_service, redis_client):
    redis_client.get.return_value = None

    assert await cache_service.get_coins() is None


async def test_set_coins_round_trips_through_get_coins(cache_service, redis_client):
    coins = list(COINS.values())

    await cache_service.set_coins(coins)
    key, ttl, value = redis_client.setex.await_args.args
    redis_client.get.return_value = value

    assert (key, ttl) == ("coins", settings.REDIS_CACHE_EXPIRE)
    assert await cache_service.get_coins() == coins
