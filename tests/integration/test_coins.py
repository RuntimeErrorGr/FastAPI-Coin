from tests.coins import COINS


async def test_lists_all_supported_coins(http_client):
    response = await http_client.get("/coins")

    assert response.status_code == 200
    assert response.json() == [coin.model_dump() for coin in COINS.values()]


async def test_lists_coins_from_cache_when_present(http_client, cache):
    await cache.set_coins([COINS["btc"]])

    response = await http_client.get("/coins")
    assert response.json() == [COINS["btc"].model_dump()]
