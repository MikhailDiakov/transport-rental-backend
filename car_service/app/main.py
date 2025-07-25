import os
from contextlib import asynccontextmanager

from app.api.v1 import availability, cars
from app.utils.kafka_producer import close_producer, get_kafka_producer, send_log
from fastapi import FastAPI
from starlette_exporter import PrometheusMiddleware, handle_metrics

USE_KAFKA = os.getenv("USE_KAFKA", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if USE_KAFKA:
        await get_kafka_producer()
        await send_log(
            {
                "service": "car_service",
                "event": "startup",
                "message": "Car service started",
            }
        )
    else:
        print("Kafka disabled: skipping kafka initialization")

    yield

    if USE_KAFKA:
        await send_log(
            {
                "service": "car_service",
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
