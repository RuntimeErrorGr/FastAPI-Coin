import pytest

from app.api.dependencies import (
    InvalidCoinException,
    OutOfBoundsAmountException,
    validate_exchange_params,
)
from app.schemas.coin import CoinType


class TestDependencies:
    @pytest.mark.parametrize(
        "coin, amount",
        [
            ("btc", 1.0),
            ("ETH", 10.5),
            ("Xrp", 9999.0),
        ],
    )
    async def test_validate_exchange_params_valid(self, coin, amount):
        result = await validate_exchange_params(coin=coin, amount=amount)
        assert result.coin == CoinType(coin.lower())
        assert result.amount == amount

    @pytest.mark.parametrize(
        "coin, amount",
        [
            ("doge", 1.0),
            ("btC", 0),
            ("eth", -1),
            ("XRP", 10000),
            (None, None),
            ("", ""),
        ],
    )
    async def test_validate_exchange_params_invalid(self, coin, amount):
        with pytest.raises((InvalidCoinException, OutOfBoundsAmountException)):
            await validate_exchange_params(coin=coin, amount=amount)
