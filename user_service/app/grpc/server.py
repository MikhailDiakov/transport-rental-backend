from sqlalchemy.ext.asyncio import async_sessionmaker

import grpc
from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import engine
from app.grpc import user_pb2, user_pb2_grpc
from app.utils.kafka_producer import send_log
from app.utils.selectors.user import get_user_by_id

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
SERVICE = f"{settings.PROJECT_NAME}_grpc"


class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
    async def GetUserByToken(self, request, context):
        token = request.token
        log = {
            "service": SERVICE,
            "event": "GetUserByToken",
            "token": token[:10] + "...",
        }

        payload = decode_access_token(token)
        if not payload:
            log.update({"result": "failure", "reason": "Invalid or expired token"})
            await send_log(log)
            return user_pb2.UserResponse(
                is_valid=False,
                error_message="Invalid or expired token",
            )

        user_id = int(payload.get("id", 0))
        async with SessionLocal() as session:
            user = await get_user_by_id(session, user_id)
            if not user:
                log.update(
                    {
                        "result": "failure",
                        "reason": "User not found",
                        "user_id": user_id,
                    }
                )
                await send_log(log)
                return user_pb2.UserResponse(
                    is_valid=False,
                    error_message="User not found",
                )

            log.update({"result": "success", "user_id": user.id})
            await send_log(log)

            return user_pb2.UserResponse(
                is_valid=True,
                error_message="",
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role_id,
            )

    async def GetUserById(self, request, context):
        user_id = request.user_id
        log = {
            "service": SERVICE,
            "event": "GetUserById",
            "user_id": user_id,
        }

        async with SessionLocal() as session:
            user = await get_user_by_id(session, user_id)
            if not user:
                log.update({"result": "failure", "reason": "User not found"})
                await send_log(log)
                return user_pb2.UserResponse(
                    is_valid=False,
                    error_message="User not found",
                )

            log.update({"result": "success"})
            await send_log(log)
            return user_pb2.UserResponse(
                is_valid=True,
                error_message="",
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role_id,
            )


async def serve():
    server = grpc.aio.server()
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    server.add_insecure_port(f"[::]:{settings.GRPC_PORT}")
    log = {
        "service": SERVICE,
        "event": "start_server",
        "message": f"gRPC User Service running on port {settings.GRPC_PORT}",
    }
    await send_log(log)
    await server.start()
    await server.wait_for_termination()
