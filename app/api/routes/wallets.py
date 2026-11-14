from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_wallet_service
from app.schemas.user import UserRead
from app.schemas.wallet import DepositCreate, WalletCreate, WalletRead
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("", response_model=WalletRead, status_code=status.HTTP_201_CREATED)
async def open_wallet(
    data: WalletCreate,
    user: UserRead = Depends(get_current_user),
    wallets: WalletService = Depends(get_wallet_service),
) -> WalletRead:
    """Opens an empty wallet for one coin."""
    return await wallets.open_wallet(user.id, data.coin)


@router.get("", response_model=list[WalletRead])
async def list_wallets(
    user: UserRead = Depends(get_current_user),
    wallets: WalletService = Depends(get_wallet_service),
) -> list[WalletRead]:
    """Lists the wallets of the logged-in user."""
    return await wallets.list_wallets(user.id)


@router.post("/{coin}/deposit", response_model=WalletRead)
async def deposit(
    coin: str,
    data: DepositCreate,
    user: UserRead = Depends(get_current_user),
    wallets: WalletService = Depends(get_wallet_service),
) -> WalletRead:
    """Adds funds to one of your wallets."""
    return await wallets.deposit(user.id, coin, data.amount)
