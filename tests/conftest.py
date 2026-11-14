from unittest.mock import MagicMock

import pytest

from app.services.cache_service import CacheService
from app.services.coingecko_service import CoinGeckoService
from app.services.failover_service import FailoverService


@pytest.fixture
def failover():
    """The FailoverService: it only keeps timestamps in memory."""
    return FailoverService()


@pytest.fixture
def cache():
    """Mock for CacheService that is up and empty."""
    mock = MagicMock(spec=CacheService)
    mock.is_up = True
    mock.get_rate.return_value = None
    mock.get_coins.return_value = None
    return mock


@pytest.fixture
def coingecko():
    """Mock for CoinGeckoService. Tests set `get_rate.return_value`."""
    return MagicMock(spec=CoinGeckoService)
