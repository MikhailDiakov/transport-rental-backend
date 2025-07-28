from app.api.deps import get_current_user_info, get_session
from app.schemas.booking import BookingCreate, BookingListRead, BookingRead
from app.services.booking_service import (
    create_booking,
    delete_user_booking,
    get_user_bookings,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/", response_model=BookingRead)
async def book_car(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_session),
    user=Depends(get_current_user_info),
):
    booking, message = await create_booking(
        db,
        car_id=booking_in.car_id,
        start_date=booking_in.start_date,
        end_date=booking_in.end_date,
        user_id=user["id"],
    )
    if not booking:
        raise HTTPException(status_code=400, detail=message)
    return booking


@router.get("/", response_model=BookingListRead)
async def list_user_bookings(
    only_future: bool = False,
    db: AsyncSession = Depends(get_session),
    user=Depends(get_current_user_info),
):
    bookings = await get_user_bookings(db, user["id"], only_future)
    return {"bookings": bookings}


@router.delete("/{booking_id}", status_code=204)
async def delete_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_session),
    user=Depends(get_current_user_info),
):
    success = await delete_user_booking(db, booking_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Booking not found or forbidden")
