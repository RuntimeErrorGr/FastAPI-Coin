from app.exceptions import AuthenticationException
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead
from app.security import hash_password, verify_password


class UserService:
    """Business logic for user accounts."""

    def __init__(self, users: UserRepository):
        self._users = users

    async def register(self, data: UserCreate) -> UserRead:
        """Creates a new account, storing only a hash of the password."""
        return await self._users.create(data, hash_password(data.password))

    async def authenticate(self, username: str, password: str) -> UserRead:
        """Returns the user if the username and password match.

        Raises:
            AuthenticationException: if the user doesn't exist or the password is wrong.
        """
        user = await self._users.get_by_username(username)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationException("Incorrect username or password.")
        return UserRead.model_validate(user.model_dump())
