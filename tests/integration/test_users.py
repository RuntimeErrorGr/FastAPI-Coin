import pytest
from sqlalchemy import select

from app.models import User
from app.security import verify_password
from tests.users import ALICE


async def test_sign_up_creates_user(http_client):
    response = await http_client.post("/users", json=ALICE)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert body["id"] > 0
    assert "created_at" in body
    assert "password" not in body
    assert "hashed_password" not in body


async def test_sign_up_stores_only_a_password_hash(http_client, db_session):
    await http_client.post("/users", json=ALICE)

    user = await db_session.scalar(select(User).where(User.username == "alice"))

    assert user.hashed_password != ALICE["password"]
    assert verify_password(ALICE["password"], user.hashed_password)


@pytest.mark.parametrize(
    "duplicate",
    [
        {**ALICE, "email": "other@example.com"},
        {**ALICE, "username": "other"},
    ],
    ids=["same-username", "same-email"],
)
async def test_sign_up_rejects_taken_username_or_email(http_client, duplicate):
    await http_client.post("/users", json=ALICE)

    response = await http_client.post("/users", json=duplicate)

    assert response.status_code == 409
    assert response.json() == {"error": "Username or email already registered."}


@pytest.mark.parametrize(
    "invalid",
    [
        {**ALICE, "email": "not-an-email"},
        {**ALICE, "password": "short"},
        {**ALICE, "username": "no spaces!"},
        {key: value for key, value in ALICE.items() if key != "full_name"},
    ],
    ids=["bad-email", "short-password", "bad-username", "missing-field"],
)
async def test_sign_up_rejects_invalid_data(http_client, invalid):
    response = await http_client.post("/users", json=invalid)

    assert response.status_code == 422


async def test_me_returns_the_logged_in_user(http_client, alice, alice_headers):
    response = await http_client.get("/users/me", headers=alice_headers)

    assert response.status_code == 200
    assert response.json() == alice


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer not-a-real-token"}],
    ids=["no-token", "invalid-token"],
)
async def test_me_rejects_requests_without_a_valid_token(http_client, headers):
    response = await http_client.get("/users/me", headers=headers)

    assert response.status_code == 401
    assert "error" in response.json()
    assert response.headers["WWW-Authenticate"] == "Bearer"
