from unittest.mock import MagicMock

import httpx
import pytest

from app.exceptions import ExternalAPIException
from app.schemas.coin import CoinType


class TestCoinGeckoService:
    async def test_get_rate_success(self, coingecko_service, mock_http_get):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"bitcoin": {"usd": 123.45}}

        mock_http_get.return_value = response

        rate = await coingecko_service.get_rate(CoinType.BTC)

        assert rate == 123.45

    async def test_get_rate_missing_rate(self, coingecko_service, mock_http_get):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {}

        mock_http_get.return_value = response

        with pytest.raises(ExternalAPIException) as exc:
            await coingecko_service.get_rate(CoinType.BTC)

        assert "Rate not found for coin" in str(exc.value)
        assert mock_http_get.await_count == 1

    @pytest.mark.parametrize(
        "status_code, expected_attempts",
        [
            (500, 2),  # server error: retried
            (503, 2),
            (429, 2),  # rate limited: retried
            (400, 1),  # client error: not retried
            (404, 1),
        ],
    )
    async def test_get_rate_http_status_error(
        self, coingecko_service, mock_http_get, status_code, expected_attempts
    ):
        request = httpx.Request("GET", "https://example.test")
        mock_http_get.return_value = httpx.Response(status_code, request=request)

        with pytest.raises(ExternalAPIException) as exc:
            await coingecko_service.get_rate(CoinType.BTC)

        assert "Failed to fetch data from CoinGecko API" in str(exc.value)
        assert mock_http_get.await_count == expected_attempts
        coingecko_service.failover.record_call.assert_not_called()

    async def test_get_rate_transport_error_is_retried(
        self, coingecko_service, mock_http_get
    ):
        mock_http_get.side_effect = httpx.ConnectTimeout("timeout")

        with pytest.raises(ExternalAPIException):
            await coingecko_service.get_rate(CoinType.BTC)

        assert mock_http_get.await_count == 2

    async def test_get_rate_recovers_after_retry(
        self, coingecko_service, mock_http_get
    ):
        ok = MagicMock()
        ok.raise_for_status.return_value = None
        ok.json.return_value = {"bitcoin": {"usd": 100.0}}
        mock_http_get.side_effect = [httpx.ConnectError("down"), ok]

        rate = await coingecko_service.get_rate(CoinType.BTC)

        assert rate == 100.0
        assert mock_http_get.await_count == 2
        coingecko_service.failover.record_call.assert_called_once_with(CoinType.BTC)
