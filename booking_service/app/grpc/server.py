import traceback

import grpc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import settings
from app.db.session import engine
from app.grpc import booking_payment_pb2, booking_payment_pb2_grpc
from app.models.booking import Booking
from app.utils.kafka_producer import send_log

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
SERVICE = f"{settings.PROJECT_NAME}_grpc"


class BookingPaymentServiceServicer(
    booking_payment_pb2_grpc.BookingPaymentServiceServicer
):
    async def GetBookingForPayment(self, request, context):
        log = {
            "service": SERVICE,
            "event": "GetBookingForPayment",
            "booking_id": request.booking_id,
        }
        try:
            async with SessionLocal() as session:
                stmt = select(Booking).where(Booking.id == request.booking_id)
                result = await session.execute(stmt)
                booking = result.scalar_one_or_none()

                if not booking:
                    msg = "Booking not found"
                    log.update({"result": "failure", "reason": msg})
                    await send_log(log)
                    return booking_payment_pb2.GetBookingForPaymentResponse(
                        success=False,
                        message=msg,
                    )

                disallowed_statuses = ["cancelled", "expired", "refunded"]

                can_pay = (
                    booking.status not in disallowed_statuses
                    and booking.status != "paid"
                    and booking.status != "confirmed"
                )
                msg = (
                    "Booking can be paid"
                    if can_pay
                    else f"Booking status is ({booking.status}), payment not allowed"
                )

                log.update(
                    {
                        "result": "success",
                        "status": booking.status,
                        "can_pay": can_pay,
                        "total_price": booking.total_price,
                    }
                )
                await send_log(log)

                return booking_payment_pb2.GetBookingForPaymentResponse(
                    success=True,
                    message=msg,
                    booking_id=booking.id,
                    total_price=booking.total_price,
                    status=booking.status,
                    can_pay=can_pay,
                    user_id=booking.user_id,
                )

        except Exception as e:
            tb_str = traceback.format_exc()
            log.update({"result": "failure", "error": str(e), "traceback": tb_str})
            await send_log(log)
            return booking_payment_pb2.GetBookingForPaymentResponse(
                success=False,
                message="Internal server error",
            )

    async def UpdateBookingPaymentStatus(self, request, context):
        log = {
            "service": SERVICE,
            "event": "UpdateBookingPaymentStatus",
            "booking_id": request.booking_id,
            "new_status": request.new_status,
        }

        allowed_statuses = {
            "pending",
            "partially_paid",
            "paid",
            "confirmed",
            "cancelled",
            "refunded",
            "expired",
        }

        if request.new_status not in allowed_statuses:
            msg = f"Invalid status '{request.new_status}'"
            log.update({"result": "failure", "reason": msg})
            await send_log(log)
            return booking_payment_pb2.UpdateBookingPaymentStatusResponse(
                success=False,
                message=msg,
            )

        try:
            async with SessionLocal() as session:
                stmt = select(Booking).where(Booking.id == request.booking_id)
                result = await session.execute(stmt)
                booking = result.scalar_one_or_none()

                if not booking:
                    msg = "Booking not found"
                    log.update({"result": "failure", "reason": msg})
                    await send_log(log)
                    return booking_payment_pb2.UpdateBookingPaymentStatusResponse(
                        success=False,
                        message=msg,
                    )

                booking.status = request.new_status
                await session.commit()

                log.update({"result": "success"})
                await send_log(log)
                return booking_payment_pb2.UpdateBookingPaymentStatusResponse(
                    success=True,
                    message="Booking status updated",
                )

        except Exception as e:
            tb_str = traceback.format_exc()
            log.update({"result": "failure", "error": str(e), "traceback": tb_str})
            await send_log(log)
            return booking_payment_pb2.UpdateBookingPaymentStatusResponse(
                success=False,
                message="Internal server error",
            )


async def serve():
    server = grpc.aio.server()
    booking_payment_pb2_grpc.add_BookingPaymentServiceServicer_to_server(
        BookingPaymentServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{settings.GRPC_PORT_FOR_BOOKING_SERVICE}")
    await send_log(
        {
            "service": SERVICE,
            "event": "start_server",
            "message": f"gRPC Booking Payment Service running on port {settings.GRPC_PORT_FOR_BOOKING_SERVICE}",
        }
    )
    await server.start()
    await server.wait_for_termination()
