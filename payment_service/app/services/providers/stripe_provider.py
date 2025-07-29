import stripe
from app.core.config import settings
from app.models.payment import Payment, PaymentStatus
from app.services.providers.base import BasePaymentProvider
from sqlalchemy.ext.asyncio import AsyncSession

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentProvider(BasePaymentProvider):
    async def create_payment(
        self,
        db: AsyncSession,
        booking_id: int,
        user_id: int,
        amount: float,
        currency: str = "usd",
    ) -> tuple[Payment, str]:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "unit_amount": int(amount * 100),
                        "product_data": {"name": f"Booking #{booking_id}"},
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=settings.BACKEND_URL + "/payments/success",
            cancel_url=settings.BACKEND_URL + "/payments/cancel",
        )

        payment = Payment(
            booking_id=booking_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.pending,
            provider="stripe",
            provider_payment_id=session.id,
        )

        return payment, session.url
