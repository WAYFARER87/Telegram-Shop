"""Admin schemas."""

from pydantic import BaseModel, Field

from app.core.enums import OrderStatus


class UpdateStockPayload(BaseModel):
    """Admin stock update payload."""

    stock_qty: int = Field(ge=0)


class UpdatePricePayload(BaseModel):
    """Admin price update payload."""

    price: float = Field(gt=0)
    old_price: float | None = None


class UpdateOrderStatusPayload(BaseModel):
    """Order status update payload."""

    status: OrderStatus
