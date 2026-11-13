from unittest.mock import patch

import pytest

from tests.coins import BTC, ETH


class TestFailoverService:
    @pytest.mark.parametrize(
        "recorded_coin, check_coin, time_passed, expected_block",
        [
            # No previous call
            (None, BTC, 0, False),
            # Same coin, only 5s passed (blocked)
            (
                BTC,
                BTC,
                5,
                True,
            ),
            # Same coin, 70s passed (expired/not blocked)
            (
                BTC,
                BTC,
                70,
                False,
            ),
            # Different coin (not blocked)
            (BTC, ETH, 5, False),
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

    @pytest.mark.parametrize(
        "time_passed, expected",
        [
            (0, 60),
            (5, 55),
            (59.5, 1),
            (60, 0),
            (70, 0),
        ],
    )
    def test_retry_after(self, failover_service, time_passed, expected):
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000
            failover_service.record_call(BTC)

            mock_time.return_value = 1000 + time_passed
            assert failover_service.retry_after(BTC) == expected

    def test_retry_after_unknown_coin(self, failover_service):
        assert failover_service.retry_after(ETH) == 0
