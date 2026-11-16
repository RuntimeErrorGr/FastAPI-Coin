"""seed initial coins

Revision ID: 0002

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

coins = sa.table(
    "coins",
    sa.column("symbol", sa.String),
    sa.column("coingecko_id", sa.String),
    sa.column("name", sa.String),
)

INITIAL_COINS = [
    {"symbol": "btc", "coingecko_id": "bitcoin", "name": "Bitcoin"},
    {"symbol": "eth", "coingecko_id": "ethereum", "name": "Ethereum"},
    {"symbol": "xrp", "coingecko_id": "ripple", "name": "XRP"},
    {"symbol": "usd", "coingecko_id": "usd", "name": "US Dollar"},
]


def upgrade() -> None:
    op.bulk_insert(coins, INITIAL_COINS)


def downgrade() -> None:
    symbols = [coin["symbol"] for coin in INITIAL_COINS]
    op.execute(coins.delete().where(coins.c.symbol.in_(symbols)))
