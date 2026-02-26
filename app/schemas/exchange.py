from pydantic import BaseModel

from app.schemas.coin import CoinType


class ExchangeQueryResponse(BaseModel):
    """Response model for the API."""

    usd_amount: float


class ExchangeQueryParams(BaseModel):
    """Internal model to hold validated query parameters."""

    coin: CoinType
    amount: float
