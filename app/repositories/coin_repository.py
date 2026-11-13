from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Coin
from app.schemas.coin import CoinRead


class CoinRepository:
    """Data access for supported coins."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_symbol(self, symbol: str) -> CoinRead | None:
        """Returns the coin with the given symbol, or None if it is not supported."""
        coin = await self._session.scalar(select(Coin).where(Coin.symbol == symbol))
        return CoinRead.model_validate(coin) if coin else None
