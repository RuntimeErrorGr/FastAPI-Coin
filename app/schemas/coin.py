from pydantic import BaseModel, ConfigDict


class CoinRead(BaseModel):
    """A supported coin, as used by the services and returned by the API."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    symbol: str
    coingecko_id: str
    name: str
