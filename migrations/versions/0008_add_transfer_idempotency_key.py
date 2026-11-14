"""add transfer idempotency key

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transfers",
        sa.Column("idempotency_key", sa.String(length=100), nullable=True),
    )
    op.execute("UPDATE transfers SET idempotency_key = 'legacy-' || id")
    op.alter_column("transfers", "idempotency_key", nullable=False)
    op.create_unique_constraint(
        op.f("uq_transfers_sender_wallet_id"),
        "transfers",
        ["sender_wallet_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq_transfers_sender_wallet_id"), "transfers", type_="unique"
    )
    op.drop_column("transfers", "idempotency_key")
