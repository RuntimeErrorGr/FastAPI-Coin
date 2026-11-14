"""create transfers table

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transfers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender_wallet_id", sa.Integer(), nullable=False),
        sa.Column("receiver_wallet_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_transfers_amount_positive")),
        sa.CheckConstraint(
            "sender_wallet_id <> receiver_wallet_id",
            name=op.f("ck_transfers_different_wallets"),
        ),
        sa.ForeignKeyConstraint(
            ["receiver_wallet_id"],
            ["wallets.id"],
            name=op.f("fk_transfers_receiver_wallet_id_wallets"),
        ),
        sa.ForeignKeyConstraint(
            ["sender_wallet_id"],
            ["wallets.id"],
            name=op.f("fk_transfers_sender_wallet_id_wallets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transfers")),
    )
    op.create_index(
        op.f("ix_transfers_receiver_wallet_id"), "transfers", ["receiver_wallet_id"]
    )
    op.create_index(
        op.f("ix_transfers_sender_wallet_id"), "transfers", ["sender_wallet_id"]
    )

    op.add_column(
        "ledger_entries", sa.Column("transfer_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_ledger_entries_transfer_id_transfers"),
        "ledger_entries",
        "transfers",
        ["transfer_id"],
        ["id"],
    )

    op.create_check_constraint(
        op.f("ck_wallets_balance_not_negative"), "wallets", "balance >= 0"
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_wallets_balance_not_negative"), "wallets", type_="check"
    )
    op.drop_constraint(
        op.f("fk_ledger_entries_transfer_id_transfers"),
        "ledger_entries",
        type_="foreignkey",
    )
    op.drop_column("ledger_entries", "transfer_id")
    op.drop_index(op.f("ix_transfers_sender_wallet_id"), table_name="transfers")
    op.drop_index(op.f("ix_transfers_receiver_wallet_id"), table_name="transfers")
    op.drop_table("transfers")
