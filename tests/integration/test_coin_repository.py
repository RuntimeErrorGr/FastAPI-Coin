import pytest

from app.repositories.coin_repository import CoinRepository
from app.schemas.coin import CoinRead
from tests.coins import COINS


@pytest.fixture
def repository(session_factory, cache):
    return CoinRepository(session_factory, cache)


@pytest.mark.parametrize("coin", COINS.values(), ids=list(COINS))
async def test_get_by_symbol_returns_seeded_coin(repository, coin):
    assert await repository.get_by_symbol(coin.symbol) == coin


async def test_get_by_symbol_returns_none_for_unknown_coin(repository):
    assert await repository.get_by_symbol("doge") is None


async def test_coins_are_loaded_from_database_and_cached_on_miss(repository, cache):
    coins = await repository.get_all()

    assert set(coins) == set(COINS.values())
    cache.set_coins.assert_awaited_once_with(coins)


async def test_coins_come_from_cache_without_querying_database(repository, cache):
    doge = CoinRead(symbol="doge", coingecko_id="dogecoin", name="Dogecoin")
    cache.get_coins.return_value = [doge]

    assert await repository.get_by_symbol("doge") == doge
    assert await repository.get_by_symbol("btc") is None
    cache.set_coins.assert_not_awaited()
