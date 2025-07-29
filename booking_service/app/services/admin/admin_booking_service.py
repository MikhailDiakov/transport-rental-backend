from datetime import date
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.booking import Booking
from app.utils.grpc import (
    book_car_via_grpc,
    restore_availability_via_grpc,
    validate_user_exists,
)
from app.utils.kafka_producer import send_log

SERVICE = settings.PROJECT_NAME


async def admin_create_booking(
    db: AsyncSession,
    car_id: int,
    start_date: date,
    end_date: date,
    user_id: int,
    admin_id: int,
):
    log = {
        "service": SERVICE,
        "event": "admin_create_booking",
        "admin_id": admin_id,
        "user_id": user_id,
        "car_id": car_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    try:
        user_exists = await validate_user_exists(user_id)
        if not user_exists:
            log.update({"result": "failure", "reason": "User not found"})
            await send_log(log)
            return None, "User does not exist"

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

        log.update({"result": "success", "booking_id": booking.id})
        await send_log(log)
        return booking, "Booking successfully created by admin"

    except Exception as e:
        log.update({"result": "failure", "error": str(e)})
        await send_log(log)
        return None, str(e)


async def admin_list_bookings(
    db: AsyncSession,
    only_future: bool = False,
    admin_id: Optional[int] = None,
    user_id: Optional[int] = None,
    car_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Booking]:
    log = {
        "service": SERVICE,
        "event": "admin_list_bookings",
    }
    if admin_id:
        log["admin_id"] = admin_id

    stmt = select(Booking)

    if only_future:
        today = date.today()
        stmt = stmt.where(
            and_(
                Booking.end_date >= today,
                Booking.status.notin_(["cancelled", "expired"]),
            )
        )
    if user_id is not None:
        stmt = stmt.where(Booking.user_id == user_id)

    if car_id is not None:
        stmt = stmt.where(Booking.car_id == car_id)

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    bookings = result.scalars().all()

    log.update({"result": "success", "count": len(bookings)})
    await send_log(log)

    return bookings


async def admin_get_booking(
    db: AsyncSession,
    booking_id: int,
    admin_id: int | None = None,
) -> Booking | None:
    log = {
        "service": SERVICE,
        "event": "admin_get_booking",
        "booking_id": booking_id,
    }
    if admin_id:
        log["admin_id"] = admin_id

    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking:
        log["result"] = "success"
    else:
        log["result"] = "failure"
        log["reason"] = "Booking not found"

    await send_log(log)
    return booking


async def admin_update_booking(
    db: AsyncSession,
    booking_id: int,
    update_data: dict,
    admin_id: int,
) -> Booking | None:
    log = {
        "service": SERVICE,
        "event": "admin_update_booking",
        "booking_id": booking_id,
        "admin_id": admin_id,
        "update_data": update_data,
    }

    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        log.update({"result": "failure", "reason": "Booking not found"})
        await send_log(log)
        return None

    for key, value in update_data.items():
        setattr(booking, key, value)

    await db.commit()
    await db.refresh(booking)

    log.update({"result": "success"})
    await send_log(log)

    return booking


async def admin_delete_booking(
    db: AsyncSession,
    booking_id: int,
    admin_id: int,
) -> bool:
    log = {
        "service": SERVICE,
        "event": "admin_delete_booking",
        "booking_id": booking_id,
        "admin_id": admin_id,
    }

    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if not booking:
        log.update({"result": "failure", "reason": "Booking not found"})
        await send_log(log)
        return False

    if booking.status == "cancelled":
        log.update({"result": "success", "note": "already cancelled"})
        await send_log(log)
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
        log.update({"result": "failure", "reason": grpc_response.message})
        await send_log(log)
        return False

    booking.status = "cancelled"
    await db.commit()
    await db.refresh(booking)

    log.update({"result": "success"})
    await send_log(log)
    return True
