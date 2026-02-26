from fastapi import APIRouter, Depends

from app.api.dependencies import get_exchange_rate, validate_exchange_params
from app.schemas.exchange import ExchangeQueryParams, ExchangeQueryResponse

router = APIRouter()


@router.get("/exchange", response_model=ExchangeQueryResponse)
async def get_exchange_info(
    query: ExchangeQueryParams = Depends(validate_exchange_params),
    rate: float = Depends(get_exchange_rate),
):
    return {"usd_amount": round(rate * query.amount, 2)}
