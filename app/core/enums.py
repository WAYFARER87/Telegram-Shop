"""Shared application enums."""

from enum import StrEnum


class CartStatus(StrEnum):
    """Supported cart statuses."""

    ACTIVE = "active"
    ORDERED = "ordered"


class OrderStatus(StrEnum):
    """Supported order statuses."""

    NEW = "new"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    """Supported payment statuses."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    """Supported payment methods."""

    CASH = "cash"
    ONLINE = "online"


class DeliveryType(StrEnum):
    """Supported delivery types."""

    COURIER = "courier"
    PICKUP = "pickup"
