import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

RESET_PREFIX = "reset:"
RESET_LIMIT_PREFIX = "reset_limit:"


async def set_token(email: str, token: str, ttl_seconds: int = 900):
    old_token = await redis_client.get(f"{RESET_PREFIX}email:{email}")
    if old_token:
        await redis_client.delete(f"{RESET_PREFIX}{old_token}")

    await redis_client.set(f"{RESET_PREFIX}{token}", email, ex=ttl_seconds)
    await redis_client.set(f"{RESET_PREFIX}email:{email}", token, ex=ttl_seconds)


async def get_email_by_token(token: str) -> str | None:
    return await redis_client.get(f"{RESET_PREFIX}{token}")


async def delete_token(token: str):
    email = await redis_client.get(f"{RESET_PREFIX}{token}")
    if email:
        await redis_client.delete(f"{RESET_PREFIX}email:{email}")
    await redis_client.delete(f"{RESET_PREFIX}{token}")


async def is_reset_request_allowed(email: str) -> bool:
    key = f"{RESET_LIMIT_PREFIX}{email}"
    exists = await redis_client.exists(key)
    if exists:
        return False
    await redis_client.set(key, "1", ex=60)
    return True


async def store_refresh_token(user_id: int, token: str, ttl_seconds: int = 7 * 86400):
    await redis_client.set(f"refresh:{user_id}", token, ex=ttl_seconds)


async def get_refresh_token(user_id: int) -> str | None:
    return await redis_client.get(f"refresh:{user_id}")


async def delete_refresh_token(user_id: int):
    await redis_client.delete(f"refresh:{user_id}")
