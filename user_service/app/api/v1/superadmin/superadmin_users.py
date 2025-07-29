from typing import List, Optional

from app.api.deps import get_current_user_info, get_session, require_superadmin
from app.schemas.user import AdminUserUpdate, UserRead
from app.services.superadmin.user_service_by_admin import (
    delete_user_by_id,
    get_user_read_by_id,
    get_users_from_db,
    update_user_by_admin,
)
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserRead],
    dependencies=[Depends(require_superadmin)],
)
async def list_users(
    role_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: AsyncSession = Depends(get_session),
):
    return await get_users_from_db(db, role_id=role_id, skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_superadmin)],
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_session)):
    return await get_user_read_by_id(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_superadmin)],
)
async def edit_user(
    user_id: int,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    user = await update_user_by_admin(db, user_id, data, current_user)
    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_superadmin)],
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    await delete_user_by_id(db, user_id, current_user)
    return None
