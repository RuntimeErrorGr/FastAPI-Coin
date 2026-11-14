from fastapi import APIRouter, Depends

from app.api.dependencies import get_coin_repository
from app.repositories.coin_repository import CoinRepository
from app.schemas.coin import CoinRead

router = APIRouter(prefix="/coins", tags=["coins"])


@router.get("", response_model=list[CoinRead])
async def list_coins(
    coins: CoinRepository = Depends(get_coin_repository),
) -> list[CoinRead]:
    """Lists every supported coin."""
    return await coins.get_all()
