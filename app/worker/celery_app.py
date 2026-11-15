from celery import Celery

from app.config import settings

celery_app = Celery(
    "coinapi",
    broker=settings.CELERY_BROKER_URL,
    include=["app.worker.tasks"],
)

celery_app.conf.beat_schedule = {
    "dispatch-outbox": {
        "task": "app.worker.tasks.dispatch_outbox",
        "schedule": settings.OUTBOX_DISPATCH_INTERVAL,
    },
    "resend-unsent-emails": {
        "task": "app.worker.tasks.retry_unsent_emails",
        "schedule": settings.EMAIL_RESEND_INTERVAL,
    },
}
