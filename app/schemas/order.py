"""Order schemas."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DeliveryType, OrderStatus, PaymentMethod
from app.schemas.common import TimestampSchema


class CheckoutPayload(BaseModel):
    """Checkout payload used by API and bot."""

    recipient_name: str
    phone: str
    delivery_type: DeliveryType
    delivery_address: str | None = None
    comment: str | None = None
    payment_method: PaymentMethod


class OrderItemRead(BaseModel):
    """Order item read schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name_snapshot: str
    qty: int
    unit_price: Decimal
    total_price: Decimal


class OrderRead(TimestampSchema):
    """Order read schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    cart_id: int
    status: OrderStatus
    total_amount: Decimal
    currency: str
    recipient_name: str
    phone: str
    delivery_type: str
    delivery_address: str | None
    comment: str | None
    items: list[OrderItemRead] = Field(default_factory=list)
