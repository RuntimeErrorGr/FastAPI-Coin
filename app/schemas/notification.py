from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    """A notification as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transfer_id: int
    message: str
    created_at: datetime
    sent_at: datetime | None


class PendingEmail(BaseModel):
    """A notification whose email has not been sent yet."""

    model_config = ConfigDict(from_attributes=True)

    notification_id: int
    email: str
    message: str
