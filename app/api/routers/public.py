"""Public API routes."""

from fastapi import APIRouter, Depends, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_redis, get_session
from app.api.serializers import (
    serialize_cart,
    serialize_category_tree,
    serialize_order,
    serialize_payment,
    serialize_product,
)
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.schemas.category import CategoryTree
from app.schemas.order import CheckoutPayload, OrderRead
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentWebhookPayload
from app.schemas.product import ProductBase
from app.schemas.user import TelegramUserPayload, UserRead
from app.services.carts import CartService
from app.services.catalog import CatalogService
from app.services.orders import OrderService
from app.services.payments import PaymentService
from app.services.users import UserService


router = APIRouter(prefix="/api", tags=["public"])


@router.post("/users/telegram", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: TelegramUserPayload,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Register or update telegram user."""

    user = await UserService(session).register_telegram_user(
        telegram_id=payload.telegram_id,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
    )
    return UserRead.model_validate(user)


@router.get("/categories", response_model=list[CategoryTree])
async def list_categories(session: AsyncSession = Depends(get_session)) -> list[CategoryTree]:
    """Return active categories tree."""

    categories = await CatalogService(session).list_categories()
    return serialize_category_tree(categories)


@router.get("/products", response_model=list[ProductBase])
async def list_products(
    category_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[ProductBase]:
    """Return products."""

    products = await CatalogService(session).list_products(category_id=category_id)
    return [serialize_product(product) for product in products]


@router.get("/products/{product_id}", response_model=ProductBase)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)) -> ProductBase:
    """Return product details."""

    product = await CatalogService(session).get_product(product_id)
    return serialize_product(product)


@router.get("/cart/{user_id}", response_model=CartRead)
async def get_cart(user_id: int, session: AsyncSession = Depends(get_session)) -> CartRead:
    """Return active cart."""

    cart = await CartService(session).get_cart(user_id)
    return serialize_cart(cart)


@router.post("/cart/{user_id}/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    user_id: int,
    payload: CartItemCreate,
    session: AsyncSession = Depends(get_session),
) -> CartRead:
    """Add item to cart."""

    cart = await CartService(session).add_item(user_id, payload.product_id, payload.qty)
    return serialize_cart(cart)


@router.patch("/cart/{user_id}/items/{item_id}", response_model=CartRead)
async def update_cart_item(
    user_id: int,
    item_id: int,
    payload: CartItemUpdate,
    session: AsyncSession = Depends(get_session),
) -> CartRead:
    """Update cart item quantity."""

    cart = await CartService(session).update_item(user_id, item_id, payload.qty)
    return serialize_cart(cart)


@router.delete("/cart/{user_id}/items/{item_id}", response_model=CartRead)
async def delete_cart_item(
    user_id: int,
    item_id: int,
    session: AsyncSession = Depends(get_session),
) -> CartRead:
    """Delete cart item."""

    cart = await CartService(session).delete_item(user_id, item_id)
    return serialize_cart(cart)


@router.delete("/cart/{user_id}/clear", response_model=CartRead)
async def clear_cart(user_id: int, session: AsyncSession = Depends(get_session)) -> CartRead:
    """Clear cart."""

    cart = await CartService(session).clear(user_id)
    return serialize_cart(cart)


@router.post("/orders/{user_id}", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    user_id: int,
    payload: CheckoutPayload,
    session: AsyncSession = Depends(get_session),
) -> OrderRead:
    """Create order from cart."""

    order = await OrderService(session).create_order(user_id, payload)
    return serialize_order(order)


@router.get("/orders/{user_id}", response_model=list[OrderRead])
async def list_orders(user_id: int, session: AsyncSession = Depends(get_session)) -> list[OrderRead]:
    """Return user orders."""

    orders = await OrderService(session).list_orders(user_id)
    return [serialize_order(order) for order in orders]


@router.get("/orders/{user_id}/{order_id}", response_model=OrderRead)
async def get_order(user_id: int, order_id: int, session: AsyncSession = Depends(get_session)) -> OrderRead:
    """Return user order details."""

    order = await OrderService(session).get_order(user_id, order_id)
    return serialize_order(order)


@router.post("/payments/{order_id}", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    order_id: int,
    payload: PaymentCreate,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> PaymentRead:
    """Create payment."""

    payment = await PaymentService(session, redis).create_payment(order_id, payload.method)
    return serialize_payment(payment)


@router.post("/payments/webhook", response_model=PaymentRead)
async def payment_webhook(
    payload: PaymentWebhookPayload,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> PaymentRead:
    """Handle payment provider webhook."""

    payment = await PaymentService(session, redis).handle_webhook(payload.external_payment_id, payload.status)
    return serialize_payment(payment)


@router.get("/health", status_code=status.HTTP_200_OK)
async def healthcheck() -> dict[str, str]:
    """Simple healthcheck."""

    return {"status": "ok"}


@router.delete("/noop", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def noop() -> Response:
    """No-op endpoint used in tests if needed."""

    return Response(status_code=status.HTTP_204_NO_CONTENT)
