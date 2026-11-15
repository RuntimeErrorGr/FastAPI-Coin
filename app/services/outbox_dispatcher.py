from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.log import get_logger
from app.repositories.outbox_repository import OutboxRepository
from app.schemas.outbox import OutboxEventRead

logger = get_logger(__name__)


class OutboxDispatcher:
    """Hands pending outbox events to the message broker."""

    def __init__(
        self,
        session: AsyncSession,
        outbox: OutboxRepository,
        publish: Callable[[OutboxEventRead], None],
    ):
        self._session = session
        self._outbox = outbox
        self._publish = publish

    async def dispatch(self, limit: int = 100) -> int:
        """Publishes pending events in Redis and returns how many were sent.

        Events are marked as published only after all of them were sent. If
        publishing fails, nothing is marked and the next run tries again, so
        an event can be sent more than once and consumers must allow for that.
        """
        events = await self._outbox.lock_pending(limit)
        for event in events:
            self._publish(event)

        if events:
            await self._outbox.mark_published([event.id for event in events])
            logger.info(f"Published {len(events)} outbox event(s)")
        await self._session.commit()
        return len(events)
