import pytest

from app.exceptions import ExternalAPIException
from app.schemas.coin import CoinType


class TestExchange:
    """API and endpoint tests for /exchange endpoint."""

    @pytest.mark.parametrize(
        "coin, cached_rate, api_rate, amount, expected_usd_amount",
        [
            ("btc", 20000, None, 1, 20000),
            ("eth", None, 3000, 2, 6000),
            ("xRp", 0.5, None, 1000, 500),
            ("BTc", None, 25000, 0.1, 2500),
        ],
    )
    def test_exchange_success_cases(
        self,
        client,
        mock_cache,
        mock_coingecko_api,
        coin,
        cached_rate,
        api_rate,
        amount,
        expected_usd_amount,
    ):
        if cached_rate:
            mock_cache.get_rate.return_value = cached_rate
        else:
            mock_cache.get_rate.return_value = None
            mock_coingecko_api.get_rate.return_value = api_rate

        response = client.get("/exchange", params={"coin": coin, "amount": str(amount)})
        assert response.status_code == 200

        data = response.json()
        assert data.get("usd_amount") == expected_usd_amount

    @pytest.mark.parametrize(
        "coin, amount, expected_error",
        [
            ("doge", 1.0, "Coin not supported"),
            ("btc", 0, "Out of bounds amount"),
            ("eth", -1, "Out of bounds amount"),
            ("xrp", 10000, "Out of bounds amount"),
        ],
    )
    def test_exchange_validation_errors(
        self,
        client,
        coin,
        amount,
        expected_error,
    ):
        response = client.get("/exchange", params={"coin": coin, "amount": str(amount)})
        assert response.status_code == 400
        error = response.json()
        assert expected_error in error.get("error", "")

    @pytest.mark.parametrize(
        "params",
        [
            ({"amount": "1.0"}),
            ({"coin": "btc"}),
            ({}),
            ({"amount": "", "coin": ""}),
            ({"amount": None, "coin": 44}),
        ],
    )
    def test_exchange_missing_params(self, client, params):
        response = client.get("/exchange", params=params)
        assert response.status_code == 422

        error = response.json()
        assert "Invalid input" in error.get("error", "")

    def test_exchange_cache_down_allows_request(
        self,
        client,
        mock_cache,
        mock_coingecko_api,
        mock_failover,
    ):
        mock_cache.is_up = False
        mock_cache.get_rate.return_value = None
        mock_failover.should_block_request.return_value = False
        mock_coingecko_api.get_rate.return_value = 3000

        response = client.get("/exchange", params={"coin": "eth", "amount": "1"})

        assert response.status_code == 200
        assert response.json().get("usd_amount") == 3000
        mock_failover.should_block_request.assert_called_once_with(CoinType.ETH)
        mock_coingecko_api.get_rate.assert_awaited_once_with(CoinType.ETH)

    def test_exchange_cache_down_blocks_request(
        self,
        client,
        mock_cache,
        mock_coingecko_api,
        mock_failover,
    ):
        mock_cache.is_up = False
        mock_cache.get_rate.return_value = None
        mock_failover.should_block_request.return_value = True
        mock_failover.retry_after.return_value = 42

        response = client.get("/exchange", params={"coin": "eth", "amount": "1"})

        assert response.status_code == 503
        assert response.headers["Retry-After"] == "42"
        assert "temporarily unavailable" in response.json().get("error", "")
        mock_failover.should_block_request.assert_called_once_with(CoinType.ETH)
        mock_coingecko_api.get_rate.assert_not_awaited()

    def test_exchange_cache_up_skips_failover(
        self,
        client,
        mock_cache,
        mock_coingecko_api,
        mock_failover,
    ):
        mock_cache.get_rate.return_value = None
        mock_coingecko_api.get_rate.return_value = 3000

        response = client.get("/exchange", params={"coin": "eth", "amount": "1"})

        assert response.status_code == 200
        mock_failover.should_block_request.assert_not_called()
        mock_cache.set_rate.assert_awaited_once_with(CoinType.ETH, 3000)

    def test_exchange_api_error(
        self,
        client,
        mock_cache,
        mock_coingecko_api,
    ):
        mock_cache.get_rate.return_value = None
        mock_coingecko_api.get_rate.side_effect = ExternalAPIException("API Error")

        response = client.get("/exchange", params={"coin": "xrp", "amount": "1"})

        assert response.status_code == 500
        error = response.json()
        assert "Internal server error" in error.get("error", "")

    def test_exchange_zero_cached_rate_is_a_hit(
        self,
        client,
        mock_cache,
        mock_coingecko_api,
    ):
        mock_cache.get_rate.return_value = 0.0

        response = client.get("/exchange", params={"coin": "xrp", "amount": "5"})

        assert response.status_code == 200
        assert response.json().get("usd_amount") == 0.0
        mock_coingecko_api.get_rate.assert_not_awaited()
