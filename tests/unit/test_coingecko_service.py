from unittest.mock import MagicMock

import httpx
import pytest

from app.exceptions import ExternalAPIException
from app.schemas.coin import CoinType


class TestCoinGeckoService:
    @pytest.mark.asyncio
    async def test_get_rate_success(self, coingecko_service, mock_http_get):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"bitcoin": {"usd": 123.45}}

        mock_http_get.return_value = response

        rate = await coingecko_service.get_rate(CoinType.BTC)

        assert rate == 123.45

    @pytest.mark.asyncio
    async def test_get_rate_missing_rate(self, coingecko_service, mock_http_get):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {}

        mock_http_get.return_value = response

        with pytest.raises(ExternalAPIException) as exc:
            await coingecko_service.get_rate(CoinType.BTC)

        assert "Rate not found for coin" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_rate_http_error(self, coingecko_service, mock_http_get):
        response = MagicMock()
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "boom", request=None, response=None
        )

        mock_http_get.return_value = response

        with pytest.raises(ExternalAPIException) as exc:
            await coingecko_service.get_rate(CoinType.BTC)

        assert "Failed to fetch data from CoinGecko API" in str(exc.value)
