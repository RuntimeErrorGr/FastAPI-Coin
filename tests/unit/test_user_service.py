from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.exceptions import AuthenticationException
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserInDB, UserRead
from app.security import hash_password, verify_password
from app.services.user_service import UserService

DATA = UserCreate(
    username="alice",
    email="alice@example.com",
    full_name="Alice Smith",
    password="s3cret-pass",
)

STORED = UserInDB(
    id=1,
    username="alice",
    email="alice@example.com",
    full_name="Alice Smith",
    phone=None,
    created_at=datetime.now(UTC),
    hashed_password=hash_password("s3cret-pass"),
)


@pytest.fixture
def users():
    return MagicMock(spec=UserRepository)


async def test_register_stores_a_hash_of_the_password(users):
    await UserService(users).register(DATA)

    data, hashed_password = users.create.await_args.args
    assert data == DATA
    assert hashed_password != DATA.password
    assert verify_password(DATA.password, hashed_password)


async def test_authenticate_returns_user_without_password_hash(users):
    users.get_by_username.return_value = STORED

    user = await UserService(users).authenticate("alice", "s3cret-pass")

    assert type(user) is UserRead
    assert user.username == "alice"


@pytest.mark.parametrize(
    "stored, password",
    [(STORED, "wrong-pass"), (None, "s3cret-pass")],
    ids=["wrong-password", "unknown-user"],
)
async def test_authenticate_rejects_bad_credentials(users, stored, password):
    users.get_by_username.return_value = stored

    with pytest.raises(AuthenticationException):
        await UserService(users).authenticate("alice", password)
