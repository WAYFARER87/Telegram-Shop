"""Cart services."""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.db.models import Cart, CartItem
from app.repositories.carts import CartRepository
from app.repositories.products import ProductRepository
from app.repositories.users import UserRepository


class CartService:
    """Cart business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.carts = CartRepository(session)
        self.products = ProductRepository(session)
        self.users = UserRepository(session)

    async def get_cart(self, user_id: int) -> Cart:
        """Return user's active cart."""

        if await self.users.get(user_id) is None:
            raise NotFoundError("User not found")
        cart = await self.carts.get_or_create_active(user_id)
        return cart

    async def add_item(self, user_id: int, product_id: int, qty: int) -> Cart:
        """Add item to cart or increase quantity."""

        cart = await self.get_cart(user_id)
        product = await self.products.get(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        if not product.is_active:
            raise ValidationError("Cannot add inactive product")
        if product.stock_qty <= 0:
            raise ValidationError("Product is out of stock")

        existing = await self.carts.get_item_by_cart_product(cart.id, product_id)
        next_qty = qty if existing is None else existing.qty + qty
        if next_qty > product.stock_qty:
            raise ValidationError("Requested quantity exceeds stock")
        if existing is None:
            await self.carts.create_item(
                cart_id=cart.id,
                product_id=product.id,
                qty=qty,
                price_snapshot=product.price,
            )
        else:
            existing.qty = next_qty
            existing.price_snapshot = product.price
        await self.session.commit()
        return await self.carts.get_or_create_active(user_id)

    async def update_item(self, user_id: int, item_id: int, qty: int) -> Cart:
        """Update cart item quantity."""

        cart = await self.get_cart(user_id)
        item = next((item for item in cart.items if item.id == item_id), None)
        if item is None:
            raise NotFoundError("Cart item not found")
        if qty > item.product.stock_qty:
            raise ValidationError("Requested quantity exceeds stock")
        item.qty = qty
        await self.session.commit()
        return await self.carts.get_or_create_active(user_id)

    async def delete_item(self, user_id: int, item_id: int) -> Cart:
        """Delete cart item."""

        cart = await self.get_cart(user_id)
        item = next((item for item in cart.items if item.id == item_id), None)
        if item is None:
            raise NotFoundError("Cart item not found")
        await self.carts.delete_item(item)
        await self.session.commit()
        return await self.carts.get_or_create_active(user_id)

    async def clear(self, user_id: int) -> Cart:
        """Clear cart."""

        cart = await self.get_cart(user_id)
        for item in list(cart.items):
            await self.carts.delete_item(item)
        await self.session.commit()
        return await self.carts.get_or_create_active(user_id)

    @staticmethod
    def total(cart: Cart) -> Decimal:
        """Calculate cart total."""

        return sum((item.price_snapshot * item.qty for item in cart.items), start=Decimal("0.00"))
