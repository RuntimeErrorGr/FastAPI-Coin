from unittest.mock import patch

import pytest

from app.schemas.coin import CoinType


class TestFailoverService:
    @pytest.mark.parametrize(
        "recorded_coin, check_coin, time_passed, expected_block",
        [
            # No previous call
            (None, CoinType.BTC, 0, False),
            # Same coin, only 5s passed (blocked)
            (
                CoinType.BTC,
                CoinType.BTC,
                5,
                True,
            ),
            # Same coin, 70s passed (expired/not blocked)
            (
                CoinType.BTC,
                CoinType.BTC,
                70,
                False,
            ),
            # Different coin (not blocked)
            (CoinType.BTC, CoinType.ETH, 5, False),
        ],
    )
    def test_should_block_request(
        self, failover_service, recorded_coin, check_coin, time_passed, expected_block
    ):
        start_time = 1000

        with patch("time.time") as mock_time:
            mock_time.return_value = start_time

            if recorded_coin:
                failover_service.record_call(recorded_coin)

            mock_time.return_value = start_time + time_passed

            result = failover_service.should_block_request(check_coin)
            assert result == expected_block
