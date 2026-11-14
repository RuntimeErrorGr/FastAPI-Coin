from functools import lru_cache

from fastapi import Depends, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.exceptions import (
    AuthenticationException,
    InvalidCoinException,
    OutOfBoundsAmountException,
    RateLimitException,
)
from app.log import get_logger
from app.repositories.coin_repository import CoinRepository
from app.repositories.ledger_repository import LedgerRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.transfer_repository import TransferRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.exchange import ExchangeQueryParams
from app.schemas.user import UserRead
from app.security import decode_access_token
from app.services.cache_service import CacheService
from app.services.coingecko_service import CoinGeckoService
from app.services.failover_service import FailoverService
from app.services.transfer_service import TransferService
from app.services.user_service import UserService
from app.services.wallet_service import WalletService

logger = get_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


@lru_cache
def get_failover_service() -> FailoverService:
    return FailoverService()


def get_coingecko_service(request: Request) -> CoinGeckoService:
    return CoinGeckoService(request.app.state.http_client)


def get_cache_service(request: Request) -> CacheService:
    return CacheService(request.app.state.redis_client)


def get_coin_repository(
    session: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service),
) -> CoinRepository:
    return CoinRepository(session, cache)


def get_notification_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationRepository:
    return NotificationRepository(session)


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    users: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(users)


def get_wallet_service(
    session: AsyncSession = Depends(get_db_session),
    coins: CoinRepository = Depends(get_coin_repository),
) -> WalletService:
    return WalletService(
        session, WalletRepository(session), LedgerRepository(session), coins
    )


def get_transfer_service(
    session: AsyncSession = Depends(get_db_session),
    users: UserRepository = Depends(get_user_repository),
) -> TransferService:
    return TransferService(
        session,
        users,
        WalletRepository(session),
        TransferRepository(session),
        LedgerRepository(session),
        OutboxRepository(session),
    )


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    users: UserRepository = Depends(get_user_repository),
) -> UserRead:
    """Returns the user identified by the bearer token of the request.

    Raises:
        AuthenticationException: if the token is missing or invalid, or its user
            no longer exists.
    """
    if token is None:
        raise AuthenticationException("Not authenticated.")
    username = decode_access_token(token)
    user = await users.get_by_username(username)
    if user is None:
        raise AuthenticationException("Could not validate credentials.")
    return UserRead.model_validate(user.model_dump())


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
    failover: FailoverService = Depends(get_failover_service),
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
        if failover.should_block_request(query.coin):
            raise RateLimitException(
                "Failover policy blocks the request.",
                retry_after=failover.retry_after(query.coin),
            )

        logger.warning("Cache is down, proceeding without cache.")

    rate = await api.get_rate(query.coin)
    failover.record_call(query.coin)
    await cache.set_rate(query.coin, rate)
    return rate
