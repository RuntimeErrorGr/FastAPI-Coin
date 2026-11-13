import httpx
import pytest

from app.exceptions import ExternalAPIException
from tests.coins import BTC


def api_response(status_code: int, json: dict | None = None) -> httpx.Response:
    request = httpx.Request("GET", "https://coingecko.test")
    return httpx.Response(status_code, json=json, request=request)


async def test_get_rate_returns_usd_price(coingecko_service, http_client):
    http_client.get.return_value = api_response(200, {"bitcoin": {"usd": 123.45}})

    rate = await coingecko_service.get_rate(BTC)

    assert rate == 123.45
    http_client.get.assert_awaited_once_with(
        "", params={"ids": "bitcoin", "vs_currencies": "usd"}
    )


async def test_get_rate_fails_when_price_is_missing(coingecko_service, http_client):
    http_client.get.return_value = api_response(200, {})

    with pytest.raises(ExternalAPIException, match="Rate not found"):
        await coingecko_service.get_rate(BTC)

    assert http_client.get.await_count == 1


@pytest.mark.parametrize(
    "status_code, attempts",
    [(500, 2), (503, 2), (429, 2), (400, 1), (404, 1)],
)
async def test_get_rate_retries_only_transient_http_errors(
    coingecko_service, http_client, status_code, attempts
):
    http_client.get.return_value = api_response(status_code)

    with pytest.raises(ExternalAPIException, match="Failed to fetch"):
        await coingecko_service.get_rate(BTC)

    assert http_client.get.await_count == attempts


async def test_get_rate_retries_network_errors(coingecko_service, http_client):
    http_client.get.side_effect = httpx.ConnectTimeout("timed out")

    with pytest.raises(ExternalAPIException):
        await coingecko_service.get_rate(BTC)

    assert http_client.get.await_count == 2


async def test_get_rate_recovers_after_failed_attempt(coingecko_service, http_client):
    http_client.get.side_effect = [
        httpx.ConnectError("down"),
        api_response(200, {"bitcoin": {"usd": 100.0}}),
    ]

    rate = await coingecko_service.get_rate(BTC)

    assert rate == 100.0
    assert http_client.get.await_count == 2
