from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import (
    AuthenticationException,
    CacheConnectionException,
    ConflictException,
    ExternalAPIException,
    InvalidCoinException,
    NotFoundException,
    OutOfBoundsAmountException,
    RateLimitException,
    TransferRejectedException,
    UserAlreadyExistsException,
)
from app.log import get_logger

logger = get_logger(__name__)


async def coin_exception_handler(_: Request, exc: InvalidCoinException):
    logger.error(f"Coin not supported: {exc.coin}")
    return JSONResponse(
        status_code=400,
        content={"error": "Coin not supported."},
    )


async def invalid_amount_exception_handler(_: Request, exc: OutOfBoundsAmountException):
    logger.error(f"Invalid amount: {exc.amount}")
    return JSONResponse(
        status_code=400,
        content={"error": "Out of bounds amount."},
    )


async def external_api_exception_handler(_: Request, exc: ExternalAPIException):
    logger.error(f"External API error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error."},
    )


async def cache_connection_exception_handler(_: Request, exc: CacheConnectionException):
    logger.error(f"Cache connection error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error."},
    )


async def failover_blocked_exception_handler(_: Request, exc: RateLimitException):
    """Cache is down and the coin was fetched recently.

    503: the client did nothing wrong, the server is degraded.
    Retry-After tells the client when the request can succeed.
    """
    logger.warning(f"Failover blocked request: {exc}")
    return JSONResponse(
        status_code=503,
        content={"error": "Service temporarily unavailable. Try again later."},
        headers={"Retry-After": str(exc.retry_after)},
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid input format or missing required parameters."},
    )


async def user_already_exists_exception_handler(
    _: Request, exc: UserAlreadyExistsException
):
    logger.warning(f"Sign-up rejected: {exc}")
    return JSONResponse(status_code=409, content={"error": exc.message})


async def authentication_exception_handler(_: Request, exc: AuthenticationException):
    logger.warning(f"Authentication failed: {exc}")
    return JSONResponse(
        status_code=401,
        content={"error": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def not_found_exception_handler(_: Request, exc: NotFoundException):
    logger.warning(f"Not found: {exc}")
    return JSONResponse(status_code=404, content={"error": exc.message})


async def conflict_exception_handler(_: Request, exc: ConflictException):
    logger.warning(f"Conflict: {exc}")
    return JSONResponse(status_code=409, content={"error": exc.message})


async def transfer_rejected_exception_handler(
    _: Request, exc: TransferRejectedException
):
    logger.warning(f"Transfer rejected: {exc}")
    return JSONResponse(status_code=400, content={"error": exc.message})


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(InvalidCoinException, coin_exception_handler)
    app.add_exception_handler(
        OutOfBoundsAmountException, invalid_amount_exception_handler
    )
    app.add_exception_handler(ExternalAPIException, external_api_exception_handler)
    app.add_exception_handler(
        CacheConnectionException, cache_connection_exception_handler
    )
    app.add_exception_handler(RateLimitException, failover_blocked_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AuthenticationException, authentication_exception_handler)
    app.add_exception_handler(
        UserAlreadyExistsException, user_already_exists_exception_handler
    )
    app.add_exception_handler(NotFoundException, not_found_exception_handler)
    app.add_exception_handler(ConflictException, conflict_exception_handler)
    app.add_exception_handler(
        TransferRejectedException, transfer_rejected_exception_handler
    )
