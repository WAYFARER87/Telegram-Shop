"""Telegram shop handlers."""

from decimal import Decimal
import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main import (
    cart_keyboard,
    categories_keyboard,
    checkout_confirm_keyboard,
    main_menu_keyboard,
    payment_method_keyboard,
    product_actions_keyboard,
    products_keyboard,
)
from app.bot.states import CheckoutStates
from app.core.enums import DeliveryType, PaymentMethod
from app.core.exceptions import AppError
from app.db.session import AsyncSessionLocal
from app.schemas.order import CheckoutPayload
from app.services.carts import CartService
from app.services.catalog import CatalogService
from app.services.orders import OrderService
from app.services.payments import PaymentService
from app.services.users import UserService


router = Router(name="shop")
logger = logging.getLogger(__name__)


async def render_catalog(message: Message, category_id: int | None = None) -> None:
    """Render root categories, nested categories, or products."""

    async with AsyncSessionLocal() as session:
        service = CatalogService(session)
        categories = await service.list_categories()
        products = await service.list_products(category_id=category_id) if category_id is not None else []

    current = next((category for category in categories if category.id == category_id), None)
    child_categories = [category for category in categories if category.parent_id == category_id]

    if child_categories:
        await message.edit_text(
            f"Категория: {current.name if current else 'Каталог'}",
            reply_markup=categories_keyboard(
                [(category.id, category.name) for category in child_categories],
                parent_id=current.parent_id if current else None,
                show_root_back=current is not None and current.parent_id is None,
            ),
        )
        return

    if products:
        await message.edit_text(
            f"Товары в категории: {current.name if current else 'Каталог'}",
            reply_markup=products_keyboard(
                [(product.id, product.name) for product in products],
                back_category_id=current.parent_id if current else None,
            ),
        )
        return

    roots = [category for category in categories if category.parent_id is None]
    if category_id is None:
        await message.edit_text("Каталог:", reply_markup=categories_keyboard([(category.id, category.name) for category in roots]))
    else:
        await message.edit_text(
            "В этой категории пока нет товаров.",
            reply_markup=categories_keyboard(
                [(category.id, category.name) for category in roots],
                show_root_back=False,
            ),
        )


def format_cart(cart) -> str:
    """Format cart message."""

    if not cart.items:
        return "Корзина пуста."
    lines = ["Корзина:"]
    for item in cart.items:
        lines.append(f"{item.product.name} x {item.qty} = {item.price_snapshot * item.qty} {item.product.currency}")
    total = CartService.total(cart)
    lines.append(f"Итого: {total}")
    return "\n".join(lines)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Register user and show main menu."""

    async with AsyncSessionLocal() as session:
        await UserService(session).register_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
    await message.answer(
        "Добро пожаловать в магазин. Выберите раздел.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "Каталог")
async def catalog_handler(message: Message) -> None:
    """Show root categories."""

    async with AsyncSessionLocal() as session:
        categories = await CatalogService(session).list_categories()
    roots = [(category.id, category.name) for category in categories if category.parent_id is None]
    await message.answer("Каталог:", reply_markup=categories_keyboard(roots))


@router.callback_query(F.data.startswith("cat:"))
async def category_callback(callback: CallbackQuery) -> None:
    """Show child categories or products for category."""

    category_id = int(callback.data.split(":")[1])
    await render_catalog(callback.message, category_id)
    await callback.answer()


@router.callback_query(F.data.startswith("cat_back:"))
async def category_back_callback(callback: CallbackQuery) -> None:
    """Navigate back in catalog tree."""

    raw_value = callback.data.split(":")[1]
    category_id = None if raw_value == "root" else int(raw_value)
    await render_catalog(callback.message, category_id)
    await callback.answer()


@router.callback_query(F.data.startswith("prod:"))
async def product_callback(callback: CallbackQuery) -> None:
    """Show product details."""

    product_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        product = await CatalogService(session).get_product(product_id)
    text = (
        f"{product.name}\n"
        f"Цена: {product.price} {product.currency}\n"
        f"Описание: {product.description or '-'}\n"
        f"Остаток: {product.stock_qty}"
    )
    await callback.message.edit_text(text, reply_markup=product_actions_keyboard(product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart_callback(callback: CallbackQuery) -> None:
    """Add one item to cart."""

    try:
        product_id = int(callback.data.split(":")[1])
        async with AsyncSessionLocal() as session:
            user = await UserService(session).register_telegram_user(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
            )
            cart = await CartService(session).add_item(user.id, product_id, 1)
        await callback.message.answer(
            format_cart(cart),
            reply_markup=cart_keyboard([(item.id, item.product.name) for item in cart.items]),
        )
        await callback.answer("Товар добавлен")
    except AppError as exc:
        await callback.answer(str(exc), show_alert=True)
    except Exception:
        logger.exception("Failed to add item to cart")
        await callback.answer("Не удалось добавить товар в корзину", show_alert=True)


@router.callback_query(F.data.startswith("buy:"))
async def buy_now_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Add item and start checkout."""

    try:
        product_id = int(callback.data.split(":")[1])
        async with AsyncSessionLocal() as session:
            user = await UserService(session).register_telegram_user(
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
            )
            await CartService(session).add_item(user.id, product_id, 1)
        await state.update_data(user_telegram_id=callback.from_user.id)
        await state.set_state(CheckoutStates.recipient_name)
        await callback.message.answer("Введите имя получателя:")
        await callback.answer()
    except AppError as exc:
        await callback.answer(str(exc), show_alert=True)
    except Exception:
        logger.exception("Failed to start buy-now flow")
        await callback.answer("Не удалось начать оформление заказа", show_alert=True)


@router.message(F.text == "Корзина")
async def cart_handler(message: Message) -> None:
    """Show cart."""

    async with AsyncSessionLocal() as session:
        user = await UserService(session).register_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        cart = await CartService(session).get_cart(user.id)
    await message.answer(format_cart(cart), reply_markup=cart_keyboard([(item.id, item.product.name) for item in cart.items]))


@router.callback_query(F.data == "cart_clear")
async def clear_cart_callback(callback: CallbackQuery) -> None:
    """Clear cart."""

    async with AsyncSessionLocal() as session:
        user = await UserService(session).register_telegram_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
        )
        cart = await CartService(session).clear(user.id)
    await callback.message.answer(format_cart(cart))
    await callback.answer()


@router.callback_query(F.data.startswith("cart_"))
async def cart_item_callback(callback: CallbackQuery) -> None:
    """Update cart item."""

    action, item_id_raw = callback.data.split(":")
    item_id = int(item_id_raw)
    async with AsyncSessionLocal() as session:
        user = await UserService(session).register_telegram_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
        )
        service = CartService(session)
        cart = await service.get_cart(user.id)
        item = next((item for item in cart.items if item.id == item_id), None)
        if item is None:
            await callback.answer("Позиция не найдена", show_alert=True)
            return
        if action == "cart_del":
            cart = await service.delete_item(user.id, item_id)
        elif action == "cart_inc":
            cart = await service.update_item(user.id, item_id, item.qty + 1)
        else:
            if item.qty == 1:
                cart = await service.delete_item(user.id, item_id)
            else:
                cart = await service.update_item(user.id, item_id, item.qty - 1)
    await callback.message.answer(format_cart(cart), reply_markup=cart_keyboard([(item.id, item.product.name) for item in cart.items]))
    await callback.answer()


@router.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Start checkout FSM."""

    await state.update_data(user_telegram_id=callback.from_user.id)
    await state.set_state(CheckoutStates.recipient_name)
    await callback.message.answer("Введите имя получателя:")
    await callback.answer()


@router.message(CheckoutStates.recipient_name)
async def checkout_recipient(message: Message, state: FSMContext) -> None:
    """Collect recipient name."""

    await state.update_data(recipient_name=message.text)
    await state.set_state(CheckoutStates.phone)
    await message.answer("Введите телефон:")


@router.message(CheckoutStates.phone)
async def checkout_phone(message: Message, state: FSMContext) -> None:
    """Collect phone."""

    await state.update_data(phone=message.text)
    await state.set_state(CheckoutStates.delivery_type)
    await message.answer("Выберите тип доставки: courier или pickup")


@router.message(CheckoutStates.delivery_type)
async def checkout_delivery_type(message: Message, state: FSMContext) -> None:
    """Collect delivery type."""

    value = (message.text or "").strip().lower()
    if value not in {DeliveryType.COURIER.value, DeliveryType.PICKUP.value}:
        await message.answer("Введите courier или pickup")
        return
    await state.update_data(delivery_type=value)
    await state.set_state(CheckoutStates.delivery_address)
    await message.answer("Введите адрес доставки или '-' для самовывоза:")


@router.message(CheckoutStates.delivery_address)
async def checkout_delivery_address(message: Message, state: FSMContext) -> None:
    """Collect address."""

    value = None if message.text == "-" else message.text
    await state.update_data(delivery_address=value)
    await state.set_state(CheckoutStates.comment)
    await message.answer("Комментарий к заказу или '-':")


@router.message(CheckoutStates.comment)
async def checkout_comment(message: Message, state: FSMContext) -> None:
    """Collect comment."""

    value = None if message.text == "-" else message.text
    await state.update_data(comment=value)
    data = await state.get_data()
    summary = (
        f"Проверьте данные:\n"
        f"Получатель: {data['recipient_name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Доставка: {data['delivery_type']}\n"
        f"Адрес: {data.get('delivery_address') or '-'}\n"
        f"Комментарий: {value or '-'}"
    )
    await state.set_state(CheckoutStates.confirm)
    await message.answer(summary, reply_markup=checkout_confirm_keyboard())


@router.callback_query(CheckoutStates.confirm, F.data == "checkout_cancel")
async def checkout_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel checkout."""

    await state.clear()
    await callback.message.answer("Оформление отменено.")
    await callback.answer()


@router.callback_query(CheckoutStates.confirm, F.data == "checkout_confirm")
async def checkout_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Proceed to payment selection."""

    await state.set_state(CheckoutStates.payment_method)
    await callback.message.answer("Выберите способ оплаты:", reply_markup=payment_method_keyboard())
    await callback.answer()


@router.callback_query(CheckoutStates.payment_method, F.data.startswith("pay:"))
async def checkout_payment(callback: CallbackQuery, state: FSMContext) -> None:
    """Create order and payment."""

    method = callback.data.split(":")[1]
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        user = await UserService(session).register_telegram_user(
            telegram_id=data["user_telegram_id"],
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
        )
        order = await OrderService(session).create_order(
            user.id,
            CheckoutPayload(
                recipient_name=data["recipient_name"],
                phone=data["phone"],
                delivery_type=DeliveryType(data["delivery_type"]),
                delivery_address=data.get("delivery_address"),
                comment=data.get("comment"),
                payment_method=PaymentMethod(method),
            ),
        )
        text = f"Заказ #{order.id} создан на сумму {Decimal(order.total_amount)} {order.currency}."
        if method == PaymentMethod.ONLINE.value:
            payment = await PaymentService(session).create_payment(order.id, PaymentMethod.ONLINE)
            text += f"\nОплатить: {payment.payment_url}"
    await state.clear()
    await callback.message.answer(text)
    await callback.answer()


@router.message(F.text == "Мои заказы")
async def orders_handler(message: Message) -> None:
    """Show orders."""

    async with AsyncSessionLocal() as session:
        user = await UserService(session).register_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        orders = await OrderService(session).list_orders(user.id)
    if not orders:
        await message.answer("Заказов пока нет.")
        return
    lines = ["Ваши заказы:"]
    for order in orders:
        lines.append(f"#{order.id} | {order.status} | {order.total_amount} {order.currency}")
    await message.answer("\n".join(lines))


@router.message(F.text == "Поддержка")
async def support_handler(message: Message) -> None:
    """Show support info."""

    await message.answer("Поддержка: support@example.com")
