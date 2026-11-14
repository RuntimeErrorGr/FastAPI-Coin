from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Coin
from app.schemas.coin import CoinRead
from app.services.cache_service import CacheService


class CoinRepository:
    """Data access for supported coins."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        cache: CacheService,
    ):
        self._session_factory = session_factory
        self._cache = cache

    async def get_by_symbol(self, symbol: str) -> CoinRead | None:
        """Returns the coin with the given symbol, or None if it is not supported."""
        coins = await self.get_all()
        return next((coin for coin in coins if coin.symbol == symbol), None)

    async def get_all(self) -> list[CoinRead]:
        """Returns supported coins, from the cache when possible."""
        coins = await self._cache.get_coins()
        if coins is not None:
            return coins

        coins = await self._query_all()
        await self._cache.set_coins(coins)
        return coins

    async def _query_all(self) -> list[CoinRead]:
        async with self._session_factory() as session:
            rows = await session.scalars(select(Coin).order_by(Coin.symbol))
            return [CoinRead.model_validate(row) for row in rows]
