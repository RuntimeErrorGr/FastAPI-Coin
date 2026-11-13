import pytest

from app.repositories.coin_repository import CoinRepository
from tests.coins import COINS


@pytest.fixture
def repository(db_session):
    return CoinRepository(db_session)


@pytest.mark.parametrize("coin", COINS.values(), ids=list(COINS))
async def test_get_by_symbol_returns_seeded_coin(repository, coin):
    assert await repository.get_by_symbol(coin.symbol) == coin


async def test_get_by_symbol_returns_none_for_unknown_coin(repository):
    assert await repository.get_by_symbol("doge") is None
