class ExchangeBaseException(Exception):
    """Base exception for the application errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidCoinException(ExchangeBaseException):
    """Exception raised when the coin symbol is invalid."""

    def __init__(self, coin: str):
        self.coin = coin
        super().__init__(f"Invalid coin: {coin}.")


class OutOfBoundsAmountException(ExchangeBaseException):
    """Exception raised when the provided amount is out of bounds."""

    def __init__(self, amount: float):
        self.amount = amount
        super().__init__(f"Out of bounds amount: {amount}.")


class ExternalAPIException(ExchangeBaseException):
    """Exception raised if the CoinGecko API is unreachable."""

    pass


class CacheConnectionException(ExchangeBaseException):
    """Exception raised if the cache is unreachable."""

    pass


class CacheMissException(ExchangeBaseException):
    """Exception raised if the requested data was not found in the cache."""

    pass


class RateLimitException(CacheConnectionException):
    """Exception raised if the cache is unreachable.

    An API call has been made recently for the same coin.
    Subsequent requests for the same coin will be blocked for
    a timeout period to prevent spamming the external API.
    """

    def __init__(self, message: str, retry_after: int):
        self.retry_after = retry_after
        super().__init__(message)
