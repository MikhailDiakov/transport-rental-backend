from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.booking import Booking
from app.utils.grpc import (
    book_car_via_grpc,
    get_user_info,
    restore_availability_via_grpc,
)
from app.utils.kafka_producer import send_log, send_notification_email

SERVICE = settings.PROJECT_NAME


async def create_booking(
    db: AsyncSession, car_id: int, start_date: date, end_date: date, user_id: int
):
    log = {
        "service": SERVICE,
        "event": "create_booking",
        "user_id": user_id,
        "car_id": car_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    try:
        grpc_response = await book_car_via_grpc(
            car_id, start_date.isoformat(), end_date.isoformat(), user_id
        )
        if not grpc_response.success:
            log.update({"result": "failure", "reason": grpc_response.message})
            await send_log(log)
            return None, grpc_response.message

        booking = Booking(
            user_id=user_id,
            car_id=car_id,
            start_date=start_date,
            end_date=end_date,
            total_price=grpc_response.total_price,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        user_response = await get_user_info(user_id)
        if user_response:
            subject = "Booking Confirmation"
            body = (
                f"Hello {user_response.username},\n\n"
                f"Your booking for car #{car_id} from {start_date} to {end_date} "
                f"was successful.\n\nTotal price: ${grpc_response.total_price:.2f}\n\n"
                f"Thank you for using our service!"
            )
            await send_notification_email(
                to_email=user_response.email,
                subject=subject,
                body=body,
            )

        log.update({"result": "success", "booking_id": booking.id})
        await send_log(log)
        return booking, "Booking successful"

    except Exception as e:
        log.update({"result": "error", "error": str(e)})
        await send_log({k: str(v) for k, v in log.items()})
        return None, "Internal error"


async def get_user_bookings(
    db: AsyncSession, user_id: int, only_future=False
) -> list[Booking]:
    stmt = select(Booking).where(Booking.user_id == user_id)
    if only_future:
        today = date.today()
        stmt = stmt.where(
            and_(
                Booking.end_date >= today,
                Booking.status.notin_(["cancelled", "expired"]),
            )
        )
    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_user_booking(db: AsyncSession, booking_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        return False

    if booking.status == "cancelled":
        return True

    price_per_day = booking.total_price / (
        (booking.end_date - booking.start_date).days + 1
    )

    grpc_response = await restore_availability_via_grpc(
        booking.car_id,
        booking.start_date.isoformat(),
        booking.end_date.isoformat(),
        price_per_day=price_per_day,
    )

    if not grpc_response.success:
        raise Exception(f"Failed to restore availability: {grpc_response.message}")

    booking.status = "cancelled"
    await db.commit()
    await db.refresh(booking)
    return True
