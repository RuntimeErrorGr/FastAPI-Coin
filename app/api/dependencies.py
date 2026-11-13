from functools import lru_cache

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.exceptions import (
    InvalidCoinException,
    OutOfBoundsAmountException,
    RateLimitException,
)
from app.log import get_logger
from app.repositories.coin_repository import CoinRepository
from app.schemas.exchange import ExchangeQueryParams
from app.services.cache_service import CacheService
from app.services.coingecko_service import CoinGeckoService
from app.services.failover_service import FailoverService

logger = get_logger(__name__)


@lru_cache
def get_failover_service():
    return FailoverService()


@lru_cache
def get_coingecko_service(failover: FailoverService = Depends(get_failover_service)):
    return CoinGeckoService(failover=failover)


@lru_cache
def get_cache_service():
    return CacheService()


def get_coin_repository(session: AsyncSession = Depends(get_db_session)):
    return CoinRepository(session)


async def validate_exchange_params(
    coin: str = Query(..., description="The coin to exchange into USD."),
    amount: float = Query(..., description="The quantity to exchange."),
    supported_coins: CoinRepository = Depends(get_coin_repository),
) -> ExchangeQueryParams:
    supported_coin = await supported_coins.get_by_symbol(coin.lower())
    if supported_coin is None:
        raise InvalidCoinException(coin=coin)

    if amount <= 0 or amount >= 10000:
        raise OutOfBoundsAmountException(amount=amount)

    return ExchangeQueryParams(coin=supported_coin, amount=amount)


async def get_exchange_rate(
    query: ExchangeQueryParams = Depends(validate_exchange_params),
    api: CoinGeckoService = Depends(get_coingecko_service),
    cache: CacheService = Depends(get_cache_service),
) -> float:
    """Gets the exchange rate for the given coin.

    1. Try to get the exchange rate from the cache.
    2. If cache is up and rate is not found, get the rate from CoinGecko API.
    3. If cache is down, check failover policy before calling CoinGecko API.
    4. If rate is fetched from API and cache is up, update the cache.
    5. Return the exchange rate.
    """
    rate = await cache.get_rate(query.coin)
    if rate is not None:
        return rate

    if not cache.is_up:
        if api.failover.should_block_request(query.coin):
            raise RateLimitException(
                "Failover policy blocks the request.",
                retry_after=api.failover.retry_after(query.coin),
            )

        logger.warning("Cache is down, proceeding without cache.")

    rate = await api.get_rate(query.coin)
    await cache.set_rate(query.coin, rate)
    return rate
