import time

from app.config import settings
from app.schemas.coin import CoinType


class FailoverService:
    """Service to track external API calls in local memory.

    Used to prevent API spamming when cache is down.
    """

    def __init__(self):
        self._last_api_call: dict[str, float] = {}
        self._timeout = settings.REDIS_CACHE_EXPIRE

    def should_block_request(self, coin: CoinType) -> bool:
        """Checks if the API was called recently for the given coin."""
        last_time = self._last_api_call.get(coin.value)
        if not last_time:
            return False

        return (time.time() - last_time) < self._timeout

    def record_call(self, coin: CoinType) -> None:
        """Records the time of the last API call for the given coin."""
        self._last_api_call[coin.value] = time.time()
