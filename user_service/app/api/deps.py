from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_limiter.depends import RateLimiter

from app.core.security import decode_access_token
from app.db.session import async_session
from app.models.role import RoleEnum

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/login", scheme_name="JWT Authorization"
)


def limiter_dep(times: int = 5, seconds: int = 60):
    return Depends(RateLimiter(times=times, seconds=seconds))


async def get_session():
    async with async_session() as session:
        yield session


async def get_current_user_info(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("id")
    role = payload.get("role")
    if user_id is None or role is None:
        raise credentials_exception

    return {"id": int(user_id), "role": int(role)}


def require_role(required_role: RoleEnum) -> Callable:
    async def checker(current=Depends(get_current_user_info)):
        if current["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only {required_role.name.lower()} can access this resource",
            )
        return current

    return checker


require_superadmin = require_role(RoleEnum.SUPERADMIN)
require_admin = require_role(RoleEnum.ADMIN)
