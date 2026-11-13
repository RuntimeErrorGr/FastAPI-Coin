import math
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

    def retry_after(self, coin: CoinType) -> int:
        """Seconds until the API may be called again for the coin (0 = now)."""
        last_time = self._last_api_call.get(coin.value)
        if not last_time:
            return 0

        remaining = self._timeout - (time.time() - last_time)
        return max(0, math.ceil(remaining))

    def should_block_request(self, coin: CoinType) -> bool:
        """Checks if the API was called recently for the given coin."""
        return self.retry_after(coin) > 0

    def record_call(self, coin: CoinType) -> None:
        """Records the time of the last API call for the given coin."""
        self._last_api_call[coin.value] = time.time()
