"""Bot keyboards."""

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Return main menu keyboard."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Каталог"), KeyboardButton(text="Корзина")],
            [KeyboardButton(text="Мои заказы"), KeyboardButton(text="Поддержка")],
        ],
        resize_keyboard=True,
    )


def categories_keyboard(
    categories: list[tuple[int, str]],
    parent_id: int | None = None,
    *,
    show_root_back: bool = False,
) -> InlineKeyboardMarkup:
    """Inline keyboard for categories."""

    builder = InlineKeyboardBuilder()
    for category_id, name in categories:
        builder.button(text=name, callback_data=f"cat:{category_id}")
    if parent_id is not None:
        builder.button(text="Назад", callback_data=f"cat_back:{parent_id}")
    elif show_root_back:
        builder.button(text="В корень каталога", callback_data="cat_back:root")
    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(products: list[tuple[int, str]], back_category_id: int | None = None) -> InlineKeyboardMarkup:
    """Inline keyboard for products."""

    builder = InlineKeyboardBuilder()
    for product_id, name in products:
        builder.button(text=name, callback_data=f"prod:{product_id}")
    if back_category_id is not None:
        builder.button(text="Назад", callback_data=f"cat_back:{back_category_id}")
    else:
        builder.button(text="В корень каталога", callback_data="cat_back:root")
    builder.adjust(1)
    return builder.as_markup()


def product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for product actions."""

    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить в корзину", callback_data=f"add:{product_id}")
    builder.button(text="Купить сразу", callback_data=f"buy:{product_id}")
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Inline keyboard for cart actions."""

    builder = InlineKeyboardBuilder()
    for item_id, name in items:
        builder.button(text=f"+ {name}", callback_data=f"cart_inc:{item_id}")
        builder.button(text=f"- {name}", callback_data=f"cart_dec:{item_id}")
        builder.button(text=f"Удалить {name}", callback_data=f"cart_del:{item_id}")
    builder.button(text="Очистить корзину", callback_data="cart_clear")
    builder.button(text="Оформить заказ", callback_data="checkout")
    builder.adjust(1)
    return builder.as_markup()


def checkout_confirm_keyboard() -> InlineKeyboardMarkup:
    """Checkout confirm keyboard."""

    builder = InlineKeyboardBuilder()
    builder.button(text="Подтвердить", callback_data="checkout_confirm")
    builder.button(text="Отменить", callback_data="checkout_cancel")
    builder.adjust(1)
    return builder.as_markup()


def payment_method_keyboard() -> InlineKeyboardMarkup:
    """Payment method keyboard."""

    builder = InlineKeyboardBuilder()
    builder.button(text="Наличными", callback_data="pay:cash")
    builder.button(text="Онлайн", callback_data="pay:online")
    builder.adjust(1)
    return builder.as_markup()
