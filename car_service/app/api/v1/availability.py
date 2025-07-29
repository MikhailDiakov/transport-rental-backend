from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_info, get_session, require_admin
from app.schemas.availability import (
    CarAvailabilityCreate,
    CarAvailabilityRead,
    CarAvailabilityUpdate,
)
from app.services.availability_service import (
    create_availability,
    delete_availability,
    get_availability,
    list_availabilities,
    update_availability,
)

router = APIRouter()


@router.post(
    "/", response_model=CarAvailabilityRead, status_code=status.HTTP_201_CREATED
)
async def create_availability_endpoint(
    availability_in: CarAvailabilityCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_admin),
):
    availability_data = availability_in.model_dump()
    return await create_availability(db, availability_data, admin_id=current_user["id"])


@router.get("/", response_model=List[CarAvailabilityRead])
async def read_availabilities(
    skip: int = 0,
    limit: int = 100,
    car_id: Optional[int] = None,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await list_availabilities(
        db, skip, limit, car_id=car_id, user_id=current_user["id"]
    )


@router.get("/{availability_id}", response_model=CarAvailabilityRead)
async def read_availability(
    availability_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_availability(db, availability_id, user_id=current_user["id"])


@router.put("/{availability_id}", response_model=CarAvailabilityRead)
async def update_availability_endpoint(
    availability_id: int,
    availability_in: CarAvailabilityUpdate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_admin),
):
    availability_data = availability_in.model_dump(exclude_unset=True)
    return await update_availability(
        db, availability_id, availability_data, admin_id=current_user["id"]
    )


@router.delete("/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability_endpoint(
    availability_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_admin),
):
    await delete_availability(db, availability_id, admin_id=current_user["id"])
