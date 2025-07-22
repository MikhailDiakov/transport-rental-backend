from typing import List

from app.api.deps import RoleEnum
from app.core.hash import get_password_hash
from app.models.user import User
from app.schemas.user import AdminUserUpdate, UserRead
from app.utils.selectors.user import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_all_users_from_db(db: AsyncSession) -> List[UserRead]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]


async def get_admins_from_db(db: AsyncSession) -> List[UserRead]:
    result = await db.execute(
        select(User).where(
            User.role_id.in_(
                [
                    RoleEnum.ADMIN.value,
                    RoleEnum.SUPERADMIN.value,
                ]
            )
        )
    )
    admins = result.scalars().all()
    return [UserRead.model_validate(u) for u in admins]


async def get_user_read_by_id(db: AsyncSession, user_id: int) -> UserRead:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found",
        )
    return UserRead.model_validate(user)


async def update_user_by_admin(
    db: AsyncSession, user_id: int, data: AdminUserUpdate, current_user: User
):
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot edit your own account",
        )
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.role_id == RoleEnum.SUPERADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit other superadmins",
        )

    if data.email and data.email != user.email:
        existing = await get_user_by_email(db, data.email)
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )
        user.email = data.email

    if data.username and data.username != user.username:
        existing = await get_user_by_username(db, data.username)
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use",
            )
        user.username = data.username

    if data.password:
        user.password = get_password_hash(data.password)

    if data.role is not None:
        if data.role == RoleEnum.SUPERADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign superadmin role",
            )
        user.role_id = data.role

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user_by_id(db: AsyncSession, user_id: int, current_user: User):
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.role_id == RoleEnum.SUPERADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete other superadmins",
        )

    await db.delete(user)
    await db.commit()
