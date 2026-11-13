from unittest.mock import patch

import pytest

from app.config import settings
from tests.coins import BTC, ETH

TIMEOUT = settings.REDIS_CACHE_EXPIRE
NOW = 1_000_000.0


@pytest.fixture
def clock():
    """Controls what time.time() returns inside the test."""
    with patch("time.time") as clock:
        yield clock


def test_coin_never_fetched_is_not_blocked(failover):
    assert failover.should_block_request(BTC) is False
    assert failover.retry_after(BTC) == 0


@pytest.mark.parametrize(
    "elapsed, blocked",
    [(0, True), (TIMEOUT - 1, True), (TIMEOUT, False), (TIMEOUT + 60, False)],
)
def test_coin_is_blocked_until_timeout_expires(failover, clock, elapsed, blocked):
    clock.return_value = NOW
    failover.record_call(BTC)

    clock.return_value = NOW + elapsed
    assert failover.should_block_request(BTC) is blocked


@pytest.mark.parametrize(
    "elapsed, expected",
    [(0, TIMEOUT), (5, TIMEOUT - 5), (TIMEOUT - 0.5, 1), (TIMEOUT, 0), (TIMEOUT + 60, 0)],
)
def test_retry_after_counts_down_to_zero(failover, clock, elapsed, expected):
    clock.return_value = NOW
    failover.record_call(BTC)

    clock.return_value = NOW + elapsed
    assert failover.retry_after(BTC) == expected


def test_other_coins_are_not_blocked(failover, clock):
    clock.return_value = NOW
    failover.record_call(BTC)

    assert failover.should_block_request(ETH) is False
