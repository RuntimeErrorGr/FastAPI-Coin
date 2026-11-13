import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_coin_repository
from app.main import app


@pytest.fixture
def overrides(overrides, fake_coin_repository):
    return {**overrides, get_coin_repository: lambda: fake_coin_repository}


@pytest.fixture
def client(override_dependencies):
    with TestClient(app) as test_client:
        yield test_client
