"""Payment repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Payment


class PaymentRepository:
    """Payment repository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, payment: Payment) -> Payment:
        """Persist payment."""

        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_external_id(self, external_payment_id: str) -> Payment | None:
        """Return payment by external id."""

        result = await self.session.execute(
            select(Payment).where(Payment.external_payment_id == external_payment_id),
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Payment]:
        """Return all payments."""

        result = await self.session.execute(select(Payment).order_by(Payment.id.desc()))
        return list(result.scalars().all())
