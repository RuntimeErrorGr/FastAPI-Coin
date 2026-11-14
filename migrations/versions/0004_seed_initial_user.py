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


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            INSERT INTO users (username, email, full_name, phone, hashed_password)
            VALUES (:username, :email, :full_name, :phone, :hashed_password)
            """),
        {
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Administrator",
            "phone": "123-456-7890",
            "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$ca/zhEMyhczmuT+5NxlIOQ$QCtqRP9Nbv2AZaiOmpJbZfMdwGBccgDtWRqc3TdRlRk",
        },
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            DELETE FROM users WHERE username = :username
            """),
        {"username": "admin"},
    )
