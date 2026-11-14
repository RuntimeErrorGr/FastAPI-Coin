from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.models import EventType, OutboxEvent
from app.repositories.outbox_repository import OutboxRepository
from app.services.outbox_dispatcher import OutboxDispatcher
from app.worker.tasks import dispatch_outbox


@pytest.fixture
async def pending_events(db_session):
    """Two unpublished events, as a transfer would have saved them."""
    outbox = OutboxRepository(db_session)
    await outbox.add(EventType.TRANSFER_COMPLETED, {"transfer_id": 1})
    await outbox.add(EventType.TRANSFER_COMPLETED, {"transfer_id": 2})
    await db_session.commit()


def dispatcher(db_session, publish) -> OutboxDispatcher:
    return OutboxDispatcher(db_session, OutboxRepository(db_session), publish)


async def unpublished(db_session) -> list[OutboxEvent]:
    return (
        await db_session.scalars(
            select(OutboxEvent).where(OutboxEvent.published_at.is_(None))
        )
    ).all()


async def test_publishes_pending_events_oldest_first(db_session, pending_events):
    published = []

    count = await dispatcher(db_session, published.append).dispatch()

    assert count == 2
    assert [event.payload["transfer_id"] for event in published] == [1, 2]
    assert await unpublished(db_session) == []


async def test_published_events_are_not_sent_again(db_session, pending_events):
    published = []
    await dispatcher(db_session, published.append).dispatch()

    count = await dispatcher(db_session, published.append).dispatch()

    assert count == 0
    assert len(published) == 2


async def test_events_stay_pending_when_the_broker_fails(db_session, pending_events):
    def broker_down(_):
        raise ConnectionError("broker unreachable")

    with pytest.raises(ConnectionError):
        await dispatcher(db_session, broker_down).dispatch()
    await db_session.rollback()

    assert len(await unpublished(db_session)) == 2


def test_celery_task_runs_the_dispatcher_against_the_database():
    with patch("app.worker.tasks.handle_event") as handle_event:
        assert dispatch_outbox() == 0

    handle_event.delay.assert_not_called()
