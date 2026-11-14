from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException
from app.models import EntryType
from app.repositories.coin_repository import CoinRepository
from app.repositories.ledger_repository import LedgerRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.wallet import WalletRead


class WalletService:
    """Business logic for wallets."""

    def __init__(
        self,
        session: AsyncSession,
        wallets: WalletRepository,
        ledger: LedgerRepository,
        coins: CoinRepository,
    ):
        self._session = session
        self._wallets = wallets
        self._ledger = ledger
        self._coins = coins

    async def open_wallet(self, user_id: int, symbol: str) -> WalletRead:
        """Opens an empty wallet for a supported coin.

        Raises:
            NotFoundException: if the coin is not supported.
            ConflictException: if the user already has a wallet for this coin.
        """
        coin = await self._coins.get_by_symbol(symbol.lower())
        if coin is None:
            raise NotFoundException(f"Coin not supported: {symbol}.")

        wallet = await self._wallets.add(user_id, coin.symbol)
        await self._session.commit()
        return wallet

    async def list_wallets(self, user_id: int) -> list[WalletRead]:
        """Returns all wallets of the user."""
        return await self._wallets.list_for_user(user_id)

    async def deposit(self, user_id: int, symbol: str, amount: Decimal) -> WalletRead:
        """Adds funds to the user's wallet and records a ledger credit.

        Raises:
            NotFoundException: if the user has no wallet for this coin.
        """
        wallet = await self._wallets.get_for_update(user_id, symbol.lower())
        if wallet is None:
            raise NotFoundException(f"You don't have a {symbol.lower()} wallet.")

        wallet = await self._wallets.change_balance(wallet.id, amount)
        await self._ledger.record(wallet.id, EntryType.CREDIT, amount)
        await self._session.commit()
        return wallet
