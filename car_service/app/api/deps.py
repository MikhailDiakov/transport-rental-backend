from typing import Callable, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.db.session import async_session
from app.models.role import RoleEnum

security = HTTPBearer()


async def get_session():
    async with async_session() as session:
        yield session


async def get_current_user_info(
    token: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token.credentials)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("id")
    role = payload.get("role")
    if user_id is None or role is None:
        raise credentials_exception

    return {"id": int(user_id), "role": int(role)}


def require_role(*allowed_roles: Union[RoleEnum, int]) -> Callable:
    async def checker(current=Depends(get_current_user_info)):
        if current["role"] not in [
            r.value if isinstance(r, RoleEnum) else r for r in allowed_roles
        ]:
            allowed_names = ", ".join(
                r.name.lower() if isinstance(r, RoleEnum) else str(r)
                for r in allowed_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only {allowed_names} can access this resource",
            )
        return current

    return checker


require_superadmin = require_role(RoleEnum.SUPERADMIN)
require_admin = require_role(RoleEnum.ADMIN, RoleEnum.SUPERADMIN)
