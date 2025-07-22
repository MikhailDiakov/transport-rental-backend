from typing import Optional

from app.core.hash import get_password_hash, verify_password
from app.models.role import RoleEnum
from app.models.user import User
from app.utils.selectors.user import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    role_id: int = RoleEnum.CLIENT,
) -> User:
    if await get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already registered")

    if await get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role_id=role_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_user_profile(db: AsyncSession, user_id: int) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def update_user_profile(
    db: AsyncSession,
    user_id: int,
    email: Optional[str] = None,
    old_password: Optional[str] = None,
    new_password: Optional[str] = None,
    confirm_password: Optional[str] = None,
) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if email:
        existing = await get_user_by_email(db, email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")
        if not old_password or not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Old password required to change email"
            )
        user.email = email

    if new_password:
        if not old_password or not verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")

        user.hashed_password = get_password_hash(new_password)

    await db.commit()
    await db.refresh(user)
    return user
