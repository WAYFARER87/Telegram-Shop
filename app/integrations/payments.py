"""Mock payment integration."""

from uuid import uuid4

from app.config import get_settings


settings = get_settings()


class MockPaymentProvider:
    """Mock payment provider."""

    @staticmethod
    def create_payment_url(order_id: int, external_payment_id: str) -> str:
        """Generate mock payment url."""

        return f"{settings.base_url}/mock-payments/{order_id}?payment_id={external_payment_id}"

    @staticmethod
    def generate_external_id() -> str:
        """Generate external payment id."""

        return uuid4().hex
