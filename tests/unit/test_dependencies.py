import pytest

from app.api.dependencies import validate_exchange_params
from app.exceptions import InvalidCoinException, OutOfBoundsAmountException
from tests.coins import COINS


class TestDependencies:
    @pytest.mark.parametrize(
        "coin, amount",
        [
            ("btc", 1.0),
            ("ETH", 10.5),
            ("Xrp", 9999.0),
        ],
    )
    async def test_validate_exchange_params_valid(
        self, fake_coin_repository, coin, amount
    ):
        result = await validate_exchange_params(
            coin=coin, amount=amount, supported_coins=fake_coin_repository
        )
        assert result.coin == COINS[coin.lower()]
        assert result.amount == amount
        fake_coin_repository.get_by_symbol.assert_awaited_once_with(coin.lower())

    @pytest.mark.parametrize(
        "coin, amount, expected_exception",
        [
            ("doge", 1.0, InvalidCoinException),
            ("", 1.0, InvalidCoinException),
            ("btC", 0, OutOfBoundsAmountException),
            ("eth", -1, OutOfBoundsAmountException),
            ("XRP", 10000, OutOfBoundsAmountException),
        ],
    )
    async def test_validate_exchange_params_invalid(
        self, fake_coin_repository, coin, amount, expected_exception
    ):
        with pytest.raises(expected_exception):
            await validate_exchange_params(
                coin=coin, amount=amount, supported_coins=fake_coin_repository
            )
