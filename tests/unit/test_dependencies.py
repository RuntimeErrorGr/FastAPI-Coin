import pytest

from app.api.dependencies import (
    InvalidCoinException,
    OutOfBoundsAmountException,
    validate_exchange_params,
)
from app.schemas.coin import CoinType


class TestDependencies:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "coin, amount, should_pass",
        [
            ("btc", 1.0, True),
            ("ETH", 10.5, True),
            ("Xrp", 9999.0, True),
            ("doge", 1.0, False),
            ("btC", 0, False),
            ("eth", -1, False),
            ("XRP", 10000, False),
            (None, None, False),
            ("", "", False),
        ],
    )
    async def test_validate_exchange_params(self, coin, amount, should_pass):
        if should_pass:
            result = await validate_exchange_params(coin=coin, amount=amount)
            assert result.coin == CoinType(coin.lower())
            assert result.amount == amount
        else:
            with pytest.raises((InvalidCoinException, OutOfBoundsAmountException)):
                await validate_exchange_params(coin=coin, amount=amount)
