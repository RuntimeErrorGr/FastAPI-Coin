from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EntryType(StrEnum):
    """Direction of a ledger entry: money into or out of a wallet."""

    CREDIT = "credit"
    DEBIT = "debit"


class LedgerEntry(Base):
    """One movement of money on a wallet. Entries are only ever inserted."""

    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("entry_type IN ('credit', 'debit')", name="entry_type_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    transfer_id: Mapped[int | None] = mapped_column(ForeignKey("transfers.id"))
    entry_type: Mapped[EntryType] = mapped_column(String(6))
    amount: Mapped[Decimal] = mapped_column(Numeric(28, 8))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
