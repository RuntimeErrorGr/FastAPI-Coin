from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import EntryType, EventType, LedgerEntry, OutboxEvent


@pytest.fixture
async def btc_wallets(auth_client, bob_headers):
    """Alice has a BTC wallet with 10 BTC, Bob has an empty BTC wallet."""
    await auth_client.post("/wallets", json={"coin": "btc"})
    await auth_client.post("/wallets/btc/deposit", json={"amount": "10"})
    await auth_client.post("/wallets", json={"coin": "btc"}, headers=bob_headers)


async def balances(auth_client, bob_headers) -> tuple[str, str]:
    alice = (await auth_client.get("/wallets")).json()[0]["balance"]
    bob = (await auth_client.get("/wallets", headers=bob_headers)).json()[0]["balance"]
    return alice, bob


def transfer(amount: str = "2.5", recipient: str = "bob", coin: str = "btc") -> dict:
    return {"recipient": recipient, "coin": coin, "amount": amount}


async def send(client, data: dict, key: str | None = None):
    """POSTs a transfer with an Idempotency-Key (a new random one by default)."""
    headers = {"Idempotency-Key": key or str(uuid4())}
    return await client.post("/transfers", json=data, headers=headers)


async def test_transfer_moves_money_between_wallets(
    auth_client, bob_headers, btc_wallets
):
    response = await send(auth_client, transfer())

    assert response.status_code == 201
    body = response.json()
    assert (body["sender"], body["recipient"], body["coin"], body["amount"]) == (
        "alice",
        "bob",
        "btc",
        "2.50000000",
    )
    assert await balances(auth_client, bob_headers) == ("7.50000000", "2.50000000")


async def test_transfer_records_a_debit_and_a_matching_credit(
    auth_client, btc_wallets, db_session
):
    transfer_id = (await send(auth_client, transfer())).json()["id"]

    entries = (
        await db_session.scalars(
            select(LedgerEntry).where(LedgerEntry.transfer_id == transfer_id)
        )
    ).all()
    assert sorted((e.entry_type, e.amount) for e in entries) == [
        (EntryType.CREDIT, 2.5),
        (EntryType.DEBIT, 2.5),
    ]


async def test_transfer_is_visible_to_sender_and_recipient(
    auth_client, bob_headers, btc_wallets
):
    sent = (await send(auth_client, transfer())).json()

    assert (await auth_client.get("/transfers")).json() == [sent]
    assert (await auth_client.get("/transfers", headers=bob_headers)).json() == [sent]


async def test_rejects_transfer_without_enough_funds(
    auth_client, bob_headers, btc_wallets
):
    response = await send(auth_client, transfer(amount="10.5"))

    assert response.status_code == 400
    assert response.json() == {"error": "Insufficient funds."}
    assert await balances(auth_client, bob_headers) == ("10.00000000", "0.00000000")


async def test_rejects_transfer_to_yourself(auth_client, btc_wallets):
    response = await send(auth_client, transfer(recipient="alice"))

    assert response.status_code == 400
    assert response.json() == {"error": "You cannot transfer to yourself."}


@pytest.mark.parametrize(
    "data, error",
    [
        (transfer(recipient="nobody"), "User not found: nobody."),
        (transfer(coin="eth"), "You don't have a eth wallet."),
    ],
    ids=["unknown-recipient", "sender-without-wallet"],
)
async def test_rejects_transfer_to_missing_user_or_wallet(
    auth_client, btc_wallets, data, error
):
    response = await send(auth_client, data)

    assert response.status_code == 404
    assert response.json() == {"error": error}


async def test_rejects_transfer_when_recipient_has_no_wallet_for_the_coin(
    auth_client, btc_wallets
):
    await auth_client.post("/wallets", json={"coin": "eth"})
    await auth_client.post("/wallets/eth/deposit", json={"amount": "1"})

    response = await send(auth_client, transfer(coin="eth", amount="1"))

    assert response.status_code == 404
    assert response.json() == {"error": "bob has no eth wallet."}


async def test_requires_authentication(http_client):
    response = await send(http_client, transfer())

    assert response.status_code == 401


async def test_retry_with_same_key_returns_original_without_paying_twice(
    auth_client, bob_headers, btc_wallets
):
    first = await send(auth_client, transfer(amount="6"), key="pay-bob-1")
    retry = await send(auth_client, transfer(amount="6"), key="pay-bob-1")

    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.json() == first.json()
    assert await balances(auth_client, bob_headers) == ("4.00000000", "6.00000000")


async def test_reusing_a_key_for_a_different_transfer_is_rejected(
    auth_client, btc_wallets
):
    await send(auth_client, transfer(amount="1"), key="pay-bob-1")

    response = await send(auth_client, transfer(amount="2"), key="pay-bob-1")

    assert response.status_code == 409
    assert response.json() == {
        "error": "Idempotency key already used for a different transfer."
    }


async def test_idempotency_key_is_required(auth_client, btc_wallets):
    response = await auth_client.post("/transfers", json=transfer())

    assert response.status_code == 422


async def outbox_events(db_session) -> list[OutboxEvent]:
    return (await db_session.scalars(select(OutboxEvent))).all()


async def test_transfer_saves_one_pending_event(
    auth_client, alice, bob_headers, btc_wallets, db_session
):
    bob = (await auth_client.get("/users/me", headers=bob_headers)).json()

    sent = (await send(auth_client, transfer())).json()

    [event] = await outbox_events(db_session)
    assert event.event_type == EventType.TRANSFER_COMPLETED
    assert event.published_at is None
    assert event.payload == {
        "transfer_id": sent["id"],
        "sender_id": alice["id"],
        "recipient_id": bob["id"],
        "coin": "btc",
        "amount": "2.50000000",
    }


async def test_rejected_transfer_saves_no_event(auth_client, btc_wallets, db_session):
    await send(auth_client, transfer(amount="999"))

    assert await outbox_events(db_session) == []


async def test_replayed_transfer_saves_no_second_event(
    auth_client, btc_wallets, db_session
):
    await send(auth_client, transfer(), key="pay-bob-1")
    await send(auth_client, transfer(), key="pay-bob-1")

    assert len(await outbox_events(db_session)) == 1
