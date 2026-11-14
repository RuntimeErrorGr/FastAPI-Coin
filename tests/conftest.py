from unittest.mock import MagicMock

import pytest

from app.services.coingecko_service import CoinGeckoService
from app.services.failover_service import FailoverService


@pytest.fixture
def failover():
    """The FailoverService: it only keeps timestamps in memory."""
    return FailoverService()


@pytest.fixture
def coingecko():
    """Mock for CoinGeckoService. Tests set `get_rate.return_value`."""
    return MagicMock(spec=CoinGeckoService)
