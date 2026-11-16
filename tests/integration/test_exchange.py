import pytest

from app.exceptions import ExternalAPIException
from tests.coins import BTC


async def test_converts_amount(auth_client, coingecko):
    coingecko.get_rate.return_value = 20000.0

    response = await auth_client.get("/exchange", params={"coin": "BTC", "amount": 2})

    assert response.status_code == 200
    assert response.json() == {"usd_amount": 40000.0}
    coingecko.get_rate.assert_awaited_once_with(BTC)


async def test_usd_converts_one_to_one_without_calling_the_api(auth_client, coingecko):
    response = await auth_client.get("/exchange", params={"coin": "usd", "amount": 2})

    assert response.json() == {"usd_amount": 2.0}
    coingecko.get_rate.assert_not_awaited()


async def test_second_request_is_served_from_redis(auth_client, coingecko, cache):
    coingecko.get_rate.return_value = 20000.0
    params = {"coin": "btc", "amount": 1}

    await auth_client.get("/exchange", params=params)
    response = await auth_client.get("/exchange", params=params)

    assert response.json() == {"usd_amount": 20000.0}
    assert await cache.get_rate(BTC) == 20000.0
    coingecko.get_rate.assert_awaited_once_with(BTC)


async def test_requires_authentication(http_client):
    response = await http_client.get("/exchange", params={"coin": "btc", "amount": 1})

    assert response.status_code == 401
    assert response.json() == {"error": "Not authenticated."}


async def test_rejects_coin_missing(auth_client):
    response = await auth_client.get("/exchange", params={"coin": "doge", "amount": 1})

    assert response.status_code == 400
    assert response.json() == {"error": "Coin not supported."}


@pytest.mark.parametrize("amount", [0, 10000])
async def test_rejects_out_of_bounds_amount(auth_client, amount):
    response = await auth_client.get(
        "/exchange", params={"coin": "btc", "amount": amount}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Out of bounds amount."}


@pytest.mark.parametrize(
    "params", [{}, {"coin": "btc"}, {"coin": "btc", "amount": "abc"}]
)
async def test_rejects_missing_or_malformed_parameters(auth_client, params):
    response = await auth_client.get("/exchange", params=params)

    assert response.status_code == 422


async def test_reports_external_api_failure(auth_client, coingecko):
    coingecko.get_rate.side_effect = ExternalAPIException("CoinGecko is down")

    response = await auth_client.get("/exchange", params={"coin": "btc", "amount": 1})

    assert response.status_code == 500
    assert response.json() == {"error": "Internal server error."}


async def test_fetches_rate_when_redis_is_down(auth_client, coingecko, redis_down):
    coingecko.get_rate.return_value = 20000.0

    response = await auth_client.get("/exchange", params={"coin": "btc", "amount": 1})

    assert response.status_code == 200
    assert response.json() == {"usd_amount": 20000.0}


async def test_rate_limits_when_redis_is_down_and_coin_was_fetched_recently(
    auth_client, coingecko, failover, redis_down
):
    failover.record_call(BTC)

    response = await auth_client.get("/exchange", params={"coin": "btc", "amount": 1})

    assert response.status_code == 503
    assert int(response.headers["Retry-After"]) > 0
    coingecko.get_rate.assert_not_awaited()
