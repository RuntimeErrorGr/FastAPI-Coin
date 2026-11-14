from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_user_service
from app.schemas.user import Token
from app.security import create_access_token
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    users: UserService = Depends(get_user_service),
) -> Token:
    """Exchanges a username and password for an access token."""
    user = await users.authenticate(form.username, form.password)
    return Token(access_token=create_access_token(user.username))
