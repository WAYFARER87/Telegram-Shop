"""Payment services."""

from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.enums import OrderStatus, PaymentMethod, PaymentStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.db.models import Payment
from app.integrations.payments import MockPaymentProvider
from app.repositories.orders import OrderRepository
from app.repositories.payments import PaymentRepository


settings = get_settings()


class PaymentService:
    """Payment business logic."""

    def __init__(self, session: AsyncSession, redis: Redis | None = None) -> None:
        self.session = session
        self.redis = redis
        self.orders = OrderRepository(session)
        self.payments = PaymentRepository(session)

    async def create_payment(self, order_id: int, method: PaymentMethod) -> Payment:
        """Create payment for order."""

        order = await self.orders.get(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        if method == PaymentMethod.CASH:
            raise ValidationError("Cash payments do not require payment link")

        external_id = MockPaymentProvider.generate_external_id()
        payment = Payment(
            order_id=order.id,
            provider=settings.payment_provider,
            method=method,
            amount=order.total_amount,
            currency=order.currency,
            status=PaymentStatus.PENDING,
            payment_url=MockPaymentProvider.create_payment_url(order.id, external_id),
            external_payment_id=external_id,
        )
        await self.payments.create(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def list_payments(self) -> list[Payment]:
        """Return all payments."""

        return await self.payments.list_all()

    async def handle_webhook(self, external_payment_id: str, status: PaymentStatus) -> Payment:
        """Handle payment webhook idempotently."""

        payment = await self.payments.get_by_external_id(external_payment_id)
        if payment is None:
            raise NotFoundError("Payment not found")
        if self.redis is None:
            raise ValidationError("Redis client is required for webhook handling")

        lock_key = f"payment:webhook:{external_payment_id}:{status.value}"
        was_set = await self.redis.set(lock_key, "1", ex=300, nx=True)
        if not was_set:
            return payment

        if payment.status == status:
            return payment

        payment.status = status
        if status == PaymentStatus.PAID:
            payment.paid_at = datetime.now(UTC)
            order = await self.orders.get(payment.order_id)
            if order is not None:
                order.status = OrderStatus.PAID
        await self.session.commit()
        await self.session.refresh(payment)
        return payment
