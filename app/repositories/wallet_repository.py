from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictException
from app.models import Wallet
from app.schemas.wallet import WalletRead


class WalletRepository:
    """Data access for wallets. It never commits: the service owns the transaction."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, user_id: int, coin_symbol: str) -> WalletRead:
        """Opens an empty wallet.

        Raises:
            ConflictException: if the user already has a wallet for this coin.
        """
        wallet = Wallet(user_id=user_id, coin_symbol=coin_symbol)
        self._session.add(wallet)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ConflictException(f"You already have a {coin_symbol} wallet.") from e

        await self._session.refresh(wallet)
        return WalletRead.model_validate(wallet)

    async def list_for_user(self, user_id: int) -> list[WalletRead]:
        wallets = await self._session.scalars(
            select(Wallet).where(Wallet.user_id == user_id).order_by(Wallet.coin_symbol)
        )
        return [WalletRead.model_validate(wallet) for wallet in wallets]

    async def get_for_update(self, user_id: int, coin_symbol: str) -> WalletRead | None:
        """Returns the user's wallet for the coin and locks its row until commit.

        Other transactions that want to lock the same wallet wait so balance
        changes on one wallet happen one after another.
        """
        wallet = await self._session.scalar(
            select(Wallet)
            .where(Wallet.user_id == user_id, Wallet.coin_symbol == coin_symbol)
            .with_for_update()
        )
        return WalletRead.model_validate(wallet) if wallet else None

    async def change_balance(self, wallet_id: int, delta: Decimal) -> WalletRead:
        wallet = await self._session.scalar(
            update(Wallet)
            .where(Wallet.id == wallet_id)
            .values(balance=Wallet.balance + delta)
            .returning(Wallet)
            .execution_options(populate_existing=True)
        )
        return WalletRead.model_validate(wallet)

    async def get_many_for_update(
        self, user_ids: list[int], coin_symbol: str
    ) -> dict[int, WalletRead]:
        """Locks the coin's wallets of several users, by user id.

        Rows are locked in wallet id order. Two transfers between the same
        wallets therefore always lock them in the same order and cannot
        deadlock by each waiting for the other.
        """
        wallets = await self._session.scalars(
            select(Wallet)
            .where(Wallet.user_id.in_(user_ids), Wallet.coin_symbol == coin_symbol)
            .order_by(Wallet.id)
            .with_for_update()
        )
        return {wallet.user_id: WalletRead.model_validate(wallet) for wallet in wallets}
