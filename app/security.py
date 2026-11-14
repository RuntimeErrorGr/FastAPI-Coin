from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import settings
from app.exceptions import AuthenticationException

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Returns an Argon2 hash of the password, safe to store in the database."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Checks a plain password against a stored hash."""
    return password_hash.verify(password, hashed_password)


def create_access_token(
    username: str,
    expires_in: timedelta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
) -> str:
    """Returns a signed JWT that identifies the user until it expires."""
    payload = {"sub": username, "exp": datetime.now(UTC) + expires_in}
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> str:
    """Returns the username stored in a valid token.

    Raises:
        AuthenticationException: if the token is malformed, tampered with or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.InvalidTokenError as e:
        raise AuthenticationException("Could not validate credentials.") from e
    return payload["sub"]
