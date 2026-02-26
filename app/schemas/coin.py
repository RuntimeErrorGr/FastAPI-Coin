from enum import Enum


class CoinType(str, Enum):
    """Supported coin types."""

    BTC = "btc"
    ETH = "eth"
    XRP = "xrp"

    @property
    def coingecko_id(self) -> str:
        """Returns the CoinGecko ID for the specific coin type."""
        mapping = {
            self.BTC: "bitcoin",
            self.ETH: "ethereum",
            self.XRP: "ripple",
        }
        return mapping[self]
