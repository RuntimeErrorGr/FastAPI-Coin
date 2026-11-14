from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Sign-up data sent by the client."""

    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    """A user as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    full_name: str
    phone: str | None
    created_at: datetime


class UserInDB(UserRead):
    """A user together with the password hash."""

    hashed_password: str


class Token(BaseModel):
    """The response of a successful login."""

    access_token: str
    token_type: str = "bearer"
