from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.money import Money


class WalletCreate(BaseModel):
    """Request to open a wallet for one coin."""

    coin: str = Field(min_length=1, max_length=10)


class DepositCreate(BaseModel):
    """Request to add funds to a wallet."""

    amount: Decimal = Field(gt=0, max_digits=28, decimal_places=8)


class WalletRead(BaseModel):
    """A wallet as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    coin: str = Field(validation_alias="coin_symbol")
    balance: Money
    created_at: datetime
