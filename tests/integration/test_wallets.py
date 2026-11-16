import pytest
from sqlalchemy import select

from app.models import EntryType, LedgerEntry


async def test_opens_an_empty_wallet(auth_client):
    response = await auth_client.post("/wallets", json={"coin": "BTC"})

    assert response.status_code == 201
    wallet = response.json()
    assert wallet["coin"] == "btc"
    assert wallet["balance"] == "0.00000000"


async def test_lists_own_wallets(auth_client):
    await auth_client.post("/wallets", json={"coin": "eth"})
    await auth_client.post("/wallets", json={"coin": "btc"})

    response = await auth_client.get("/wallets")

    assert response.status_code == 200
    assert [wallet["coin"] for wallet in response.json()] == ["btc", "eth"]


async def test_rejects_second_wallet_for_same_coin(auth_client):
    await auth_client.post("/wallets", json={"coin": "btc"})

    response = await auth_client.post("/wallets", json={"coin": "btc"})

    assert response.status_code == 409
    assert response.json() == {"error": "You already have a btc wallet."}


async def test_rejects_unsupported_coin(auth_client):
    response = await auth_client.post("/wallets", json={"coin": "doge"})

    assert response.status_code == 404
    assert response.json() == {"error": "Coin not supported: doge."}


async def test_requires_authentication(http_client):
    response = await http_client.get("/wallets")

    assert response.status_code == 401


async def test_deposit_increases_balance(auth_client):
    await auth_client.post("/wallets", json={"coin": "btc"})

    await auth_client.post("/wallets/btc/deposit", json={"amount": "1.5"})
    response = await auth_client.post("/wallets/BTC/deposit", json={"amount": "0.25"})

    assert response.status_code == 200
    assert response.json()["balance"] == "1.75000000"


async def test_deposit_records_one_credit_entry(auth_client, db_session):
    wallet = (await auth_client.post("/wallets", json={"coin": "btc"})).json()

    await auth_client.post("/wallets/btc/deposit", json={"amount": "2"})

    entries = (
        await db_session.scalars(
            select(LedgerEntry).where(LedgerEntry.wallet_id == wallet["id"])
        )
    ).all()
    assert [(e.wallet_id, e.entry_type, e.amount) for e in entries] == [
        (wallet["id"], EntryType.CREDIT, 2)
    ]


async def test_deposit_requires_an_open_wallet(auth_client):
    response = await auth_client.post("/wallets/eth/deposit", json={"amount": "1"})

    assert response.status_code == 404
    assert response.json() == {"error": "You don't have a eth wallet."}


@pytest.mark.parametrize("amount", ["0", "-1", "0.123456789"])
async def test_deposit_rejects_invalid_amount(auth_client, amount):
    await auth_client.post("/wallets", json={"coin": "btc"})

    response = await auth_client.post("/wallets/btc/deposit", json={"amount": amount})

    assert response.status_code == 422
