from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.dependencies import (
    get_cache_service,
    get_coingecko_service,
    get_failover_service,
)
from app.main import app
from app.repositories.coin_repository import CoinRepository
from app.services.cache_service import CacheService
from app.services.coingecko_service import CoinGeckoService
from app.services.failover_service import FailoverService
from tests.coins import COINS


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
def fake_coin_repository():
    repository = MagicMock(spec=CoinRepository)
    repository.get_by_symbol = AsyncMock(side_effect=COINS.get)
    return repository


@pytest.fixture
def overrides(mock_cache, mock_coingecko_api, mock_failover):
    """Dependencies replaced in every test that goes through the app.

    Test packages extend this by redefining an `overrides` fixture
    that requests this one and adds their own entries.
    """
    return {
        get_cache_service: lambda: mock_cache,
        get_coingecko_service: lambda: mock_coingecko_api,
        get_failover_service: lambda: mock_failover,
    }


@pytest.fixture
def override_dependencies(overrides):
    app.dependency_overrides.update(overrides)
    yield
    app.dependency_overrides.clear()
