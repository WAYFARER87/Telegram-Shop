"""Cart schemas."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CartStatus
from app.schemas.common import TimestampSchema
from app.schemas.product import ProductBase


class CartItemCreate(BaseModel):
    """Add item to cart payload."""

    product_id: int
    qty: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    """Update cart item quantity."""

    qty: int = Field(ge=1)


class CartItemRead(TimestampSchema):
    """Cart item read schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    qty: int
    price_snapshot: Decimal
    product: ProductBase


class CartRead(TimestampSchema):
    """Cart read schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: CartStatus
    items: list[CartItemRead] = Field(default_factory=list)
    total_amount: Decimal
