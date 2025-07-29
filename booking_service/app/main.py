import os
from contextlib import asynccontextmanager

from app.api.v1 import booking
from app.api.v1.admin import admin_booking
from app.core.config import settings
from app.utils.kafka_producer import close_producer, get_kafka_producer, send_log
from fastapi import FastAPI
from starlette_exporter import PrometheusMiddleware, handle_metrics

IS_DEV_MODE = os.getenv("IS_DEV_MODE", "false").lower() == "true"

SERVICE = settings.PROJECT_NAME


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not IS_DEV_MODE:
        await get_kafka_producer()
        await send_log(
            {
                "service": SERVICE,
                "event": "startup",
                "message": "Car service started",
            }
        )
    else:
        print("[DEV_MODE] Kafka disabled for car_service")

    yield

    if not IS_DEV_MODE:
        await send_log(
            {
                "service": SERVICE,
                "event": "shutdown",
                "message": "Car service stopped",
            }
        )
        await close_producer()


app = FastAPI(lifespan=lifespan)
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

app.include_router(booking.router, prefix="/booking", tags=["booking"])
app.include_router(
    admin_booking.router, prefix="/admin/booking", tags=["admin_booking"]
)
