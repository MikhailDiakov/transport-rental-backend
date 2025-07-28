from datetime import date

import grpc
from app.core.config import settings
from app.grpc import car_booking_pb2, car_booking_pb2_grpc
from app.models.booking import Booking
from app.utils.kafka_producer import send_log
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

SERVICE = settings.PROJECT_NAME


async def book_car_via_grpc(car_id: int, start: str, end: str, user_id: int):
    async with grpc.aio.insecure_channel(settings.CAR_GRPC_HOST) as channel:
        stub = car_booking_pb2_grpc.BookingServiceStub(channel)
        request = car_booking_pb2.BookCarRequest(
            car_id=car_id,
            start_date=start,
            end_date=end,
            user_id=user_id,
        )
        response = await stub.BookCar(request)
        return response


async def restore_availability_via_grpc(car_id: int, start: str, end: str):
    async with grpc.aio.insecure_channel(settings.CAR_GRPC_HOST) as channel:
        stub = car_booking_pb2_grpc.BookingServiceStub(channel)
        request = car_booking_pb2.RestoreAvailabilityRequest(
            car_id=car_id,
            start_date=start,
            end_date=end,
        )
        response = await stub.RestoreAvailability(request)
        return response


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

    grpc_response = await restore_availability_via_grpc(
        booking.car_id,
        booking.start_date.isoformat(),
        booking.end_date.isoformat(),
    )

    if not grpc_response.success:
        raise Exception(f"Failed to restore availability: {grpc_response.message}")

    await db.delete(booking)
    await db.commit()
    return True
