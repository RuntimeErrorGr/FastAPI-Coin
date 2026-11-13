import pytest

from app.api.dependencies import get_exchange_rate, validate_exchange_params
from app.exceptions import (
    InvalidCoinException,
    OutOfBoundsAmountException,
    RateLimitException,
)
from app.schemas.exchange import ExchangeQueryParams
from tests.coins import BTC, COINS

QUERY = ExchangeQueryParams(coin=BTC, amount=1.0)


@pytest.mark.parametrize("coin, amount", [("btc", 1.0), ("ETH", 10.5), ("Xrp", 9999.0)])
async def test_validate_accepts_supported_coin_in_any_case(
    coin_repository, coin, amount
):
    query = await validate_exchange_params(
        coin=coin, amount=amount, supported_coins=coin_repository
    )

    assert query == ExchangeQueryParams(coin=COINS[coin.lower()], amount=amount)


async def test_validate_rejects_unsupported_coin(coin_repository):
    with pytest.raises(InvalidCoinException):
        await validate_exchange_params(
            coin="doge", amount=1.0, supported_coins=coin_repository
        )


@pytest.mark.parametrize("amount", [0, -1, 10000])
async def test_validate_rejects_out_of_bounds_amount(coin_repository, amount):
    with pytest.raises(OutOfBoundsAmountException):
        await validate_exchange_params(
            coin="btc", amount=amount, supported_coins=coin_repository
        )


async def test_rate_comes_from_cache_when_present(cache, coingecko, failover):
    cache.get_rate.return_value = 20000.0

    rate = await get_exchange_rate(
        query=QUERY, api=coingecko, cache=cache, failover=failover
    )

    assert rate == 20000.0
    coingecko.get_rate.assert_not_awaited()


async def test_rate_is_fetched_and_cached_on_miss(cache, coingecko, failover):
    coingecko.get_rate.return_value = 3000.0

    rate = await get_exchange_rate(
        query=QUERY, api=coingecko, cache=cache, failover=failover
    )

    assert rate == 3000.0
    coingecko.get_rate.assert_awaited_once_with(BTC)
    cache.set_rate.assert_awaited_once_with(BTC, 3000.0)
    assert failover.should_block_request(BTC) is True


async def test_rate_is_fetched_when_cache_is_down(cache, coingecko, failover):
    cache.is_up = False
    coingecko.get_rate.return_value = 3000.0

    rate = await get_exchange_rate(
        query=QUERY, api=coingecko, cache=cache, failover=failover
    )

    assert rate == 3000.0


async def test_rate_is_blocked_when_cache_is_down_and_coin_was_fetched_recently(
    cache, coingecko, failover
):
    cache.is_up = False
    failover.record_call(BTC)

    with pytest.raises(RateLimitException) as exc_info:
        await get_exchange_rate(
            query=QUERY, api=coingecko, cache=cache, failover=failover
        )

    assert exc_info.value.retry_after > 0
    coingecko.get_rate.assert_not_awaited()
