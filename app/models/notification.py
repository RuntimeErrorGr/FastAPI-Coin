from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    """A message to a user about a transfer, also sent to them by email.

    At most one per user and transfer, so handling the same event twice
    cannot notify anyone twice. `sent_at` is empty until the email went out.
    """

    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("transfer_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    transfer_id: Mapped[int] = mapped_column(ForeignKey("transfers.id"))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
