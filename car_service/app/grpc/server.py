import traceback
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.session import engine
from app.grpc import booking_pb2, booking_pb2_grpc
from app.models.availability import CarAvailability
from app.utils.kafka_producer import send_log
from app.utils.selectors.car import get_car_by_id
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

import grpc

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

SERVICE = "car_service_grpc"


class BookingServiceServicer(booking_pb2_grpc.BookingServiceServicer):
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
                    return booking_pb2.BookCarResponse(
                        success=False,
                        message="Car not found or unavailable",
                    )

                stmt = select(CarAvailability).where(CarAvailability.car_id == car.id)
                result = await session.execute(stmt)
                availabilities = result.scalars().all()

                for availability in availabilities:
                    if (
                        availability.start_date <= start
                        and availability.end_date >= end
                    ):
                        await session.delete(availability)

                        if availability.start_date < start:
                            session.add(
                                CarAvailability(
                                    car_id=car.id,
                                    start_date=availability.start_date,
                                    end_date=start - timedelta(days=1),
                                    price_per_day=availability.price_per_day,
                                )
                            )
                        if availability.end_date > end:
                            session.add(
                                CarAvailability(
                                    car_id=car.id,
                                    start_date=end + timedelta(days=1),
                                    end_date=availability.end_date,
                                    price_per_day=availability.price_per_day,
                                )
                            )

                        await session.commit()
                        log.update({"result": "success"})
                        await send_log(log)
                        return booking_pb2.BookCarResponse(
                            success=True,
                            message="Booking confirmed",
                        )

                log.update(
                    {"result": "failure", "reason": "Requested dates not available"}
                )
                await send_log(log)
                return booking_pb2.BookCarResponse(
                    success=False,
                    message="Requested dates are not available",
                )

        except Exception as e:
            tb_str = traceback.format_exc()
            log.update({"result": "failure", "error": str(e), "traceback": tb_str})
            await send_log(log)
            return booking_pb2.BookCarResponse(
                success=False,
                message="Internal error",
            )


async def serve():
    server = grpc.aio.server()
    booking_pb2_grpc.add_BookingServiceServicer_to_server(
        BookingServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{settings.GRPC_PORT}")
    print(f"🚀 gRPC Car Service running on port {settings.GRPC_PORT}")
    await server.start()
    await server.wait_for_termination()
