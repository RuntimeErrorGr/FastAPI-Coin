import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from app.config import settings
from app.exceptions import ExternalAPIException
from app.log import get_logger
from app.schemas.coin import CoinType
from app.services.failover_service import FailoverService

logger = get_logger(__name__)


class CoinGeckoService:
    """Service to interact with the CoinGecko API."""

    def __init__(self, failover: FailoverService):
        self.client = httpx.AsyncClient(
            base_url=settings.EXTERNAL_API_URL,
            timeout=settings.EXTERNAL_API_TIMEOUT,
        )
        self.failover = failover

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(settings.EXTERNAL_API_TIMEOUT),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    async def _get_rate(self, coin: CoinType) -> float:
        try:
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
                raise ExternalAPIException(f"Rate not found for coin: {coin.value}")

            return float(rate)
        except (httpx.HTTPError, RetryError) as e:
            raise ExternalAPIException(
                "Failed to fetch data from CoinGecko API."
            ) from e

    async def get_rate(self, coin: CoinType) -> float:
        """Attempts to get the exchange rate from CoinGecko API."""
        rate = await self._get_rate(coin)
        self.failover.record_call(coin)
        return rate
