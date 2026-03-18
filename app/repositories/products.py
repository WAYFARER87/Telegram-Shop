"""Product repository."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Product, ProductImage


class ProductRepository:
    """Product repository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, *, category_id: int | None = None, active_only: bool = True) -> list[Product]:
        """Return products."""

        stmt = select(Product).options(selectinload(Product.images)).order_by(Product.id.desc())
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if active_only:
            stmt = stmt.where(Product.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get(self, product_id: int) -> Product | None:
        """Return product by id."""

        stmt = select(Product).options(selectinload(Product.images)).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, product: Product) -> Product:
        """Persist product."""

        self.session.add(product)
        await self.session.flush()
        return product

    async def replace_images(self, product: Product, image_urls: list[str]) -> None:
        """Replace product images."""

        await self.session.execute(
            delete(ProductImage).where(ProductImage.product_id == product.id),
        )
        self.session.add_all(
            [
                ProductImage(product_id=product.id, image_url=image_url, sort_order=index)
                for index, image_url in enumerate(image_urls)
            ]
        )
        await self.session.flush()
