from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EventType, OutboxEvent
from app.schemas.outbox import OutboxEventRead


class OutboxRepository:
    """Stores events to publish.

    It never commits: the event is saved with the caller's transaction, so it
    exists if and only if that transaction commits.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, event_type: EventType, payload: dict[str, Any]) -> None:
        """Adds an event to the current transaction."""
        self._session.add(OutboxEvent(event_type=event_type, payload=payload))
        await self._session.flush()

    async def lock_pending(self, limit: int) -> list[OutboxEventRead]:
        """Returns the oldest unpublished events and locks them until commit.

        SKIP LOCKED makes a second dispatcher skip events the first one is
        already publishing, instead of waiting for them or sending them twice.
        """
        events = await self._session.scalars(
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return [OutboxEventRead.model_validate(event) for event in events]

    async def mark_published(self, event_ids: list[int]) -> None:
        """Records that the events were handed to the broker."""
        await self._session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id.in_(event_ids))
            .values(published_at=func.now())
        )
