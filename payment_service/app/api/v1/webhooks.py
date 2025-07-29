import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.config import settings
from app.models.payment import Payment, PaymentStatus
from app.utils.grpc import get_user_info, update_booking_status
from app.utils.kafka_producer import send_log, send_notification_email

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY
SERVICE = settings.PROJECT_NAME


@router.post("/stripe/webhook/", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    log = {
        "service": SERVICE,
        "event": "stripe_webhook",
        "event_type": None,
        "provider": "stripe",
    }

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        log.update({"result": "failure", "reason": "Invalid signature"})
        await send_log(log)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        )

    log["event_type"] = event["type"]

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        provider_payment_id = session_data["id"]
        log["provider_payment_id"] = provider_payment_id

        stmt = select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        result = await db.execute(stmt)
        payment: Payment = result.scalar_one_or_none()

        if not payment:
            log.update({"result": "failure", "reason": "Payment not found"})
            await send_log(log)
            raise HTTPException(status_code=404, detail="Payment not found")

        log["payment_id"] = payment.id
        log["booking_id"] = payment.booking_id
        log["current_status"] = payment.status

        if payment.status != PaymentStatus.succeeded:
            payment.status = PaymentStatus.succeeded
            await db.commit()

            await update_booking_status(payment.booking_id, "paid")
            log["booking_status_updated"] = "paid"

            user_response = await get_user_info(payment.user_id)
            if user_response:
                subject = "Payment Confirmation"
                body = (
                    f"Hello {user_response.username},\n\n"
                    f"We've received your payment for booking #{payment.booking_id}.\n"
                    f"Total paid: ${payment.amount:.2f}\n\n"
                    f"Thank you for choosing our service!"
                )
                await send_notification_email(
                    to_email=user_response.email,
                    subject=subject,
                    body=body,
                )
                log["email_sent"] = True
            else:
                log["email_sent"] = False
                log["reason"] = "User info not found"

        log.update({"result": "success"})
        await send_log(log)

    else:
        log.update({"result": "ignored", "reason": "Unhandled event type"})
        await send_log(log)

    return {"status": "ok"}
