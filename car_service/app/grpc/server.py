import traceback
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.session import engine
from app.grpc import car_booking_pb2, car_booking_pb2_grpc
from app.models.availability import CarAvailability
from app.utils.kafka_producer import send_log
from app.utils.selectors.car import get_car_by_id
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

import grpc

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
SERVICE = str(settings.PROJECT_NAME + "_grpc")


def _overlaps_or_adjacent(a, b):
    return a.end_date + timedelta(
        days=1
    ) >= b.start_date and a.start_date <= b.end_date + timedelta(days=1)


class BookingServiceServicer(car_booking_pb2_grpc.BookingServiceServicer):
    async def BookCar(self, request, context):
        log = {
            "service": SERVICE,
            "event": "BookCar",
            "car_id": request.car_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "user_id": request.user_id,
        }

        try:
            start = datetime.fromisoformat(request.start_date).date()
            end = datetime.fromisoformat(request.end_date).date()
            if end < start:
                raise ValueError("End date cannot be before start date")

            async with SessionLocal() as session:
                car = await get_car_by_id(session, request.car_id)
                if not car or not car.is_available:
                    log.update({"result": "failure", "reason": "Car not available"})
                    await send_log(log)
                    return car_booking_pb2.BookCarResponse(
                        success=False, message="Car not found or unavailable"
                    )

                stmt = select(CarAvailability).where(CarAvailability.car_id == car.id)
                result = await session.execute(stmt)
                availabilities = sorted(
                    result.scalars().all(), key=lambda x: x.start_date
                )

                collected = []
                total_days = 0
                total_price = 0
                current = start

                for avail in availabilities:
                    if avail.end_date < current:
                        continue
                    if avail.start_date > current:
                        break

                    segment_start = max(avail.start_date, current)
                    segment_end = min(avail.end_date, end)

                    if segment_start <= segment_end:
                        days = (segment_end - segment_start).days + 1
                        total_days += days
                        total_price += days * avail.price_per_day
                        collected.append((avail, segment_start, segment_end))
                        current = segment_end + timedelta(days=1)

                    if current > end:
                        break

                if current <= end:
                    log.update(
                        {"result": "failure", "reason": "Requested dates not available"}
                    )
                    await send_log(log)
                    return car_booking_pb2.BookCarResponse(
                        success=False, message="Requested dates are not available"
                    )

                for avail, s, e in collected:
                    await session.delete(avail)
                    if avail.start_date < s:
                        session.add(
                            CarAvailability(
                                car_id=car.id,
                                start_date=avail.start_date,
                                end_date=s - timedelta(days=1),
                                price_per_day=avail.price_per_day,
                            )
                        )
                    if avail.end_date > e:
                        session.add(
                            CarAvailability(
                                car_id=car.id,
                                start_date=e + timedelta(days=1),
                                end_date=avail.end_date,
                                price_per_day=avail.price_per_day,
                            )
                        )

                await session.commit()
                log.update({"result": "success", "total_price": total_price})
                await send_log(log)
                return car_booking_pb2.BookCarResponse(
                    success=True, message="Booking confirmed", total_price=total_price
                )

        except Exception as e:
            tb_str = traceback.format_exc()
            log.update({"result": "failure", "error": str(e), "traceback": tb_str})
            await send_log(log)
            return car_booking_pb2.BookCarResponse(
                success=False, message="Internal error"
            )

    async def RestoreAvailability(self, request, context):
        log = {
            "service": SERVICE,
            "event": "RestoreAvailability",
            "car_id": request.car_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "price_per_day": request.price_per_day,
        }

        try:
            start = datetime.fromisoformat(request.start_date).date()
            end = datetime.fromisoformat(request.end_date).date()

            if end < start:
                raise ValueError("End date cannot be before start date")

            price_per_day = request.price_per_day
            if price_per_day <= 0:
                raise ValueError("Invalid price_per_day")

            async with SessionLocal() as session:
                stmt = select(CarAvailability).where(
                    CarAvailability.car_id == request.car_id
                )
                result = await session.execute(stmt)
                slots = result.scalars().all()

                merged_start = start
                merged_end = end

                for slot in slots:
                    if slot.price_per_day != price_per_day:
                        continue
                    if _overlaps_or_adjacent(
                        slot,
                        CarAvailability(start_date=merged_start, end_date=merged_end),
                    ):
                        merged_start = min(merged_start, slot.start_date)
                        merged_end = max(merged_end, slot.end_date)
                        await session.delete(slot)

                session.add(
                    CarAvailability(
                        car_id=request.car_id,
                        start_date=merged_start,
                        end_date=merged_end,
                        price_per_day=price_per_day,
                    )
                )

                await session.commit()
                log.update({"result": "success"})
                await send_log(log)
                return car_booking_pb2.RestoreAvailabilityResponse(
                    success=True, message="Availability restored successfully"
                )

        except Exception as e:
            tb_str = traceback.format_exc()
            log.update({"result": "failure", "error": str(e), "traceback": tb_str})
            await send_log(log)
            return car_booking_pb2.RestoreAvailabilityResponse(
                success=False, message=f"Failed: {str(e)}"
            )


async def serve():
    server = grpc.aio.server()
    car_booking_pb2_grpc.add_BookingServiceServicer_to_server(
        BookingServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{settings.GRPC_PORT}")
    log = {
        "service": SERVICE,
        "event": "start_server",
        "message": f"gRPC Car Service running on port {settings.GRPC_PORT}",
    }
    await send_log(log)
    await server.start()
    await server.wait_for_termination()
