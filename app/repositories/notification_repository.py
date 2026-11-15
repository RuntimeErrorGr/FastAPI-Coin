from datetime import timedelta

from sqlalchemy import Select, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, User
from app.schemas.notification import NotificationRead, NotificationPending


class NotificationRepository:
    """Data access for notifications. It never commits."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_if_missing(
        self, user_id: int, transfer_id: int, message: str
    ) -> None:
        """Creates the notification unless this user already has one for the transfer."""
        await self._session.execute(
            insert(Notification)
            .values(user_id=user_id, transfer_id=transfer_id, message=message)
            .on_conflict_do_nothing(index_elements=["transfer_id", "user_id"])
        )

    async def list_unsent(self, transfer_id: int) -> list[NotificationPending]:
        """Returns the transfer's notifications whose email was not sent yet."""
        return await self._pending(
            _unsent().where(Notification.transfer_id == transfer_id)
        )

    async def list_unsent_older_than(
        self, age: timedelta, limit: int = 100
    ) -> list[NotificationPending]:
        """Returns unsent notifications created more than `age` ago, oldest first."""
        return await self._pending(
            _unsent().where(Notification.created_at < func.now() - age).limit(limit)
        )

    async def _pending(self, query: Select) -> list[NotificationPending]:
        rows = await self._session.execute(query)
        return [NotificationPending.model_validate(row) for row in rows]

    async def mark_sent(self, notification_id: int) -> None:
        """Records that the notification's email went out."""
        await self._session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(sent_at=func.now())
        )

    async def list_for_user(self, user_id: int) -> list[NotificationRead]:
        """Returns the user's notifications, newest first."""
        notifications = await self._session.scalars(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.id.desc())
        )
        return [NotificationRead.model_validate(n) for n in notifications]


def _unsent() -> Select:
    """Notifications whose email was not sent yet, with the user's address."""
    return (
        select(
            Notification.id.label("notification_id"),
            User.email.label("to"),
            Notification.message,
        )
        .join(User, Notification.user_id == User.id)
        .where(Notification.sent_at.is_(None))
        .order_by(Notification.id)
    )
