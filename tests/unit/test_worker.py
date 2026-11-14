from unittest.mock import AsyncMock, patch

from app.config import settings
from app.schemas.outbox import OutboxEventRead
from app.worker.celery_app import celery_app
from app.worker.tasks import dispatch_outbox, handle_event, publish


def test_dispatcher_runs_on_a_schedule():
    schedule = celery_app.conf.beat_schedule["dispatch-outbox"]

    assert schedule["task"] == dispatch_outbox.name
    assert schedule["schedule"] == settings.OUTBOX_DISPATCH_INTERVAL


def test_publish_sends_the_event_as_a_task():
    event = OutboxEventRead(id=7, event_type="transfer.completed", payload={"a": 1})

    with patch("app.worker.tasks.handle_event") as handle_event:
        publish(event)

    handle_event.delay.assert_called_once_with(7, "transfer.completed", {"a": 1})


def test_broker_url_uses_its_own_redis_database():
    assert settings.CELERY_BROKER_URL.endswith(
        f"{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.CELERY_BROKER_DB}"
    )


def test_transfer_completed_event_sends_notifications():
    payload = {"transfer_id": 1}

    with patch("app.worker.tasks._with_session", new_callable=AsyncMock) as session:
        session.return_value = 2
        handle_event(7, "transfer.completed", payload)

    session.assert_awaited_once()


def test_unknown_event_types_are_ignored():
    with patch("app.worker.tasks._with_session", new_callable=AsyncMock) as session:
        handle_event(7, "something.else", {})

    session.assert_not_awaited()


def test_failed_emails_are_retried():
    assert handle_event.max_retries == 5
    assert OSError in handle_event.autoretry_for
