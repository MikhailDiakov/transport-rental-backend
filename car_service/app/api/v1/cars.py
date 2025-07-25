from app.api.deps import get_current_user_info, get_session, require_admin
from app.schemas.car import CarCreate, CarRead, CarUpdate
from app.services.car_service import (
    create_car,
    delete_car,
    get_car,
    list_cars,
    update_car,
)
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/", response_model=CarRead, status_code=status.HTTP_201_CREATED)
async def create_car_endpoint(
    car_in: CarCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_admin),
):
    car_data = car_in.model_dump()
    return await create_car(db, car_data, admin_id=current_user["id"])


@router.get("/{car_id}", response_model=CarRead)
async def read_car(
    car_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await get_car(db, car_id, user_id=current_user["id"])


@router.get("/", response_model=list[CarRead])
async def read_cars(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user_info),
):
    return await list_cars(db, skip, limit, user_id=current_user["id"])


@router.put("/{car_id}", response_model=CarRead)
async def update_car_endpoint(
    car_id: int,
    car_in: CarUpdate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_admin),
):
    car_data = car_in.model_dump(exclude_unset=True)
    return await update_car(db, car_id, car_data, admin_id=current_user["id"])


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car_endpoint(
    car_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_admin),
):
    await delete_car(db, car_id, admin_id=current_user["id"])
