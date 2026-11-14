from datetime import timedelta

import pytest

from app.exceptions import AuthenticationException
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_is_not_the_plain_password():
    hashed = hash_password("s3cret-pass")

    assert hashed != "s3cret-pass"
    assert hashed.startswith("$argon2")


def test_verify_accepts_correct_password():
    assert verify_password("s3cret-pass", hash_password("s3cret-pass")) is True


def test_verify_rejects_wrong_password():
    assert verify_password("wrong-pass", hash_password("s3cret-pass")) is False


def test_token_carries_the_username():
    token = create_access_token("alice")

    assert decode_access_token(token) == "alice"


def test_expired_token_is_rejected():
    token = create_access_token("alice", expires_in=timedelta(seconds=-1))

    with pytest.raises(AuthenticationException):
        decode_access_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token("alice")
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}.{signature[::-1]}"

    with pytest.raises(AuthenticationException):
        decode_access_token(tampered)
