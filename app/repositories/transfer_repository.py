from decimal import Decimal

from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.exceptions import ConflictException
from app.models import Transfer, User, Wallet
from app.schemas.transfer import TransferRead

SenderWallet = aliased(Wallet)
ReceiverWallet = aliased(Wallet)
Sender = aliased(User)
Receiver = aliased(User)


def _transfers_with_names() -> Select:
    """Transfers joined with the usernames and coin, the shape of TransferRead."""
    return (
        select(
            Transfer.id,
            Sender.username.label("sender"),
            Receiver.username.label("recipient"),
            SenderWallet.coin_symbol.label("coin"),
            Transfer.amount,
            Transfer.created_at,
        )
        .join(SenderWallet, Transfer.sender_wallet_id == SenderWallet.id)
        .join(Sender, SenderWallet.user_id == Sender.id)
        .join(ReceiverWallet, Transfer.receiver_wallet_id == ReceiverWallet.id)
        .join(Receiver, ReceiverWallet.user_id == Receiver.id)
    )


class TransferRepository:
    """Data access for transfers. It never commits: the service owns the transaction."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(
        self,
        sender_wallet_id: int,
        receiver_wallet_id: int,
        amount: Decimal,
        idempotency_key: str,
    ) -> int:
        """Adds a transfer to the current transaction and returns its id.

        Raises:
            ConflictException: if the sender already used this idempotency key.
        """
        transfer = Transfer(
            sender_wallet_id=sender_wallet_id,
            receiver_wallet_id=receiver_wallet_id,
            amount=amount,
            idempotency_key=idempotency_key,
        )
        self._session.add(transfer)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ConflictException("Idempotency key already used.") from e
        return transfer.id

    async def get_by_idempotency_key(
        self, sender_wallet_id: int, idempotency_key: str
    ) -> TransferRead | None:
        """Returns the transfer the sender made with this key, if any."""
        row = (
            await self._session.execute(
                _transfers_with_names().where(
                    Transfer.sender_wallet_id == sender_wallet_id,
                    Transfer.idempotency_key == idempotency_key,
                )
            )
        ).one_or_none()
        return TransferRead.model_validate(row) if row else None

    async def get(self, transfer_id: int) -> TransferRead:
        """Returns one transfer."""
        row = (
            await self._session.execute(
                _transfers_with_names().where(Transfer.id == transfer_id)
            )
        ).one()
        return TransferRead.model_validate(row)

    async def list_for_user(self, user_id: int) -> list[TransferRead]:
        """Returns the transfers the user sent or received, newest first."""
        rows = await self._session.execute(
            _transfers_with_names()
            .where(or_(Sender.id == user_id, Receiver.id == user_id))
            .order_by(Transfer.id.desc())
        )
        return [TransferRead.model_validate(row) for row in rows]
