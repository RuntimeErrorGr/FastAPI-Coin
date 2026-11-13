"""create coins table

Revision ID: 0001

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "coins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("coingecko_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_coins")),
        sa.UniqueConstraint("coingecko_id", name=op.f("uq_coins_coingecko_id")),
        sa.UniqueConstraint("symbol", name=op.f("uq_coins_symbol")),
    )


def downgrade() -> None:
    op.drop_table("coins")
