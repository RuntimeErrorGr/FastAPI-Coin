import pytest

from app.security import decode_access_token
from tests.users import ALICE


async def test_login_returns_a_bearer_token_for_the_user(http_client, alice):
    form = {"username": ALICE["username"], "password": ALICE["password"]}

    response = await http_client.post("/auth/token", data=form)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert decode_access_token(body["access_token"]) == "alice"


@pytest.mark.parametrize(
    "form",
    [
        {"username": "alice", "password": "wrong-pass"},
        {"username": "nobody", "password": "s3cret-pass"},
    ],
    ids=["wrong-password", "unknown-user"],
)
async def test_login_rejects_bad_credentials(http_client, alice, form):
    response = await http_client.post("/auth/token", data=form)

    assert response.status_code == 401
    assert response.json() == {"error": "Incorrect username or password."}
    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_seeded_admin_can_log_in(http_client):
    form = {"username": "admin", "password": "admin1234"}

    response = await http_client.post("/auth/token", data=form)

    assert response.status_code == 200
