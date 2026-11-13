from tests.coins import BTC


class TestExchangeWithDatabase:
    """Test Exchange with coin lookup."""

    async def test_exchange_uses_coin_from_database(
        self, async_client, mock_coingecko_api
    ):
        mock_coingecko_api.get_rate.return_value = 20000

        response = await async_client.get(
            "/exchange", params={"coin": "BTC", "amount": "2"}
        )

        assert response.status_code == 200
        assert response.json() == {"usd_amount": 40000}
        mock_coingecko_api.get_rate.assert_awaited_once_with(BTC)

    async def test_exchange_rejects_coin_missing_from_database(self, async_client):
        response = await async_client.get(
            "/exchange", params={"coin": "doge", "amount": "1"}
        )

        assert response.status_code == 400
        assert "Coin not supported" in response.json().get("error", "")
