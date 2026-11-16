"""create wallets table

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("coin_symbol", sa.String(length=10), nullable=False),
        sa.Column(
            "balance",
            sa.Numeric(precision=28, scale=8),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["coin_symbol"],
            ["coins.symbol"],
            name=op.f("fk_wallets_coin_symbol_coins"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_wallets_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wallets")),
        sa.UniqueConstraint("user_id", "coin_symbol", name=op.f("uq_wallets_user_id")),
    )
    op.execute(
        sa.text("""
            INSERT INTO wallets (user_id, coin_symbol)
            SELECT users.id, coins.symbol FROM users CROSS JOIN coins
            WHERE users.username IN ('john', 'jane') AND coins.symbol IN ('usd', 'btc')
            """)
    )


def downgrade() -> None:
    op.drop_table("wallets")
