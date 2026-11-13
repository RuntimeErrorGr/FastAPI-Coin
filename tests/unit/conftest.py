from unittest.mock import AsyncMock, MagicMock

import pytest
from tenacity import wait_none

from app.repositories.coin_repository import CoinRepository
from app.services.cache_service import CacheService
from app.services.coingecko_service import CoinGeckoService
from tests.coins import COINS


@pytest.fixture
def redis_client():
    return AsyncMock()


@pytest.fixture
def cache_service(redis_client):
    """Real CacheService talking to a fake Redis client."""
    service = CacheService()
    service.client = redis_client
    return service


@pytest.fixture
def http_client():
    return AsyncMock()


@pytest.fixture
def coingecko_service(http_client):
    """Real CoinGeckoService talking to a fake HTTP client, with no wait between retries."""
    service = CoinGeckoService()
    service.client = http_client
    service._fetch_rate.retry.wait = wait_none()
    return service


@pytest.fixture
def coin_repository():
    """Stand-in for CoinRepository that knows the coins in tests/coins.py."""
    mock = MagicMock(spec=CoinRepository)
    mock.get_by_symbol.side_effect = COINS.get
    return mock
