import asyncio
from datetime import timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.log import get_logger
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.notification import NotificationPending
from app.services.email_sender import EmailSender

logger = get_logger(__name__)

SUBJECT = "Transfer completed"


def _readable(amount: str) -> str:
    """Turns "1.50000000" into "1.5"."""
    return format(Decimal(amount).normalize(), "f")


class NotificationService:
    """Tells the sender and the recipient of a transfer that it completed."""

    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        notifications: NotificationRepository,
        email: EmailSender,
    ):
        self._session = session
        self._users = users
        self._notifications = notifications
        self._email = email

    async def notify_transfer_completed(self, payload: dict[str, Any]) -> int:
        """Notifies both users of a transfer and returns how many emails were sent.

        Safe to run again for the same event: the notifications already exist
        and only emails that were not sent yet are sent.
        """
        sender = await self._users.get_by_id(payload["sender_id"])
        recipient = await self._users.get_by_id(payload["recipient_id"])
        transfer_id = payload["transfer_id"]
        amount = f"{_readable(payload['amount'])} {payload['coin'].upper()}"

        await self._notifications.add_if_missing(
            sender.id, transfer_id, f"You sent {amount} to {recipient.username}."
        )
        await self._notifications.add_if_missing(
            recipient.id, transfer_id, f"You received {amount} from {sender.username}."
        )
        await self._session.commit()

        return await self._send(await self._notifications.list_unsent(transfer_id))

    async def retry_unsent(self, older_than: timedelta) -> int:
        """Sends the emails still unsent after `older_than` and returns how many.

        They are the ones whose event gave up retrying.
        """
        return await self._send(
            await self._notifications.list_unsent_older_than(older_than)
        )

    async def _send(self, pending: list[NotificationPending]) -> int:
        """Emails each notification and commits it as sent, one by one."""
        for email in pending:
            await asyncio.to_thread(self._email.send, email.to, SUBJECT, email.message)
            await self._notifications.mark_sent(email.notification_id)
            await self._session.commit()
            logger.info(f"Emailed {email.to}: {email.message}")
        return len(pending)
