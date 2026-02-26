from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache_service import CacheService
from app.services.coingecko_service import CoinGeckoService
from app.services.failover_service import FailoverService


@pytest.fixture
def failover_service():
    service = FailoverService()
    service._timeout = 60
    return service


@pytest.fixture
def mock_redis_client():
    client = MagicMock()
    client.get = AsyncMock()
    client.setex = AsyncMock()
    return client


@pytest.fixture
def cache_service(mock_redis_client):
    with patch(
        "app.services.cache_service.redis.Redis", return_value=mock_redis_client
    ):
        yield CacheService()


@pytest.fixture
def mock_http_get():
    with patch(
        "app.services.coingecko_service.httpx.AsyncClient.get",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def coingecko_service():
    return CoinGeckoService(failover=MagicMock())
