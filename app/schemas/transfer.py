from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.money import Money


class TransferCreate(BaseModel):
    """Request to send money to another user."""

    recipient: str = Field(min_length=1, max_length=50)
    coin: str = Field(min_length=1, max_length=10)
    amount: Decimal = Field(gt=0, max_digits=28, decimal_places=8)


class TransferRead(BaseModel):
    """A completed transfer, as seen by the sender or the recipient."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sender: str
    recipient: str
    coin: str
    amount: Money
    created_at: datetime
