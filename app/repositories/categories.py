"""Category repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Category


class CategoryRepository:
    """Category repository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, *, active_only: bool = True) -> list[Category]:
        """Return categories."""

        stmt = select(Category).options(selectinload(Category.children)).order_by(Category.sort_order, Category.id)
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get(self, category_id: int) -> Category | None:
        """Return category by id."""

        return await self.session.get(Category, category_id)

    async def create(self, category: Category) -> Category:
        """Persist category."""

        self.session.add(category)
        await self.session.flush()
        return category

    async def delete(self, category: Category) -> None:
        """Delete category."""

        await self.session.delete(category)
