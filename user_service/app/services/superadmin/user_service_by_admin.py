from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleEnum
from app.core.config import settings
from app.core.hash import get_password_hash
from app.models.user import User
from app.schemas.user import AdminUserUpdate, UserRead
from app.utils.kafka_producer import send_log
from app.utils.selectors.user import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)

SERVICE = settings.PROJECT_NAME


async def get_users_from_db(
    db: AsyncSession,
    role_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[UserRead]:
    query = select(User)
    if role_id is not None:
        query = query.where(User.role_id == role_id)

    query = query.offset(skip).limit(limit)

    users = (await db.execute(query)).scalars().all()

    await send_log(
        {
            "service": SERVICE,
            "event": "get_users",
            "result": "success",
            "count": len(users),
            "filtered_by_role": role_id,
            "skip": skip,
            "limit": limit,
        }
    )
    return [UserRead.model_validate(u) for u in users]


async def get_user_read_by_id(db: AsyncSession, user_id: int) -> UserRead:
    log = {"service": SERVICE, "event": "get_user_by_id", "user_id": user_id}
    user = await get_user_by_id(db, user_id)
    if not user:
        log.update({"result": "failure", "reason": "User not found"})
        await send_log(log)
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"User with id={user_id} not found"
        )
    log.update({"result": "success"})
    await send_log(log)
    return UserRead.model_validate(user)


async def update_user_by_admin(
    db: AsyncSession, user_id: int, data: AdminUserUpdate, current_user: dict
):
    log = {
        "service": SERVICE,
        "event": "update_user_by_admin",
        "user_id": user_id,
        "admin_id": current_user["id"],
    }

    if user_id == current_user["id"]:
        log.update({"result": "failure", "reason": "Cannot edit own account"})
        await send_log(log)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot edit your own account",
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        log.update({"result": "failure", "reason": "User not found"})
        await send_log(log)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role_id == RoleEnum.SUPERADMIN.value:
        log.update({"result": "failure", "reason": "Cannot edit other superadmins"})
        await send_log(log)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit other superadmins",
        )

    if data.email and data.email != user.email:
        existing = await get_user_by_email(db, data.email)
        if existing and existing.id != user.id:
            log.update({"result": "failure", "reason": "Email already in use"})
            await send_log(log)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )
        user.email = data.email

    if data.username and data.username != user.username:
        existing = await get_user_by_username(db, data.username)
        if existing and existing.id != user.id:
            log.update({"result": "failure", "reason": "Username already in use"})
            await send_log(log)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use",
            )
        user.username = data.username

    if data.password:
        user.hashed_password = get_password_hash(data.password)

    if data.role is not None:
        if data.role == RoleEnum.SUPERADMIN.value:
            log.update({"result": "failure", "reason": "Cannot assign superadmin role"})
            await send_log(log)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign superadmin role",
            )
        user.role_id = data.role

    db.add(user)
    await db.commit()
    await db.refresh(user)

    log.update({"result": "success"})
    await send_log(log)

    return user


async def delete_user_by_id(db: AsyncSession, user_id: int, current_user: dict):
    log = {
        "service": SERVICE,
        "event": "delete_user_by_admin",
        "user_id": user_id,
        "admin_id": current_user["id"],
    }

    if user_id == current_user["id"]:
        log.update({"result": "failure", "reason": "Cannot delete own account"})
        await send_log(log)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        log.update({"result": "failure", "reason": "User not found"})
        await send_log(log)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role_id == RoleEnum.SUPERADMIN.value:
        log.update({"result": "failure", "reason": "Cannot delete other superadmins"})
        await send_log(log)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete other superadmins",
        )

    await db.delete(user)
    await db.commit()

    log.update({"result": "success"})
    await send_log(log)
