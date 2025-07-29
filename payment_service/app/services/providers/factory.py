from app.schemas.payment import PaymentMethod
from app.services.providers.base import BasePaymentProvider
from app.services.providers.stripe_provider import StripePaymentProvider


def get_payment_provider(method: PaymentMethod) -> BasePaymentProvider:
    if method == PaymentMethod.stripe:
        return StripePaymentProvider()
    raise ValueError(f"Unsupported payment method: {method}")
