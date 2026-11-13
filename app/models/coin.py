from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Coin(Base):
    """A coin supported by the exchange endpoint."""

    __tablename__ = "coins"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), unique=True)
    coingecko_id: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(50))
