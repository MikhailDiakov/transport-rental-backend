import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from app.api.v1 import users
from app.api.v1.superadmin import users_by_admin as superadmin_users
from app.core.config import settings
from app.utils.kafka_producer import close_producer, get_kafka_producer, send_log
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from starlette_exporter import PrometheusMiddleware, handle_metrics

IS_DEV_MODE = os.getenv("IS_DEV_MODE", "false").lower() == "true"

SERVICE = settings.PROJECT_NAME


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_connection = redis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)

    if not IS_DEV_MODE:
        await get_kafka_producer()
        await send_log(
            {
                "service": SERVICE,
                "event": "startup",
                "message": "User service started",
            }
        )
    else:
        print("[DEV_MODE] Kafka is disabled")

    yield

    if not IS_DEV_MODE:
        await send_log(
            {
                "service": SERVICE,
                "event": "shutdown",
                "message": "User service stopped",
            }
        )
        await close_producer()


app = FastAPI(lifespan=lifespan)

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(
    superadmin_users.router, prefix="/admin/users", tags=["superadmin-users"]
)
