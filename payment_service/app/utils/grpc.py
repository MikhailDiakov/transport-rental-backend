import grpc
from app.core.config import settings
from app.grpc import (
    booking_payment_pb2,
    booking_payment_pb2_grpc,
    user_pb2,
    user_pb2_grpc,
)


async def get_booking_info(booking_id: int):
    async with grpc.aio.insecure_channel(settings.BOOKING_GRPC_HOST) as channel:
        stub = booking_payment_pb2_grpc.BookingPaymentServiceStub(channel)
        request = booking_payment_pb2.GetBookingForPaymentRequest(booking_id=booking_id)
        response = await stub.GetBookingForPayment(request)
        return response


async def update_booking_status(booking_id: int, new_status: str):
    async with grpc.aio.insecure_channel(settings.BOOKING_GRPC_HOST) as channel:
        stub = booking_payment_pb2_grpc.BookingPaymentServiceStub(channel)
        request = booking_payment_pb2.UpdateBookingPaymentStatusRequest(
            booking_id=booking_id,
            new_status=new_status,
        )
        response = await stub.UpdateBookingPaymentStatus(request)
        return response


async def get_user_info(user_id: int) -> user_pb2.UserResponse | None:
    async with grpc.aio.insecure_channel(settings.USER_GRPC_HOST) as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        request = user_pb2.GetUserByIdRequest(user_id=user_id)
        response = await stub.GetUserById(request)
        if response.is_valid:
            return response
        return None
