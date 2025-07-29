from app.core.config import settings
from app.models.payment import Payment
from app.models.role import RoleEnum
from app.schemas.payment import PaymentCreate
from app.services.providers.factory import get_payment_provider
from app.utils.grpc import get_booking_info
from app.utils.kafka_producer import send_log
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

SERVICE = settings.PROJECT_NAME


async def create_payment(
    db: AsyncSession, data: PaymentCreate, current_user: dict
) -> tuple[Payment, str]:
    log = {
        "service": SERVICE,
        "event": "create_payment",
        "user_id": current_user["id"],
        "booking_id": data.booking_id,
        "payment_method": data.method,
    }

    try:
        grpc_booking = await get_booking_info(data.booking_id)

        if not grpc_booking.success:
            log.update({"result": "failure", "reason": "Booking not found or invalid"})
            await send_log(log)
            raise HTTPException(status_code=400, detail="Booking not found or invalid")

        log["booking_user_id"] = grpc_booking.user_id
        log["can_pay"] = grpc_booking.can_pay
        log["booking_total_price"] = grpc_booking.total_price

        if grpc_booking.user_id != current_user["id"] and current_user["role"] not in {
            RoleEnum.SUPERADMIN,
            RoleEnum.ADMIN,
        }:
            log.update({"result": "failure", "reason": "Unauthorized user"})
            await send_log(log)
            raise HTTPException(
                status_code=403, detail="Not authorized to pay for this booking"
            )

        if not grpc_booking.can_pay:
            log.update(
                {"result": "failure", "reason": "Payment not allowed for this booking"}
            )
            await send_log(log)
            raise HTTPException(status_code=400, detail="Cannot pay for this booking")

        provider = get_payment_provider(data.method)
        payment, url = await provider.create_payment(
            db=db,
            booking_id=data.booking_id,
            user_id=current_user["id"],
            amount=grpc_booking.total_price,
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        log.update(
            {
                "result": "success",
                "payment_id": payment.id,
                "payment_provider": payment.provider,
                "payment_amount": payment.amount,
                "payment_status": payment.status,
                "payment_url": url,
            }
        )
        await send_log(log)

        return payment, url

    except Exception as e:
        log.update({"result": "error", "error": str(e)})
        await send_log({k: str(v) for k, v in log.items()})
        raise
