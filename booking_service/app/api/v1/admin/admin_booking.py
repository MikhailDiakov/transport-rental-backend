from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_admin
from app.schemas.booking import (
    AdminBookingCreate,
    BookingListRead,
    BookingRead,
    BookingUpdate,
)
from app.services.admin.admin_booking_service import (
    admin_create_booking,
    admin_delete_booking,
    admin_get_booking,
    admin_list_bookings,
    admin_update_booking,
)

router = APIRouter()


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking_endpoint(
    booking_in: AdminBookingCreate,
    db: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    booking, message = await admin_create_booking(
        db,
        car_id=booking_in.car_id,
        start_date=booking_in.start_date,
        end_date=booking_in.end_date,
        user_id=booking_in.user_id,
        admin_id=admin["id"],
    )
    if not booking:
        raise HTTPException(status_code=400, detail=message)
    return booking


@router.get("/", response_model=BookingListRead)
async def list_bookings_endpoint(
    only_future: Optional[bool] = False,
    user_id: Optional[int] = None,
    car_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    bookings = await admin_list_bookings(
        db,
        only_future=only_future,
        admin_id=admin["id"],
        user_id=user_id,
        car_id=car_id,
        limit=limit,
        offset=offset,
    )
    return {"bookings": bookings}


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking_endpoint(
    booking_id: int,
    db: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    booking = await admin_get_booking(db, booking_id, admin_id=admin["id"])
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.put("/{booking_id}", response_model=BookingRead)
async def update_booking_endpoint(
    booking_id: int,
    booking_in: BookingUpdate,
    db: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    booking = await admin_update_booking(
        db, booking_id, booking_in.model_dump(exclude_unset=True), admin_id=admin["id"]
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking_endpoint(
    booking_id: int,
    db: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    success = await admin_delete_booking(db, booking_id, admin_id=admin["id"])
    if not success:
        raise HTTPException(
            status_code=404, detail="Booking not found or failed to delete"
        )
