from fastapi import APIRouter, Depends, Header, Response, status

from app.api.dependencies import get_current_user, get_transfer_service
from app.schemas.transfer import TransferCreate, TransferRead
from app.schemas.user import UserRead
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    data: TransferCreate,
    response: Response,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=100,
        description="A unique value per transfer; retries must reuse it.",
    ),
    user: UserRead = Depends(get_current_user),
    transfers: TransferService = Depends(get_transfer_service),
) -> TransferRead:
    """Sends money from your wallet to another user wallet of the same coin.

    Returns 201 for a new transfer and 200 when a retry replays an earlier one.
    """
    result = await transfers.transfer(user, data, idempotency_key)
    if not result.created:
        response.status_code = status.HTTP_200_OK
    return result.transfer


@router.get("", response_model=list[TransferRead])
async def list_transfers(
    user: UserRead = Depends(get_current_user),
    transfers: TransferService = Depends(get_transfer_service),
) -> list[TransferRead]:
    """Lists the transfers you sent or received, newest first."""
    return await transfers.list_transfers(user.id)
