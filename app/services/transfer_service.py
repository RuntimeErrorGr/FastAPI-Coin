from datetime import datetime
from decimal import Decimal
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ConflictException,
    NotFoundException,
    TransferRejectedException,
)
from app.models import EntryType, EventType
from app.repositories.ledger_repository import LedgerRepository
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.transfer_repository import TransferRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.transfer import TransferCreate, TransferRead
from app.schemas.user import UserRead
from app.schemas.wallet import WalletRead


class TransferResult(NamedTuple):
    """A transfer and whether this request created it (False for a replay)."""

    transfer: TransferRead
    created: bool


class TransferService:
    """Moves money between users' wallets."""

    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        wallets: WalletRepository,
        transfers: TransferRepository,
        ledger: LedgerRepository,
        outbox: OutboxRepository,
    ):
        self._session = session
        self._users = users
        self._wallets = wallets
        self._transfers = transfers
        self._ledger = ledger
        self._outbox = outbox

    async def transfer(
        self, sender: UserRead, data: TransferCreate, idempotency_key: str
    ) -> TransferResult:
        """Sends money in one database transaction: all of it happens or none.

        A retry with the same idempotency key returns the original transfer
        instead of sending the money again.

        Raises:
            TransferRejectedException: for a transfer to yourself or without funds.
            NotFoundException: if the recipient or one of the wallets doesn't exist.
            ConflictException: if the key was already used for a different transfer.
        """
        coin = data.coin.lower()
        recipient = await self._get_recipient(sender, data.recipient)
        sender_wallet, recipient_wallet = await self._lock_wallets(
            sender, recipient, coin
        )

        previous = await self._find_previous(
            sender_wallet.id, idempotency_key, recipient.username, coin, data.amount
        )
        if previous is not None:
            return TransferResult(previous, created=False)

        if sender_wallet.balance < data.amount:
            raise TransferRejectedException("Insufficient funds.")

        transfer_id, created_at = await self._move_money(
            sender_wallet.id, recipient_wallet.id, data.amount, idempotency_key
        )
        await self._add_completed_event(
            transfer_id, sender.id, recipient.id, coin, data.amount
        )
        await self._session.commit()

        return TransferResult(
            TransferRead(
                id=transfer_id,
                sender=sender.username,
                recipient=recipient.username,
                coin=coin,
                amount=data.amount,
                created_at=created_at,
            ),
            created=True,
        )

    async def _get_recipient(self, sender: UserRead, username: str) -> UserRead:
        """Returns the recipient, who must exist and be someone else."""
        if username == sender.username:
            raise TransferRejectedException("You cannot transfer to yourself.")

        recipient = await self._users.get_by_username(username)
        if recipient is None:
            raise NotFoundException(f"User not found: {username}.")
        return recipient

    async def _lock_wallets(
        self, sender: UserRead, recipient: UserRead, coin: str
    ) -> tuple[WalletRead, WalletRead]:
        """Locks both users' wallets of the coin and returns (sender's, recipient's)."""
        wallets = await self._wallets.get_many_for_update(
            [sender.id, recipient.id], coin
        )
        if sender.id not in wallets:
            raise NotFoundException(f"You don't have a {coin} wallet.")
        if recipient.id not in wallets:
            raise NotFoundException(f"{recipient.username} has no {coin} wallet.")
        return wallets[sender.id], wallets[recipient.id]

    async def _find_previous(
        self,
        sender_wallet_id: int,
        idempotency_key: str,
        recipient: str,
        coin: str,
        amount: Decimal,
    ) -> TransferRead | None:
        """Returns the transfer already made with this key, if any.

        Raises:
            ConflictException: if that transfer differs from this request.
        """
        previous = await self._transfers.get_by_idempotency_key(
            sender_wallet_id, idempotency_key
        )
        if previous is not None and (
            previous.recipient,
            previous.coin,
            previous.amount,
        ) != (recipient, coin, amount):
            raise ConflictException(
                "Idempotency key already used for a different transfer."
            )
        return previous

    async def _move_money(
        self,
        sender_wallet_id: int,
        recipient_wallet_id: int,
        amount: Decimal,
        idempotency_key: str,
    ) -> tuple[int, datetime]:
        """Saves the transfer, both balances and the two ledger entries."""
        transfer_id, created_at = await self._transfers.add(
            sender_wallet_id, recipient_wallet_id, amount, idempotency_key
        )
        await self._wallets.change_balance(sender_wallet_id, -amount)
        await self._wallets.change_balance(recipient_wallet_id, amount)
        await self._ledger.record(
            sender_wallet_id, EntryType.DEBIT, amount, transfer_id
        )
        await self._ledger.record(
            recipient_wallet_id, EntryType.CREDIT, amount, transfer_id
        )
        return transfer_id, created_at

    async def _add_completed_event(
        self,
        transfer_id: int,
        sender_id: int,
        recipient_id: int,
        coin: str,
        amount: Decimal,
    ) -> None:
        """Adds the transfer.completed event to the outbox, in this transaction."""
        await self._outbox.add(
            EventType.TRANSFER_COMPLETED,
            {
                "transfer_id": transfer_id,
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "coin": coin,
                "amount": format(amount, ".8f"),
            },
        )

    async def list_transfers(self, user_id: int) -> list[TransferRead]:
        """Returns the transfers the user sent or received."""
        return await self._transfers.list_for_user(user_id)
