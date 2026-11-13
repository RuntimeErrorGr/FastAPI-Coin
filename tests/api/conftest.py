from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_cache_service,
    get_coingecko_service,
    get_failover_service,
)
from app.main import app
from app.services.cache_service import CacheService
from app.services.coingecko_service import CoinGeckoService
from app.services.failover_service import FailoverService


@pytest.fixture
def mock_cache():
    mock = MagicMock(spec_set=CacheService)
    mock.is_up = True
    mock.get_rate = AsyncMock(return_value=None)
    mock.set_rate = AsyncMock()
    return mock


@pytest.fixture
def mock_failover():
    mock = MagicMock(spec_set=FailoverService)
    mock.should_block_request.return_value = False
    mock.record_call = MagicMock()
    return mock


@pytest.fixture
def mock_coingecko_api(mock_failover):
    mock = MagicMock(spec=CoinGeckoService)
    mock.get_rate = AsyncMock(return_value=20000)
    mock.failover = mock_failover
    return mock


@pytest.fixture
def client(mock_cache, mock_coingecko_api, mock_failover):
    app.dependency_overrides[get_cache_service] = lambda: mock_cache
    app.dependency_overrides[get_coingecko_service] = lambda: mock_coingecko_api
    app.dependency_overrides[get_failover_service] = lambda: mock_failover

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
