from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EntryType, LedgerEntry


class LedgerRepository:
    """Records ledger entries. Entries are never updated or deleted."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def record(
        self,
        wallet_id: int,
        entry_type: EntryType,
        amount: Decimal,
        transfer_id: int | None = None,
    ) -> None:
        """Adds one entry to the current transaction."""
        self._session.add(
            LedgerEntry(
                wallet_id=wallet_id,
                entry_type=entry_type,
                amount=amount,
                transfer_id=transfer_id,
            )
        )
        await self._session.flush()
