from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Coin
from app.schemas.coin import CoinRead
from app.services.cache_service import CacheService


class CoinRepository:
    """Data access for supported coins."""

    def __init__(self, session: AsyncSession, cache: CacheService):
        self._session = session
        self._cache = cache

    async def get_by_symbol(self, symbol: str) -> CoinRead | None:
        """Returns the coin with the given symbol, or None if it is not supported."""
        coins = await self.get_all()

        for coin in coins:
            if coin.symbol == symbol:
                return coin
        return None

    async def get_all(self) -> list[CoinRead]:
        """Returns supported coins, from the cache when possible."""
        coins = await self._cache.get_coins()
        if coins is not None:
            return coins

        coins = await self._query_all()
        await self._cache.set_coins(coins)
        return coins

    async def _query_all(self) -> list[CoinRead]:
        rows = await self._session.scalars(select(Coin).order_by(Coin.symbol))
        return [CoinRead.model_validate(row) for row in rows]
