from pydantic import BaseModel

from app.schemas.coin import CoinRead


class ExchangeQueryResponse(BaseModel):
    """Response model for the API."""

    usd_amount: float


class ExchangeQueryParams(BaseModel):
    """Internal model to hold validated query parameters."""

    coin: CoinRead
    amount: float
