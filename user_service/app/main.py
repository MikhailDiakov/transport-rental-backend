from contextlib import asynccontextmanager

import redis.asyncio as redis
from app.api.v1 import users
from app.api.v1.superadmin import users_by_admin as superadmin_users
from app.core.config import settings
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from starlette_exporter import PrometheusMiddleware, handle_metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_connection = redis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(
    superadmin_users.router, prefix="/superadmin/users", tags=["superadmin-users"]
)
