"""seed_initial_user

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-14 09:07:09.173312

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$z9XOwTyP4qi+cbW64w5LaA$GZKkJ8rF/TzRRCmNvWh0qrhFHFcKEPPA2Q1DdKdFUFU"

DEMO_USERS = [
    {
        "username": "john",
        "email": "john@example.com",
        "full_name": "John Doe",
        "phone": None,
        "hashed_password": PASSWORD_HASH,
    },
    {
        "username": "jane",
        "email": "jane@example.com",
        "full_name": "Jane Doe",
        "phone": None,
        "hashed_password": PASSWORD_HASH,
    },
]


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            INSERT INTO users (username, email, full_name, phone, hashed_password)
            VALUES (:username, :email, :full_name, :phone, :hashed_password)
            """),
        DEMO_USERS,
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM users WHERE username IN ('john', 'jane')"))
