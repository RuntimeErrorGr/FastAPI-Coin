from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions import TransferRejectedException
from app.repositories.ledger_repository import LedgerRepository
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.transfer_repository import TransferRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.transfer import TransferCreate
from app.schemas.user import UserInDB, UserRead
from app.schemas.wallet import WalletRead
from app.services.transfer_service import TransferService

NOW = datetime.now(UTC)
ALICE = UserRead(
    id=1,
    username="alice",
    email="alice@example.com",
    full_name="Alice",
    phone=None,
    created_at=NOW,
)
BOB = UserInDB(
    id=2,
    username="bob",
    email="bob@example.com",
    full_name="Bob",
    phone=None,
    created_at=NOW,
    hashed_password="hash",
)


def wallet(wallet_id: int, balance: str) -> WalletRead:
    return WalletRead(
        id=wallet_id, coin_symbol="btc", balance=Decimal(balance), created_at=NOW
    )


@pytest.fixture
def repositories():
    users = MagicMock(spec=UserRepository)
    users.get_by_username.return_value = BOB
    wallets = MagicMock(spec=WalletRepository)
    wallets.get_many_for_update.return_value = {
        ALICE.id: wallet(10, "1"),
        BOB.id: wallet(20, "0"),
    }
    transfers = MagicMock(spec=TransferRepository)
    transfers.get_by_idempotency_key.return_value = None
    return {
        "users": users,
        "wallets": wallets,
        "transfers": transfers,
        "ledger": MagicMock(spec=LedgerRepository),
        "outbox": MagicMock(spec=OutboxRepository),
    }


@pytest.fixture
def service(repositories):
    return TransferService(session=AsyncMock(), **repositories)


async def test_transfer_to_yourself_is_rejected_before_any_lookup(
    service, repositories
):
    data = TransferCreate(recipient="alice", coin="btc", amount=Decimal("1"))

    with pytest.raises(TransferRejectedException):
        await service.transfer(ALICE, data, "key-1")

    repositories["users"].get_by_username.assert_not_awaited()


async def test_insufficient_funds_changes_nothing(service, repositories):
    data = TransferCreate(recipient="bob", coin="btc", amount=Decimal("1.5"))

    with pytest.raises(TransferRejectedException, match="Insufficient funds"):
        await service.transfer(ALICE, data, "key-1")

    repositories["wallets"].change_balance.assert_not_awaited()
    repositories["ledger"].record.assert_not_awaited()
    repositories["transfers"].add.assert_not_awaited()
    repositories["outbox"].add.assert_not_awaited()
