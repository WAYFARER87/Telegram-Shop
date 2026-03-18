"""Payment schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.enums import PaymentMethod, PaymentStatus
from app.schemas.common import TimestampSchema


class PaymentCreate(BaseModel):
    """Create payment payload."""

    method: PaymentMethod


class PaymentWebhookPayload(BaseModel):
    """Payment webhook payload."""

    external_payment_id: str
    status: PaymentStatus


class PaymentRead(TimestampSchema):
    """Payment read schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    provider: str
    method: PaymentMethod
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_url: str | None
    external_payment_id: str | None
    paid_at: datetime | None
