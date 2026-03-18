"""Admin API routes."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.api.serializers import serialize_category_tree, serialize_order, serialize_payment, serialize_product
from app.schemas.admin import UpdateOrderStatusPayload, UpdatePricePayload, UpdateStockPayload
from app.schemas.category import CategoryCreate, CategoryTree
from app.schemas.order import OrderRead
from app.schemas.payment import PaymentRead
from app.schemas.product import ProductBase, ProductCreate
from app.services.catalog import CatalogService
from app.services.orders import OrderService
from app.services.payments import PaymentService


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/categories", response_model=list[CategoryTree])
async def admin_list_categories(session: AsyncSession = Depends(get_session)) -> list[CategoryTree]:
    """List categories."""

    categories = await CatalogService(session).list_categories()
    return serialize_category_tree(categories)


@router.post("/categories", response_model=CategoryTree, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, session: AsyncSession = Depends(get_session)) -> CategoryTree:
    """Create category."""

    category = await CatalogService(session).create_category(payload)
    return CategoryTree(
        id=category.id,
        parent_id=category.parent_id,
        name=category.name,
        slug=category.slug,
        is_active=category.is_active,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at,
        children=[],
    )


@router.put("/categories/{category_id}", response_model=CategoryTree)
async def update_category(
    category_id: int,
    payload: CategoryCreate,
    session: AsyncSession = Depends(get_session),
) -> CategoryTree:
    """Update category."""

    category = await CatalogService(session).update_category(category_id, payload)
    return CategoryTree(
        id=category.id,
        parent_id=category.parent_id,
        name=category.name,
        slug=category.slug,
        is_active=category.is_active,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at,
        children=[],
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session: AsyncSession = Depends(get_session)) -> Response:
    """Delete category."""

    await CatalogService(session).delete_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/products", response_model=list[ProductBase])
async def admin_list_products(session: AsyncSession = Depends(get_session)) -> list[ProductBase]:
    """List products."""

    products = await CatalogService(session).list_products(category_id=None, active_only=False)
    return [serialize_product(product) for product in products]


@router.post("/products", response_model=ProductBase, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, session: AsyncSession = Depends(get_session)) -> ProductBase:
    """Create product."""

    product = await CatalogService(session).create_product(payload)
    return serialize_product(product)


@router.put("/products/{product_id}", response_model=ProductBase)
async def update_product(
    product_id: int,
    payload: ProductCreate,
    session: AsyncSession = Depends(get_session),
) -> ProductBase:
    """Update product."""

    product = await CatalogService(session).update_product(product_id, payload)
    return serialize_product(product)


@router.patch("/products/{product_id}/price", response_model=ProductBase)
async def update_product_price(
    product_id: int,
    payload: UpdatePricePayload,
    session: AsyncSession = Depends(get_session),
) -> ProductBase:
    """Update product prices."""

    service = CatalogService(session)
    product = await service.get_product(product_id)
    product.price = payload.price
    product.old_price = payload.old_price
    await session.commit()
    return serialize_product(product)


@router.patch("/products/{product_id}/stock", response_model=ProductBase)
async def update_product_stock(
    product_id: int,
    payload: UpdateStockPayload,
    session: AsyncSession = Depends(get_session),
) -> ProductBase:
    """Update product stock."""

    service = CatalogService(session)
    product = await service.get_product(product_id)
    product.stock_qty = payload.stock_qty
    await session.commit()
    return serialize_product(product)


@router.get("/orders", response_model=list[OrderRead])
async def list_orders(session: AsyncSession = Depends(get_session)) -> list[OrderRead]:
    """List all orders."""

    orders = await OrderService(session).list_all()
    return [serialize_order(order) for order in orders]


@router.patch("/orders/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    payload: UpdateOrderStatusPayload,
    session: AsyncSession = Depends(get_session),
) -> OrderRead:
    """Change order status."""

    order = await OrderService(session).update_status(order_id, payload.status)
    return serialize_order(order)


@router.get("/payments", response_model=list[PaymentRead])
async def list_payments(
    session: AsyncSession = Depends(get_session),
) -> list[PaymentRead]:
    """List payments."""

    payments = await PaymentService(session).list_payments()
    return [serialize_payment(payment) for payment in payments]
