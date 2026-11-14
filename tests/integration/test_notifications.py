from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import Notification, OutboxEvent
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService


class FakeEmailSender:
    """Records emails instead of sending them. Can be told to fail."""

    def __init__(self, fail: bool = False):
        self.sent: list[tuple[str, str, str]] = []
        self.fail = fail

    def send(self, to: str, subject: str, body: str) -> None:
        if self.fail:
            raise ConnectionError("SMTP server unreachable")
        self.sent.append((to, subject, body))


@pytest.fixture
async def transfer_event(auth_client, bob_headers, db_session) -> dict:
    """Alice sends 2.5 BTC to Bob; returns the payload of the saved event."""
    await auth_client.post("/wallets", json={"coin": "btc"})
    await auth_client.post("/wallets/btc/deposit", json={"amount": "10"})
    await auth_client.post("/wallets", json={"coin": "btc"}, headers=bob_headers)
    await auth_client.post(
        "/transfers",
        json={"recipient": "bob", "coin": "btc", "amount": "2.5"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    event = await db_session.scalar(select(OutboxEvent))
    return event.payload


def service(db_session, email) -> NotificationService:
    return NotificationService(
        db_session,
        UserRepository(db_session),
        NotificationRepository(db_session),
        email,
    )


async def test_emails_sender_and_recipient(db_session, transfer_event):
    email = FakeEmailSender()

    sent = await service(db_session, email).notify_transfer_completed(transfer_event)

    assert sent == 2
    assert sorted(email.sent) == [
        ("alice@example.com", "Transfer completed", "You sent 2.5 BTC to bob."),
        ("bob@example.com", "Transfer completed", "You received 2.5 BTC from alice."),
    ]


async def test_handling_the_same_event_twice_sends_nothing_more(
    db_session, transfer_event
):
    email = FakeEmailSender()
    await service(db_session, email).notify_transfer_completed(transfer_event)

    sent_again = await service(db_session, email).notify_transfer_completed(
        transfer_event
    )

    assert sent_again == 0
    assert len(email.sent) == 2
    assert len((await db_session.scalars(select(Notification))).all()) == 2


async def test_unsent_emails_are_sent_when_retried(db_session, transfer_event):
    with pytest.raises(ConnectionError):
        await service(db_session, FakeEmailSender(fail=True)).notify_transfer_completed(
            transfer_event
        )

    email = FakeEmailSender()
    sent = await service(db_session, email).notify_transfer_completed(transfer_event)

    assert sent == 2
    assert len(email.sent) == 2


async def test_users_see_their_notifications(
    auth_client, bob_headers, db_session, transfer_event
):
    await service(db_session, FakeEmailSender()).notify_transfer_completed(
        transfer_event
    )

    response = await auth_client.get("/notifications", headers=bob_headers)

    assert response.status_code == 200
    [notification] = response.json()
    assert notification["message"] == "You received 2.5 BTC from alice."
    assert notification["sent_at"] is not None


async def test_notifications_require_authentication(http_client):
    response = await http_client.get("/notifications")

    assert response.status_code == 401
