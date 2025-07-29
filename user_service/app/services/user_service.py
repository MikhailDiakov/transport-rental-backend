import secrets
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.hash import get_password_hash, verify_password
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.models.role import RoleEnum
from app.models.user import User
from app.utils.kafka_producer import send_log, send_notification_email
from app.utils.redis_client import (
    delete_refresh_token,
    delete_token,
    get_email_by_token,
    get_refresh_token,
    is_reset_request_allowed,
    set_token,
    store_refresh_token,
)
from app.utils.selectors.user import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)

SERVICE = settings.PROJECT_NAME


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


async def login_user(form_data, db: AsyncSession) -> JSONResponse:
    username = form_data.username
    password = form_data.password
    log = {
        "service": "user_service",
        "event": "login_user",
        "username": username,
    }

    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        log.update({"result": "failure", "reason": "Invalid credentials"})
        await send_log(log)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"id": str(user.id), "role": str(user.role_id)})
    refresh_token = create_refresh_token({"id": str(user.id)})

    await store_refresh_token(user.id, refresh_token)

    log.update({"result": "success", "user_id": user.id})
    await send_log(log)

    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,  # True in prod
        max_age=7 * 86400,
    )
    return response


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


async def refresh_user_token(request: Request) -> dict:
    log = {
        "service": "user_service",
        "event": "refresh_user_token",
    }

    token = request.cookies.get("refresh_token")
    if not token:
        log.update({"result": "failure", "reason": "Missing refresh token"})
        await send_log(log)
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = decode_refresh_token(token)
    if not payload:
        log.update({"result": "failure", "reason": "Invalid refresh token"})
        await send_log(log)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = int(payload["id"])
    stored_token = await get_refresh_token(user_id)
    if stored_token != token:
        log.update(
            {"result": "failure", "reason": "Token mismatch", "user_id": user_id}
        )
        await send_log(log)
        raise HTTPException(status_code=401, detail="Token mismatch")

    access_token = create_access_token(
        {"id": str(user_id), "role": str(payload.get("role", "1"))}
    )

    log.update({"result": "success", "user_id": user_id})
    await send_log(log)

    return {"access_token": access_token, "token_type": "bearer"}


async def logout_user(user_id: int) -> JSONResponse:
    log = {
        "service": "user_service",
        "event": "logout_user",
        "user_id": user_id,
    }

    await delete_refresh_token(user_id)

    log.update({"result": "success"})
    await send_log(log)

    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("refresh_token")
    return response


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


async def request_password_reset(email: str, db: AsyncSession) -> None:
    log = {
        "service": SERVICE,
        "event": "request_password_reset",
        "email": email,
    }

    user = await get_user_by_email(db, email)
    allowed = await is_reset_request_allowed(email)
    if not allowed:
        log.update({"result": "failure", "reason": "Too many requests"})
        await send_log(log)
        raise HTTPException(
            status_code=429,
            detail="You can request password reset only once per minute.",
        )

    if user:
        code = secrets.token_urlsafe(24)
        await set_token(email=email, token=code, ttl_seconds=900)

        subject = "Your Password Reset Code"
        body = f"Hello {user.username},\n\nYour password reset code is:\n{code}\n\nIt expires in 15 minutes."
        await send_notification_email(to_email=email, subject=subject, body=body)

        log.update({"result": "success", "user_id": user.id})
    else:
        log.update({"result": "ignored", "reason": "Email not registered"})

    await send_log(log)


async def reset_password(token: str, new_password: str, db: AsyncSession) -> None:
    log = {
        "service": SERVICE,
        "event": "reset_password",
        "token": token,
    }

    email = await get_email_by_token(token)
    if not email:
        log.update({"result": "failure", "reason": "Invalid or expired token"})
        await send_log(log)
        raise ValueError("Invalid or expired reset code")

    user = await get_user_by_email(db, email)
    if not user:
        log.update({"result": "failure", "reason": "User not found"})
        await send_log(log)
        raise ValueError("User not found")

    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    await delete_token(token)

    log.update({"result": "success", "user_id": user.id})
    await send_log(log)
