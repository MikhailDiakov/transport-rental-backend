from typing import Optional

from app.models.payment import Payment
from app.utils.kafka_producer import send_log
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

SERVICE = "payment_service"


async def admin_list_payments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    admin_id: Optional[int] = None,
) -> list[Payment]:
    log = {
        "service": SERVICE,
        "event": "admin_list_payments",
        "admin_id": admin_id,
    }

    stmt = select(Payment).offset(skip).limit(limit)
    result = await db.execute(stmt)
    payments = result.scalars().all()

    log.update({"result": "success", "count": len(payments)})
    await send_log(log)

    return payments


async def admin_get_payment(
    db: AsyncSession,
    payment_id: int,
    admin_id: Optional[int] = None,
) -> Optional[Payment]:
    log = {
        "service": SERVICE,
        "event": "admin_get_payment",
        "payment_id": payment_id,
        "admin_id": admin_id,
    }

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if payment:
        log["result"] = "success"
    else:
        log.update({"result": "failure", "reason": "Payment not found"})

    await send_log(log)
    return payment


async def admin_update_payment_status(
    db: AsyncSession,
    payment_id: int,
    new_status: str,
    admin_id: Optional[int] = None,
) -> Optional[Payment]:
    log = {
        "service": SERVICE,
        "event": "admin_update_payment_status",
        "payment_id": payment_id,
        "new_status": new_status,
        "admin_id": admin_id,
    }

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        log.update({"result": "failure", "reason": "Payment not found"})
        await send_log(log)
        return None

    payment.status = new_status
    await db.commit()
    await db.refresh(payment)

    log["result"] = "success"
    await send_log(log)
    return payment
