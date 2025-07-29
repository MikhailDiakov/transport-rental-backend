import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette_exporter import PrometheusMiddleware, handle_metrics

from app.api.v1 import availability, cars
from app.core.config import settings
from app.utils.kafka_producer import close_producer, get_kafka_producer, send_log

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

app.include_router(cars.router, prefix="/cars", tags=["cars"])
app.include_router(
    availability.router, prefix="/cars-availability", tags=["cars-availability"]
)
