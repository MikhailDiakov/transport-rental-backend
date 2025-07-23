from typing import Optional

from app.core.hash import get_password_hash, verify_password
from app.models.role import RoleEnum
from app.models.user import User
from app.utils.kafka_producer import send_log
from app.utils.selectors.user import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

SERVICE = "user_service"


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    role_id: int = RoleEnum.CLIENT,
) -> User:
    log = {
        "service": SERVICE,
        "event": "create_user",
        "username": username,
        "email": email,
    }

    if await get_user_by_username(db, username):
        log.update({"result": "failure", "reason": "Username already registered"})
        await send_log(log)
        raise HTTPException(status_code=400, detail="Username already registered")

    if await get_user_by_email(db, email):
        log.update({"result": "failure", "reason": "Email already registered"})
        await send_log(log)
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

    log.update({"result": "success", "user_id": user.id})
    await send_log(log)
    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    log = {
        "service": SERVICE,
        "event": "authenticate_user",
        "username": username,
    }

    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        log.update({"result": "failure", "reason": "Invalid credentials"})
        await send_log(log)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    log.update({"result": "success", "user_id": user.id})
    await send_log(log)
    return user


async def get_user_profile(db: AsyncSession, user_id: int) -> User:
    log = {
        "service": SERVICE,
        "event": "get_user_profile",
        "user_id": user_id,
    }

    user = await get_user_by_id(db, user_id)
    if not user:
        log.update({"result": "failure", "reason": "User not found"})
        await send_log(log)
        raise HTTPException(status_code=404, detail="User not found")

    log.update({"result": "success"})
    await send_log(log)
    return user


async def update_user_profile(
    db: AsyncSession,
    user_id: int,
    email: Optional[str] = None,
    old_password: Optional[str] = None,
    new_password: Optional[str] = None,
    confirm_password: Optional[str] = None,
) -> User:
    log = {
        "service": SERVICE,
        "event": "update_user_profile",
        "user_id": user_id,
    }

    user = await get_user_by_id(db, user_id)
    if not user:
        log.update({"result": "failure", "reason": "User not found"})
        await send_log(log)
        raise HTTPException(status_code=404, detail="User not found")

    if email:
        existing = await get_user_by_email(db, email)
        if existing and existing.id != user_id:
            log.update({"result": "failure", "reason": "Email already in use"})
            await send_log(log)
            raise HTTPException(status_code=400, detail="Email already in use")
        if not old_password or not verify_password(old_password, user.hashed_password):
            log.update(
                {"result": "failure", "reason": "Old password required to change email"}
            )
            await send_log(log)
            raise HTTPException(
                status_code=400, detail="Old password required to change email"
            )
        user.email = email

    if new_password:
        if not old_password or not verify_password(old_password, user.hashed_password):
            log.update({"result": "failure", "reason": "Old password is incorrect"})
            await send_log(log)
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        if new_password != confirm_password:
            log.update({"result": "failure", "reason": "New passwords do not match"})
            await send_log(log)
            raise HTTPException(status_code=400, detail="New passwords do not match")
        user.hashed_password = get_password_hash(new_password)

    await db.commit()
    await db.refresh(user)

    log.update({"result": "success"})
    await send_log(log)
    return user
