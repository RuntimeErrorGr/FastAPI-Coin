import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_fixed,
)

from app.config import settings
from app.exceptions import ExternalAPIException
from app.log import get_logger
from app.schemas.coin import CoinRead
from app.services.failover_service import FailoverService

logger = get_logger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    """Retry only on transient failures: network errors, 5xx and 429."""
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status >= 500 or status == 429
    return False


class CoinGeckoService:
    """Service to interact with the CoinGecko API."""

    def __init__(self, failover: FailoverService):
        self.client = httpx.AsyncClient(
            base_url=settings.EXTERNAL_API_URL,
            timeout=settings.EXTERNAL_API_TIMEOUT,
        )
        self.failover = failover

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(settings.EXTERNAL_API_TIMEOUT),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    async def _fetch_rate(self, coin: CoinRead) -> float:
        response = await self.client.get(
            "",
            params={
                "ids": coin.coingecko_id,
                "vs_currencies": "usd",
            },
        )
        response.raise_for_status()
        data = response.json()
        logger.debug(f"CoinGecko response data: {data}")

        rate = data.get(coin.coingecko_id, {}).get("usd")
        if not rate:
            raise ExternalAPIException(f"Rate not found for coin: {coin.symbol}")

        return float(rate)

    async def get_rate(self, coin: CoinRead) -> float:
        """Attempts to get the exchange rate from CoinGecko API."""
        try:
            rate = await self._fetch_rate(coin)
        except httpx.HTTPError as e:
            raise ExternalAPIException(
                "Failed to fetch data from CoinGecko API."
            ) from e

        self.failover.record_call(coin)
        return rate
