"""Order repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Order


class OrderRepository:
    """Order repository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, order: Order) -> Order:
        """Persist order."""

        self.session.add(order)
        await self.session.flush()
        return order

    async def list_for_user(self, user_id: int) -> list[Order]:
        """Return user orders."""

        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .order_by(Order.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_for_user(self, user_id: int, order_id: int) -> Order | None:
        """Return user order."""

        stmt = (
            select(Order)
            .where(Order.user_id == user_id, Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.payments))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get(self, order_id: int) -> Order | None:
        """Return order by id."""

        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items), selectinload(Order.payments))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Order]:
        """Return all orders."""

        result = await self.session.execute(select(Order).options(selectinload(Order.items)).order_by(Order.id.desc()))
        return list(result.scalars().unique().all())
