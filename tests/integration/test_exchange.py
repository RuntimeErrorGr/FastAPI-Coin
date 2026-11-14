import pytest

from app.exceptions import ExternalAPIException
from tests.coins import BTC


async def test_converts_amount(http_client, coingecko):
    coingecko.get_rate.return_value = 20000.0

    response = await http_client.get("/exchange", params={"coin": "BTC", "amount": 2})

    assert response.status_code == 200
    assert response.json() == {"usd_amount": 40000.0}
    coingecko.get_rate.assert_awaited_once_with(BTC)


async def test_rejects_coin_missing(http_client):
    response = await http_client.get("/exchange", params={"coin": "doge", "amount": 1})

    assert response.status_code == 400
    assert response.json() == {"error": "Coin not supported."}


@pytest.mark.parametrize("amount", [0, 10000])
async def test_rejects_out_of_bounds_amount(http_client, amount):
    response = await http_client.get(
        "/exchange", params={"coin": "btc", "amount": amount}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Out of bounds amount."}


@pytest.mark.parametrize(
    "params", [{}, {"coin": "btc"}, {"coin": "btc", "amount": "abc"}]
)
async def test_rejects_missing_or_malformed_parameters(http_client, params):
    response = await http_client.get("/exchange", params=params)

    assert response.status_code == 422


async def test_reports_external_api_failure(http_client, coingecko):
    coingecko.get_rate.side_effect = ExternalAPIException("CoinGecko is down")

    response = await http_client.get("/exchange", params={"coin": "btc", "amount": 1})

    assert response.status_code == 500
    assert response.json() == {"error": "Internal server error."}


async def test_rate_limits_when_cache_is_down_and_coin_was_fetched_recently(
    http_client, cache, failover
):
    cache.is_up = False
    failover.record_call(BTC)

    response = await http_client.get("/exchange", params={"coin": "btc", "amount": 1})

    assert response.status_code == 503
    assert int(response.headers["Retry-After"]) > 0
