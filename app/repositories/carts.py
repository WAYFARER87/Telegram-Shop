"""Cart repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.enums import CartStatus
from app.db.models import Cart, CartItem, Product


class CartRepository:
    """Cart repository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_for_user(self, user_id: int) -> Cart | None:
        """Return active cart."""

        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE)
            .options(
                selectinload(Cart.items).joinedload(CartItem.product).selectinload(Product.images),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_active(self, user_id: int) -> Cart:
        """Return active cart or create it."""

        cart = await self.get_active_for_user(user_id)
        if cart is None:
            cart = Cart(user_id=user_id, status=CartStatus.ACTIVE)
            self.session.add(cart)
            await self.session.flush()
        return cart

    async def get_item(self, item_id: int) -> CartItem | None:
        """Return cart item by id."""

        stmt = select(CartItem).options(joinedload(CartItem.product)).where(CartItem.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_item_by_cart_product(self, cart_id: int, product_id: int) -> CartItem | None:
        """Return cart item by cart and product ids."""

        stmt = (
            select(CartItem)
            .options(joinedload(CartItem.product))
            .where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_item(self, *, cart_id: int, product_id: int, qty: int, price_snapshot) -> CartItem:
        """Create cart item."""

        item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            qty=qty,
            price_snapshot=price_snapshot,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def delete_item(self, item: CartItem) -> None:
        """Delete cart item."""

        await self.session.delete(item)
