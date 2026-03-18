"""Catalog services."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import Category, Product
from app.repositories.categories import CategoryRepository
from app.repositories.products import ProductRepository
from app.schemas.product import ProductCreate


class CatalogService:
    """Catalog business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.categories = CategoryRepository(session)
        self.products = ProductRepository(session)

    async def list_categories(self) -> list[Category]:
        """Return active categories."""

        return await self.categories.list()

    async def create_category(self, payload) -> Category:
        """Create category."""

        category = Category(
            parent_id=payload.parent_id,
            name=payload.name,
            slug=payload.slug,
            is_active=payload.is_active,
            sort_order=payload.sort_order,
        )
        await self.categories.create(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def update_category(self, category_id: int, payload) -> Category:
        """Update category."""

        category = await self.categories.get(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        category.parent_id = payload.parent_id
        category.name = payload.name
        category.slug = payload.slug
        category.is_active = payload.is_active
        category.sort_order = payload.sort_order
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete_category(self, category_id: int) -> None:
        """Delete category."""

        category = await self.categories.get(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        await self.categories.delete(category)
        await self.session.commit()

    async def list_products(self, category_id: int | None = None, active_only: bool = True) -> list[Product]:
        """Return active products."""

        return await self.products.list(category_id=category_id, active_only=active_only)

    async def get_product(self, product_id: int) -> Product:
        """Return product by id."""

        product = await self.products.get(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def create_product(self, payload: ProductCreate) -> Product:
        """Create product."""

        product = Product(
            category_id=payload.category_id,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            price=payload.price,
            old_price=payload.old_price,
            currency=payload.currency,
            stock_qty=payload.stock_qty,
            is_active=payload.is_active,
        )
        await self.products.create(product)
        await self.products.replace_images(product, payload.image_urls)
        await self.session.commit()
        return await self.get_product(product.id)

    async def update_product(self, product_id: int, payload: ProductCreate) -> Product:
        """Update product."""

        product = await self.get_product(product_id)
        product.category_id = payload.category_id
        product.name = payload.name
        product.slug = payload.slug
        product.description = payload.description
        product.price = payload.price
        product.old_price = payload.old_price
        product.currency = payload.currency
        product.stock_qty = payload.stock_qty
        product.is_active = payload.is_active
        await self.products.replace_images(product, payload.image_urls)
        await self.session.commit()
        return await self.get_product(product.id)
