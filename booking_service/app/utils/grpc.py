import grpc
from app.core.config import settings
from app.grpc import car_booking_pb2, car_booking_pb2_grpc, user_pb2, user_pb2_grpc


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


async def restore_availability_via_grpc(
    car_id: int, start: str, end: str, price_per_day: float
):
    async with grpc.aio.insecure_channel(settings.CAR_GRPC_HOST) as channel:
        stub = car_booking_pb2_grpc.BookingServiceStub(channel)
        request = car_booking_pb2.RestoreAvailabilityRequest(
            car_id=car_id,
            start_date=start,
            end_date=end,
            price_per_day=price_per_day,
        )
        return await stub.RestoreAvailability(request)


async def validate_user_exists(user_id: int) -> bool:
    async with grpc.aio.insecure_channel(settings.USER_GRPC_HOST) as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        request = user_pb2.GetUserByIdRequest(user_id=user_id)
        response = await stub.GetUserById(request)
        return response.is_valid


async def get_user_info(user_id: int) -> user_pb2.UserResponse | None:
    async with grpc.aio.insecure_channel(settings.USER_GRPC_HOST) as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        request = user_pb2.GetUserByIdRequest(user_id=user_id)
        response = await stub.GetUserById(request)
        if response.is_valid:
            return response
        return None
