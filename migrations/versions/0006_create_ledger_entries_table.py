"""create ledger entries table

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("entry_type", sa.String(length=6), nullable=False),
        sa.Column("amount", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount > 0", name=op.f("ck_ledger_entries_amount_positive")
        ),
        sa.CheckConstraint(
            "entry_type IN ('credit', 'debit')",
            name=op.f("ck_ledger_entries_entry_type_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["wallet_id"],
            ["wallets.id"],
            name=op.f("fk_ledger_entries_wallet_id_wallets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ledger_entries")),
    )
    op.create_index(
        op.f("ix_ledger_entries_wallet_id"),
        "ledger_entries",
        ["wallet_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ledger_entries_wallet_id"), table_name="ledger_entries")
    op.drop_table("ledger_entries")
