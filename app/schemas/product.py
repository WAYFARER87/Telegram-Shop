"""Product schemas."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampSchema


class ProductImageSchema(BaseModel):
    """Product image schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    sort_order: int


class ProductBase(TimestampSchema):
    """Product read schema."""

    id: int
    category_id: int
    name: str
    slug: str
    description: str | None
    price: Decimal
    old_price: Decimal | None
    currency: str
    stock_qty: int
    is_active: bool
    images: list[ProductImageSchema] = Field(default_factory=list)


class ProductCreate(BaseModel):
    """Product create/update payload."""

    category_id: int
    name: str
    slug: str
    description: str | None = None
    price: Decimal
    old_price: Decimal | None = None
    currency: str = "RUB"
    stock_qty: int = 0
    is_active: bool = True
    image_urls: list[str] = Field(default_factory=list)
