"""Response serialization helpers."""

from app.db.models import Cart, Category, Order, Payment, Product
from app.schemas.cart import CartRead
from app.schemas.category import CategoryTree
from app.schemas.order import OrderRead
from app.schemas.payment import PaymentRead
from app.schemas.product import ProductBase
from app.services.carts import CartService


def serialize_category_tree(categories: list[Category]) -> list[CategoryTree]:
    """Serialize categories as tree."""

    by_parent: dict[int | None, list[Category]] = {}
    for category in categories:
        by_parent.setdefault(category.parent_id, []).append(category)

    def build(node: Category) -> CategoryTree:
        return CategoryTree(
            id=node.id,
            parent_id=node.parent_id,
            name=node.name,
            slug=node.slug,
            is_active=node.is_active,
            sort_order=node.sort_order,
            created_at=node.created_at,
            updated_at=node.updated_at,
            children=[build(child) for child in by_parent.get(node.id, [])],
        )

    return [build(root) for root in by_parent.get(None, [])]


def serialize_cart(cart: Cart) -> CartRead:
    """Serialize cart."""

    return CartRead(
        id=cart.id,
        user_id=cart.user_id,
        status=cart.status,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        items=cart.items,
        total_amount=CartService.total(cart),
    )


def serialize_product(product: Product) -> ProductBase:
    """Serialize product."""

    return ProductBase.model_validate(product)


def serialize_order(order: Order) -> OrderRead:
    """Serialize order."""

    return OrderRead.model_validate(order)


def serialize_payment(payment: Payment) -> PaymentRead:
    """Serialize payment."""

    return PaymentRead.model_validate(payment)
