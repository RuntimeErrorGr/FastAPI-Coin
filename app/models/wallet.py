from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Wallet(TimestampMixin, Base):
    """A user's balance in one coin. A user has at most one wallet per coin."""

    __tablename__ = "wallets"
    __table_args__ = (
        UniqueConstraint("user_id", "coin_symbol"),
        CheckConstraint("balance >= 0", name="balance_not_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    coin_symbol: Mapped[str] = mapped_column(String(10), ForeignKey("coins.symbol"))
    balance: Mapped[Decimal] = mapped_column(Numeric(28, 8), server_default="0")
