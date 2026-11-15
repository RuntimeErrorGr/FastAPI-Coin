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
        if data.recipient == sender.username:
            raise TransferRejectedException("You cannot transfer to yourself.")

        recipient = await self._users.get_by_username(data.recipient)
        if recipient is None:
            raise NotFoundException(f"User not found: {data.recipient}.")

        wallets = await self._wallets.get_many_for_update(
            [sender.id, recipient.id], coin
        )
        if sender.id not in wallets:
            raise NotFoundException(f"You don't have a {coin} wallet.")
        if recipient.id not in wallets:
            raise NotFoundException(f"{recipient.username} has no {coin} wallet.")

        sender_wallet, recipient_wallet = wallets[sender.id], wallets[recipient.id]
        previous = await self._transfers.get_by_idempotency_key(
            sender_wallet.id, idempotency_key
        )
        if previous is not None:
            if (previous.recipient, previous.coin, previous.amount) != (
                recipient.username,
                coin,
                data.amount,
            ):
                raise ConflictException(
                    "Idempotency key already used for a different transfer."
                )
            return TransferResult(previous, created=False)

        if sender_wallet.balance < data.amount:
            raise TransferRejectedException("Insufficient funds.")

        transfer_id = await self._transfers.add(
            sender_wallet.id, recipient_wallet.id, data.amount, idempotency_key
        )
        await self._wallets.change_balance(sender_wallet.id, -data.amount)
        await self._wallets.change_balance(recipient_wallet.id, data.amount)
        await self._ledger.record(
            sender_wallet.id, EntryType.DEBIT, data.amount, transfer_id
        )
        await self._ledger.record(
            recipient_wallet.id, EntryType.CREDIT, data.amount, transfer_id
        )
        transfer = await self._transfers.get(transfer_id)
        await self._outbox.add(
            EventType.TRANSFER_COMPLETED,
            {
                "transfer_id": transfer.id,
                "sender_id": sender.id,
                "recipient_id": recipient.id,
                "coin": transfer.coin,
                "amount": format(transfer.amount, "f"),
            },
        )
        await self._session.commit()
        return TransferResult(transfer, created=True)

    async def list_transfers(self, user_id: int) -> list[TransferRead]:
        """Returns the transfers the user sent or received."""
        return await self._transfers.list_for_user(user_id)
