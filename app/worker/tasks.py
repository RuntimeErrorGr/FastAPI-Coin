import asyncio
import smtplib
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import create_session_factory
from app.log import get_logger
from app.models import EventType
from app.repositories.notification_repository import NotificationRepository
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.user_repository import UserRepository
from app.schemas.outbox import OutboxEventRead
from app.services.email_sender import create_email_sender
from app.services.notification_service import NotificationService
from app.services.outbox_dispatcher import OutboxDispatcher
from app.worker.celery_app import celery_app

logger = get_logger(__name__)


def publish(event: OutboxEventRead) -> None:
    """Sends one event to the broker, as a `handle_event` task for a worker."""
    handle_event.delay(event.id, event.event_type, event.payload)


async def _with_session[T](work: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Runs `work` with a database session on a short-lived engine.

    A Celery task runs outside FastAPI, with no lifespan and no running event
    loop, so each task run creates its own engine and closes it when done.
    """
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    try:
        async with create_session_factory(engine)() as session:
            return await work(session)
    finally:
        await engine.dispose()


async def _dispatch(session: AsyncSession) -> int:
    return await OutboxDispatcher(
        session, OutboxRepository(session), publish
    ).dispatch()


async def _notify(session: AsyncSession, payload: dict[str, Any]) -> int:
    service = NotificationService(
        session,
        UserRepository(session),
        NotificationRepository(session),
        create_email_sender(),
    )
    return await service.notify_transfer_completed(payload)


@celery_app.task
def dispatch_outbox() -> int:
    """Periodic task (Celery beat): publishes pending outbox events."""
    return asyncio.run(_with_session(_dispatch))


@celery_app.task(
    autoretry_for=(OSError, smtplib.SMTPException),
    retry_backoff=True,
    max_retries=5,
)
def handle_event(event_id: int, event_type: str, payload: dict[str, Any]) -> None:
    """Consumes one published event.

    If sending an email fails, Celery runs the task again later (up to 5
    times, waiting longer each time). Only the unsent emails are retried.
    """
    if event_type != EventType.TRANSFER_COMPLETED:
        logger.warning(f"Ignoring event {event_id}: unknown type {event_type}")
        return

    sent = asyncio.run(_with_session(lambda session: _notify(session, payload)))
    logger.info(f"Event {event_id}: sent {sent} email(s)")
