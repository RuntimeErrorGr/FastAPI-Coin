from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Transfer(Base):
    """Money moved from one wallet to another wallet of the same coin."""

    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint(
            "sender_wallet_id <> receiver_wallet_id", name="different_wallets"
        ),
        UniqueConstraint("sender_wallet_id", "idempotency_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    receiver_wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(28, 8))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
