"""Order services."""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CartStatus, OrderStatus, PaymentMethod
from app.core.exceptions import NotFoundError, ValidationError
from app.db.models import Order, OrderItem
from app.repositories.carts import CartRepository
from app.repositories.orders import OrderRepository
from app.repositories.users import UserRepository
from app.schemas.order import CheckoutPayload
from app.services.carts import CartService


class OrderService:
    """Order business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.orders = OrderRepository(session)
        self.carts = CartRepository(session)
        self.users = UserRepository(session)

    async def create_order(self, user_id: int, payload: CheckoutPayload) -> Order:
        """Create order from active cart."""

        if await self.users.get(user_id) is None:
            raise NotFoundError("User not found")
        cart = await self.carts.get_or_create_active(user_id)
        if not cart.items:
            raise ValidationError("Cannot create order from empty cart")

        total = CartService.total(cart)
        status = OrderStatus.NEW if payload.payment_method == PaymentMethod.CASH else OrderStatus.PENDING_PAYMENT
        order = Order(
            user_id=user_id,
            cart_id=cart.id,
            status=status,
            total_amount=total,
            currency=cart.items[0].product.currency,
            recipient_name=payload.recipient_name,
            phone=payload.phone,
            delivery_type=payload.delivery_type.value,
            delivery_address=payload.delivery_address,
            comment=payload.comment,
        )
        for item in cart.items:
            order.items.append(
                OrderItem(
                    product_id=item.product_id,
                    product_name_snapshot=item.product.name,
                    qty=item.qty,
                    unit_price=item.price_snapshot,
                    total_price=item.price_snapshot * item.qty,
                )
            )
            item.product.stock_qty -= item.qty
        cart.status = CartStatus.ORDERED
        await self.orders.create(order)
        await self.session.commit()
        return await self.orders.get(order.id)

    async def list_orders(self, user_id: int) -> list[Order]:
        """Return user orders."""

        return await self.orders.list_for_user(user_id)

    async def get_order(self, user_id: int, order_id: int) -> Order:
        """Return user order."""

        order = await self.orders.get_for_user(user_id, order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    async def list_all(self) -> list[Order]:
        """Return all orders."""

        return await self.orders.list_all()

    async def update_status(self, order_id: int, status: OrderStatus) -> Order:
        """Update order status."""

        order = await self.orders.get(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        order.status = status
        await self.session.commit()
        await self.session.refresh(order)
        return order
