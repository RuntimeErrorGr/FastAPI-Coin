from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_user_service
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def sign_up(
    data: UserCreate,
    users: UserService = Depends(get_user_service),
) -> UserRead:
    """Creates a new user account."""
    return await users.register(data)


@router.get("/me", response_model=UserRead)
async def read_current_user(user: UserRead = Depends(get_current_user)) -> UserRead:
    """Returns the account of the logged-in user."""
    return user
