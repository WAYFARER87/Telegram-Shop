"""Telegram bot FSM states."""

from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    """Checkout flow states."""

    recipient_name = State()
    phone = State()
    delivery_type = State()
    delivery_address = State()
    comment = State()
    confirm = State()
    payment_method = State()
