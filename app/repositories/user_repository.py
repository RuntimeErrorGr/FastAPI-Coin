from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import UserAlreadyExistsException
from app.models import User
from app.schemas.user import UserCreate, UserInDB, UserRead


class UserRepository:
    """Data access for users."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: UserCreate, hashed_password: str) -> UserRead:
        """Stores a new user.

        Raises:
            UserAlreadyExistsException: if the username or email is already taken.
        """
        user = User(
            **data.model_dump(exclude={"password"}), hashed_password=hashed_password
        )
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            raise UserAlreadyExistsException() from e

        await self._session.refresh(user)
        return UserRead.model_validate(user)

    async def get_by_username(self, username: str) -> UserInDB | None:
        """Returns the user with the given username, including the password hash."""
        user = await self._session.scalar(select(User).where(User.username == username))
        return UserInDB.model_validate(user) if user else None
